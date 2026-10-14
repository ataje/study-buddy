# Study Buddy

**A multi-agent tutor that turns lecture PDFs into explanations, follow-up answers and practice quizzes.**

Built by **Aya Taje**

**Public preview:** [aya-study-buddy.streamlit.app](https://aya-study-buddy.streamlit.app/)

## Release status

The notebook interface puts lecture uploads, Study, Practice and Ask in one focused workspace. A separate **sample preview** needs no account, uploads or API credits. Its lesson, questions and follow-up answers are explicitly labeled as **prewritten examples**. The sample quiz is interactive and graded deterministically.

**Public live AI remains disabled.** It requires an OpenAI-compatible provider, a supported model, a server-side API key, and a durable public usage counter. No live provider credentials are included in this repository. Real PDF retrieval, lesson generation, quiz generation and multiple-choice grading have been tested locally with Groq. This local verification does not enable or verify public live AI.

## Notebook interface update — October 14, 2026

- Warm paper colors, sage accents, consistent icons and compact navigation replace the oversized landing layout.
- Lecture upload is the primary starting point; Study, Practice and Ask share the same session's notes.
- Lessons, quiz feedback and answers sit beside an evidence panel with source passages and page references.
- The sample uses the same notebook style while retaining its explicit prewritten-example label.

The notebook release passed local checks and was approved for publication. Cloud verification of this interface is pending.

## Try it

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the address printed by Streamlit and choose **Explore a sample lesson**. VS Code is optional. Python 3.12 is the tested dependency target.

For live setup and publication, see [DEPLOYMENT.md](DEPLOYMENT.md).

## The workflow

```text
Lecture PDF
  → text extraction with page metadata
  → overlapping chunks and sentence-transformer embeddings
  → session-isolated ChromaDB collection
  → relevant passages
  → explanation + response review, or quiz + grading
  → visible source passages and page references
```

| Component | Responsibility |
| --- | --- |
| Routing agent | Selects a task; missing-document requests are handled without a model call. |
| Query enhancer | Rewrites a request for retrieval; falls back to a deterministic query if rewriting fails. |
| Retrieval agent | Searches page-aware chunks in an ephemeral collection unique to each session. |
| Explaining agent | Produces a lesson or follow-up answer from retrieved evidence. |
| Quiz agent | Generates a validated quiz; grades multiple choice deterministically and short answers using the provider. |
| Response review agent | Compares an explanation with its evidence; failed or rejected reviews are visibly flagged. |

The agents have focused inputs and outputs. Homepage routing, PDF validation and multiple-choice grading are deterministic; language generation and free-form routing use an LLM. A review model is a second check, not proof of factual correctness.

## Reliability and public-demo controls

- Each visitor gets a separate ChromaDB collection. Uploading or switching a document does not overwrite another visitor's vectors.
- A replacement document is indexed successfully before it becomes active. Empty, scanned, encrypted and overlarge PDFs receive a useful error.
- Each file is limited to **5 MB, 40 pages and 25,000 extracted words**; a session holds at most **three documents**.
- Provider work runs on explicit submission. Cached UI state prevents free-form requests from running again on ordinary Streamlit reruns; failed lessons require an explicit retry.
- Model output is capped at **1,200 tokens per call** by default. Prompts are limited to **24,000 characters**. SDK retries are disabled, and requests have a timeout.
- Default quotas are **100 provider calls per UTC day across all visitors** and **30 per session per day**. Every attempted request reserves a call before reaching the provider. A user action can require several calls.
- Public live mode requires a **durable Redis REST counter** with an atomic reservation. If the counter is unavailable or the quota is exhausted, provider calls fail closed. Local development can use SQLite.
- API keys belong in environment variables or Streamlit deployment secrets. Real secrets files and runtime state are ignored by Git. Provider errors are redacted before display.
- Quiz structure, question types, answer membership and short-answer scores are validated. Untrusted text is escaped when inserted into HTML; generated answers use Streamlit's normal Markdown renderer.

Call and token limits bound request volume, not a dollar amount. Configure provider-side spending controls too. New sessions can reset the session allowance, but cannot reset the durable shared daily counter.

## Storage and privacy

This demo intentionally provides **session-only storage**, without accounts or a permanent document library. Uploaded text stays in the session, and its vectors stay in memory. Vectors are removed on replacement or explicit session clearing. Collections idle for two hours are eligible for cleanup during subsequent indexing; they are also lost on a server restart. Only the public embedding model is shared across sessions.

When live AI is enabled, retrieved excerpts, questions and some document previews are sent to the configured AI provider. Do not upload confidential material. The app does not persist uploads on the host's filesystem. Streamlit Community Cloud does not guarantee durable local storage, so a disk-based Chroma database would not provide reliable long-term persistence there. A future authenticated product could add durable external storage and user-level permissions; that is outside this demo's scope.

## Validation

```bash
python -m unittest discover -s tests -v
python -m pip check
```

The notebook release passed **24 automated checks locally** using Python 3.12, real ChromaDB storage with deterministic test embeddings, and Streamlit AppTest. They cover session isolation, page metadata, document replacement, PDF limits, concurrent daily quotas, quota-store failure, configuration, provider-error redaction, quiz validation, grading, no-document routing, failed review handling, sample interaction, navigation and rerun behavior.

Provider calls and Redis HTTP responses are mocked in the automated checks. **They do not establish live model accuracy or provider connectivity.** Separate local live checks used a text-based PDF, actual embeddings and Groq to exercise retrieval, lesson generation, a three-question quiz, multiple-choice grading and source passages. No accuracy percentage has been measured. Public live provider and durable-quota checks remain pending.

The earlier public sample was checked in Chrome and a separate browser session: lesson, missing-evidence response, 3/3 quiz grading, source pages and notes download. The notebook update still requires a cloud browser check after deployment.

## Project files

```text
app.py                  Streamlit notebook interface and orchestration
notebook_ui.py          Shared notebook theme, icons and headings
sample_preview.py       Clearly labeled prewritten fallback
samples/lecture.md      Original public sample notes
settings.py             Server-side settings
agents/                 Routing, enhancement, explanation, quiz and review
rag/retrieval_agent.py   ChromaDB retrieval and session isolation
llm/service.py          Bounded OpenAI-compatible requests
llm/budget.py           Durable public quotas / local SQLite quotas
document_ingest.py      PDF limits and page metadata
tests/                  Regression and Streamlit UI checks
.streamlit/             Theme and secret configuration example
```

## Limitations

Text-based PDFs work best; OCR is not included. Retrieved passages may omit relevant parts of a lecture. Model-written citations require verification. Short-answer grading is advisory and may be inconsistent. Multiple-choice grading checks the generated answer key, whose factual correctness also depends on the model. This release does not claim measured time savings, comprehensive lecture coverage or a quantified accuracy improvement.

## References

- [Streamlit deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app)
- [Streamlit secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Streamlit storage considerations](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data)
- [Chroma Python clients](https://docs.trychroma.com/reference/python)


