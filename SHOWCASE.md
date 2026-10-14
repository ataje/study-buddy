# Study Buddy — Aya Taje

**A multi-agent RAG tutor for lecture PDFs**

Study Buddy turns static lecture material into guided explanations, follow-up answers and practice quizzes. I built the application in Python with Streamlit, sentence-transformer embeddings and ChromaDB for my CS494 Agentic AI course at the University of Illinois Chicago.

Six focused agents separate routing, query enhancement, retrieval, explanation, quiz generation and response review. The notebook interface offers Study, Practice and Ask, with source passages alongside each result. Session-isolated document collections, bounded uploads, validated quiz responses and usage controls support a more dependable workflow.

The project reflects the kind of operational automation I want to build: turn a document-based task into a repeatable workflow, keep the source evidence available, and handle failure explicitly. Multiple-choice grading is deterministic; short-answer feedback and generated explanations remain model judgments that users should verify.

**Try the preview:** read the sample lesson, answer the three-question quiz, then check each claim against the source. The sample is explicitly labeled as prewritten. Public live AI remains disabled until its provider and durable usage counter are configured and tested.

**Validation:** 24 automated regression and UI checks passed locally. Separate local checks used actual embeddings and Groq to test PDF retrieval, lesson generation, a three-question quiz, multiple-choice grading and source passages. These checks establish working paths, not a measured accuracy score. The earlier public sample was browser-tested; cloud verification of the notebook update and public live AI is pending.

**Public website:** https://aya-study-buddy.streamlit.app/  
**Public source:** https://github.com/ataje/study-buddy

**October 14 update:** warm notebook styling, compact navigation, a clearer upload flow and evidence beside results. The local version was approved for publication.

The public link demonstrates the sample experience; public live AI is not connected. No accuracy percentage or hours-saved claim has been measured.
