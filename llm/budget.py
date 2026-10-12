"""Atomic reservations before provider requests, including failed requests.

Public deployments require durable Redis REST counters. Local development can
use SQLite, which is not a durable limit on an ephemeral cloud disk.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from urllib.error import URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from settings import setting, positive_int


class UsageLimitError(RuntimeError):
    pass


class CallBudget:
    def __init__(self, session_id):
        self.session_id = session_id
        self.session_limit = positive_int("MAX_SESSION_CALLS", 30)
        self.daily_limit = positive_int("MAX_DAILY_CALLS", 100)
        self.redis_url = str(setting("QUOTA_REDIS_URL", "")).rstrip("/")
        self.redis_token = setting("QUOTA_REDIS_TOKEN", "")
        self.local = setting("APP_ENV", "public") == "local"

    @property
    def ready(self):
        parsed = urlparse(self.redis_url)
        return self.local or bool(parsed.scheme == "https" and parsed.netloc and self.redis_token)

    def reserve(self):
        if not self.ready:
            raise UsageLimitError("Live AI is paused until its usage limit is configured.")
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self.redis_url and self.redis_token:
            self._reserve_redis(day)
        else:
            self._reserve_sqlite(day)

    def _reserve_redis(self, day):
        script = """
        local daily = tonumber(redis.call('GET', KEYS[1]) or '0')
        local session = tonumber(redis.call('GET', KEYS[2]) or '0')
        if daily >= tonumber(ARGV[1]) or session >= tonumber(ARGV[2]) then return 0 end
        redis.call('INCR', KEYS[1]); redis.call('EXPIRE', KEYS[1], 172800)
        redis.call('INCR', KEYS[2]); redis.call('EXPIRE', KEYS[2], 172800)
        return 1
        """
        payload = ["EVAL", script, "2", f"studybuddy:daily:{day}",
                   f"studybuddy:session:{day}:{self.session_id}",
                   str(self.daily_limit), str(self.session_limit)]
        request = Request(self.redis_url, data=json.dumps(payload).encode(),
                          headers={"Authorization": f"Bearer {self.redis_token}",
                                   "Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=8) as response:
                result = json.load(response)
            if result.get("error") or "result" not in result:
                raise ValueError("Invalid quota response")
            approved = result["result"] == 1
        except (URLError, ValueError, KeyError, TypeError):
            raise UsageLimitError("Live AI is temporarily unavailable. Please try the sample preview.") from None
        if not approved:
            raise UsageLimitError("The demo's AI allowance has been reached. Please try the sample preview.")

    def _reserve_sqlite(self, day):
        path = Path(setting("QUOTA_SQLITE_PATH", ".runtime/usage.sqlite3"))
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path, timeout=10) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS usage (key TEXT PRIMARY KEY, count INTEGER NOT NULL)")
            connection.execute("BEGIN IMMEDIATE")
            keys = [(f"daily:{day}", self.daily_limit),
                    (f"session:{day}:{self.session_id}", self.session_limit)]
            for key, limit in keys:
                row = connection.execute("SELECT count FROM usage WHERE key = ?", (key,)).fetchone()
                if row and row[0] >= limit:
                    raise UsageLimitError("The demo's AI allowance has been reached. Please try the sample preview.")
            for key, _ in keys:
                connection.execute("INSERT INTO usage VALUES (?, 1) ON CONFLICT(key) DO UPDATE SET count = count + 1", (key,))
