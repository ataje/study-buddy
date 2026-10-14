# Study Buddy — Aya Taje

**A multi-agent RAG tutor for lecture PDFs**

Study Buddy turns static lecture material into guided explanations, follow-up answers and practice quizzes. I built the application in Python with Streamlit, sentence-transformer embeddings and ChromaDB for my CS494 Agentic AI course at the University of Illinois Chicago.

Six focused agents separate routing, query enhancement, retrieval, explanation, quiz generation and response review. The notebook interface offers Study, Practice and Ask, with source passages alongside each result. Session-isolated document collections, bounded uploads, validated quiz responses and usage controls support a more dependable workflow.

The project reflects the kind of operational automation I want to build: turn a document-based task into a repeatable workflow, keep the source evidence available, and handle failure explicitly. Multiple-choice grading is deterministic; short-answer feedback and generated explanations remain model judgments that users should verify.

**Try it:** upload a text-based lecture PDF, choose Study, Practice or Ask, and check the source passages beside the result. You can also explore the clearly labeled prewritten sample without making an AI request.

**Validation:** 24 automated regression and UI checks passed locally, and GitHub Actions passed on Linux. Public browser checks verified live PDF indexing, lessons, a three-question quiz, multiple-choice and AI short-answer feedback, and source-based questions with page references. Two sessions with different PDFs passed the checked isolation scenario. Blank and protected PDFs were rejected, and the session allowance blocked further generation at its limit. A rejected lesson draft was visibly flagged for review.

**Public website:** https://aya-study-buddy.streamlit.app/  
**Public source:** https://github.com/ataje/study-buddy

**October 14 update:** warm notebook styling, compact navigation, a clearer upload flow and evidence beside results. Live Groq generation uses a durable Upstash quota: 100 provider calls per UTC day across visitors and 20 per session per day.

Credentials stay in encrypted deployment settings. Generated explanations and grading can be wrong; source review is part of the experience. Mobile browser validation remains pending. No accuracy percentage or hours-saved claim has been measured.
