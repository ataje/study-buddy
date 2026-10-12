# Study Buddy — Aya Taje

**A multi-agent RAG tutor for lecture PDFs**

Study Buddy turns static lecture material into guided explanations, follow-up answers and practice quizzes. I built the application in Python with Streamlit, sentence-transformer embeddings and ChromaDB for my CS494 Agentic AI course at the University of Illinois Chicago. Manav Malik provided TA review support.

Six focused agents separate routing, query enhancement, retrieval, explanation, quiz generation and response review. This makes the workflow easier to inspect and extend. The portfolio preparation adds page metadata and visible source passages, session-isolated document collections, bounded uploads, validated quiz responses and controls on model usage.

The project reflects the kind of operational automation I want to build: turn a document-based task into a repeatable workflow, keep the source evidence available, and handle failure explicitly. Multiple-choice grading is deterministic; short-answer feedback and generated explanations remain model judgments that users should verify.

**Try the preview:** read the sample lesson, answer the three-question quiz, then check each claim against the source. The sample is explicitly labeled as prewritten. Live AI requires a connected provider and configured usage limits.

**Validation:** 20 automated regression and UI checks passed locally and in GitHub Actions on Linux. These test software behavior with mocked provider calls and fixed test embeddings; they do not establish live-model accuracy. The public preview was checked in Chrome and a separate browser session: lesson, missing-evidence response, 3/3 quiz grading, source pages and notes download. Live provider checks remain pending.

**Public website:** https://aya-study-buddy.streamlit.app/  
**Public source:** https://github.com/ataje/study-buddy.

The public link currently demonstrates the sample experience; live AI is not connected. No accuracy percentage or hours-saved claim has been measured.
