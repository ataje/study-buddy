# Publish Study Buddy on Streamlit Community Cloud

## Safe preview release

The preview can be deployed without an AI provider or quota-store account. It contains no secret key and cannot make paid model calls. The UI clearly distinguishes the prewritten sample from live AI.

1. The prepared source is published at [ataje/study-buddy](https://github.com/ataje/study-buddy). For a new deployment, put this prepared folder's **contents** in a personal GitHub repository. Preserve `agents/`, `rag/`, `llm/`, `samples/`, `tests/` and `.streamlit/`. Keep the original classroom repository separate.
2. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/). Connect the GitHub account that owns the personal repository.
3. Create an app with the repository, branch `main`, and entrypoint `app.py`.
4. In Advanced settings, choose **Python 3.12**. The Python version is chosen in the deployment UI; do not rely on a `runtime.txt` file.
5. Leave live AI disabled. No secrets are needed for the sample preview. Optionally set `SOURCE_REPOSITORY_URL` to the verified public repository URL in the app's Secrets settings.
6. Deploy. Check the build logs, then confirm the public URL loads from a signed-out browser.
7. Test the sample lesson, all three quiz answers, the unsupported sample question, source view, download and mobile layout. Save the real URL only after these checks pass.

If files were uploaded inside a wrapper directory, move them to the repository root before deployment. Streamlit custom configuration should be at `.streamlit/config.toml` in the repository root.

The Linux deployment prefers CPU-only PyTorch wheels through the additional official PyTorch package index. Dependency installation and all 20 tests passed in GitHub Actions on Linux. Resource use and the Streamlit host build still require deployment verification.

## Enable live AI

A new provider account is needed because the previous Hugging Face account is unavailable. This application supports an OpenAI-compatible endpoint; its availability, model access and JSON response-format support must be verified with the chosen provider.

Set these values through Streamlit's **Secrets** settings, never through a public code file:

```toml
APP_ENV = "public"
LIVE_AI_ENABLED = true
LLM_MODEL = "a-supported-provider-model"
LLM_BASE_URL = "https://your-provider.example/v1"
LLM_API_KEY = "your-private-provider-key"
QUOTA_REDIS_URL = "https://your-durable-redis-rest-endpoint"
QUOTA_REDIS_TOKEN = "your-private-redis-rest-token"
MAX_DAILY_CALLS = 100
MAX_SESSION_CALLS = 30
MAX_OUTPUT_TOKENS = 1200
MAX_PROMPT_CHARS = 24000
```

Use a durable Redis service with a Redis-compatible REST API supporting `EVAL`, such as Upstash. The app's Lua script checks and increments the daily and session counters atomically. The REST token and endpoint must refer to the same database. Limit access to the app's dedicated quota database.

Configure provider-side spending controls and start with a small allowance. A provider call limit is not a monetary spending cap. Do not point Community Cloud at `localhost`: that address is the cloud host, not your Mac.

With public mode and a missing quota endpoint/token, live AI stays disabled even if a provider key is present. With a configured but unavailable quota store, it refuses paid requests. No automatic retry consumes additional calls after a failed provider response.

## Required live checks before sharing as a live AI application

- Confirm MiniLM downloads and the embedding model loads on the cloud host.
- Upload a short, public, text-based PDF. Test a lesson, a supported follow-up, an unsupported question, a quiz, multiple-choice grading and short-answer feedback.
- Compare each answer and page reference with the original PDF. Record any incorrect result; do not infer accuracy from a successful response.
- Open two different browser sessions with different PDFs. Verify that one visitor's upload and document switch do not affect the other visitor's answers or source passages.
- Confirm a new quiz clears old answers. Switch documents and verify that old lesson and quiz results disappear.
- Test blank/scanned PDFs, an encrypted PDF and an overlarge upload.
- Set a small quota temporarily and verify that both session and shared daily limits stop provider calls; restore the intended limits afterward.
- Test provider and quota-store failures. Verify that the UI gives a useful message without showing credentials or provider diagnostics.
- Leave the app running through a restart and verify that uploads are lost as documented while the external daily quota remains intact.

## Local live development

Use environment variables or an ignored `.streamlit/secrets.toml`. For local testing only, set `APP_ENV="local"`; SQLite counters will be written under the ignored `.runtime/` folder. Keep `LIVE_AI_ENABLED=true` explicit. A local Ollama endpoint can be configured if Ollama and a compatible model are already installed, but it is not a Community Cloud hosting solution.

## Current verification boundary

The prepared code passed 20 automated checks and dependency consistency checks locally and in GitHub Actions on Linux. The sample was exercised with Streamlit AppTest. This environment blocked binding a local preview port and downloading the MiniLM model. The preview is now deployed at https://aya-study-buddy.streamlit.app/ and checked in Chrome plus a separate browser session. The lesson, unsupported sample question, 3/3 quiz grading, source pages and notes download worked; homepage geometry at a 390px viewport had no horizontal overflow. Real-model retrieval remains unverified. No live provider key or Redis account was supplied. Live provider and quota-store checks are still required before enabling public AI generation.
