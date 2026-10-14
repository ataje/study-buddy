# Publish Study Buddy on Streamlit Community Cloud

## Safe preview release

The preview can be deployed without an AI provider or quota-store account. It contains no secret key and cannot make provider calls. The UI clearly distinguishes the prewritten sample from live AI.

The existing app is [aya-study-buddy.streamlit.app](https://aya-study-buddy.streamlit.app/), connected to [ataje/study-buddy](https://github.com/ataje/study-buddy), branch `main`, entrypoint `app.py`. The October 14 notebook source is published, with a successful GitHub Actions run. Groq and the free Upstash `study-buddy-usage` database are configured in Streamlit's encrypted secrets settings. The public notebook interface and live PDF paths were browser-tested.

The steps below describe a preview-only deployment. The existing deployment is configured for public live AI with limits of **100 provider calls per UTC day globally** and **20 per session per day**. No credential values belong in this document or the repository.

1. The prepared source is published at [ataje/study-buddy](https://github.com/ataje/study-buddy). For a new deployment, put this prepared folder's **contents** in a personal GitHub repository. Preserve `agents/`, `rag/`, `llm/`, `samples/`, `tests/` and `.streamlit/`. Keep the original classroom repository separate.
2. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/). Connect the GitHub account that owns the personal repository.
3. Create an app with the repository, branch `main`, and entrypoint `app.py`.
4. In Advanced settings, choose **Python 3.12**. The Python version is chosen in the deployment UI; do not rely on a `runtime.txt` file.
5. Leave live AI disabled. No secrets are needed for the sample preview. Optionally set `SOURCE_REPOSITORY_URL` to the verified public repository URL in the app's Secrets settings.
6. Deploy. Check the build logs, then confirm the public URL loads from a signed-out browser.
7. Test notebook navigation, the sample lesson, all three quiz answers, the unsupported sample question, source view, download and mobile layout. Confirm the upload and live actions stay disabled until the required public secrets are configured.

If files were uploaded inside a wrapper directory, move them to the repository root before deployment. Streamlit custom configuration should be at `.streamlit/config.toml` in the repository root.

The Linux deployment prefers CPU-only PyTorch wheels through the additional official PyTorch package index. The notebook release has 24 passing local checks and a successful GitHub Actions run on Linux. Its Streamlit build loaded successfully, including MiniLM on the cold host.

## Enable live AI

Groq has been tested locally and on the public deployment. This application supports an OpenAI-compatible endpoint; verify model access and JSON response-format support again when changing provider or model. Keep the provider and Upstash accounts on their approved free tiers; do not add payment details or upgrade as part of this release.

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
MAX_SESSION_CALLS = 20
MAX_OUTPUT_TOKENS = 1200
MAX_PROMPT_CHARS = 24000
```

Use a durable Redis service with a Redis-compatible REST API supporting `EVAL`, such as Upstash. The app's Lua script checks and increments the daily and session counters atomically. The REST token and endpoint must refer to the same database. Limit access to the app's dedicated quota database.

Use the provider's free-tier limits and start with a small allowance. A provider call limit is not a monetary spending cap. Do not point Community Cloud at `localhost`: that address is the cloud host, not your Mac.

With public mode and a missing quota endpoint/token, live AI stays disabled even if a provider key is present. With a configured but unavailable quota store, it refuses provider requests. No automatic retry consumes additional calls after a failed provider response. Do not copy local `APP_ENV="local"` settings to Community Cloud to bypass this control.

## Checks for future deployment changes

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

Use environment variables or an ignored `.streamlit/secrets.toml`. For local testing only, set `APP_ENV="local"`; SQLite counters will be written under the ignored `.runtime/` folder. Keep `LIVE_AI_ENABLED=true` explicit. Launch with `python -m streamlit run app.py` from the prepared environment. Aya's local package also includes `Run Study Buddy.command`; keep its Terminal window open while using the app. The launcher is for the local Mac, not Community Cloud.

## Current verification boundary

The notebook code passed 24 automated checks locally, and GitHub Actions completed successfully on Linux for published commit `bea7e97`. Automated checks use mocked provider and Redis responses; separate local live checks used actual embeddings and Groq. These checks do not measure answer accuracy.

On October 14, public browser checks verified:

- Notebook rendering, cold-host MiniLM loading and indexing an original public QA PDF.
- A generated lesson, a three-question quiz, correct multiple-choice feedback and AI short-answer feedback. A reviewer-rejected lesson displayed the unapproved-draft warning.
- An Ask answer grounded in the original PDF's Chroma facts with a page-one reference.
- Two separate sessions: the second initially had no notes and answered correctly from a different fictional PDF. The first session's checked absent-fact request displayed only its original notes and did not expose the second document's facts. This does not establish universal refusal of unsupported questions.
- Clear rejection of blank and password-protected PDFs.
- The actual 20-call session allowance blocking further generation. Separate live Redis tests used isolated keys to check global denial, session denial, successful reservation and both counter increments; test state was restored afterward.
- The prewritten sample's 3/3 quiz, source tabs and downloaded notes.

Mobile browser validation remains pending: the attempted viewport override did not change the browser's actual width. Provider and quota-store failures are covered by automated tests; live external outages, cloud restart persistence and stress testing were not exercised. No accuracy score has been measured.
