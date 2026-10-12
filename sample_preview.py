"""A labeled, prewritten fallback; never presented as a live AI result."""
from pathlib import Path
import streamlit as st

SAMPLE_LECTURE = Path(__file__).parent / "samples" / "lecture.md"
LESSON = """### What RAG changes
A language model can make unsupported claims. RAG adds relevant source passages to its context before it writes an answer. This helps ground an answer, but it does not guarantee correctness. **[p. 1]**

### How the document is searched
The document is split into chunks. Embeddings represent the chunks as numerical vectors, which are stored with their text and page metadata. The user's question is also embedded so the system can find similar passages. **[p. 2]**

### Why the source stays visible
Page references make it easier to check an answer. If the source does not contain the answer, the assistant should say so. A review agent can flag unsupported content, but its review is still a model judgment. **[p. 3]**
"""
QUIZ = [
    {"question": "What does RAG supply to the model at answer time?",
     "options": ["Relevant source passages", "A guarantee that every answer is correct", "A replacement for the user's question"],
     "answer": "Relevant source passages", "why": "The passages become context for the answer. [p. 1]"},
    {"question": "Why store page metadata with each chunk?",
     "options": ["To help readers verify answers against the source", "To prevent every retrieval error", "To avoid storing source text"],
     "answer": "To help readers verify answers against the source", "why": "Page metadata connects a retrieved passage to the original document. [p. 2]"},
    {"question": "What should the tutor do when the evidence does not contain the answer?",
     "options": ["Acknowledge the missing evidence", "Invent a plausible answer", "Treat the review model as proof"],
     "answer": "Acknowledge the missing evidence", "why": "The answer should acknowledge what the supplied context cannot support. [p. 3]"},
]


def render_sample():
    if st.button("← Back to home", key="sample_back"):
        st.session_state.page = "home"
        st.rerun()
    st.title("A lecture, made interactive")
    st.info("Sample preview: the lesson, questions and feedback below are prewritten examples. No live AI requests are made.")
    st.caption("Original sample material · Introduction to retrieval-augmented generation · 3 pages")
    lesson_tab, practice_tab, source_tab = st.tabs(["Study the lesson", "Try a quiz", "Check the source"])
    with lesson_tab:
        st.markdown(LESSON)
        st.subheader("A follow-up, with evidence")
        question = st.selectbox("Choose a sample question", ["Does RAG guarantee a correct answer?", "What is an embedding?", "Which embedding model is best?"])
        answers = {
            "Does RAG guarantee a correct answer?": "No. Source quality, retrieval quality and generation quality still matter. [p. 1]",
            "What is an embedding?": "An embedding is a numerical vector representing aspects of a passage's meaning. It enables similarity search. [p. 2]",
            "Which embedding model is best?": "The sample lecture does not compare embedding models, so it does not support an answer to that question.",
        }
        st.write(answers[question])
    with practice_tab:
        st.caption("This sample uses deterministic multiple-choice grading. The live app also supports AI-assisted short-answer grading.")
        with st.form("sample_quiz"):
            choices = [st.radio(q["question"], q["options"], index=None, key=f"sample_q_{i}") for i, q in enumerate(QUIZ)]
            submitted = st.form_submit_button("Check my answers", use_container_width=True)
        if submitted:
            score = sum(choice == q["answer"] for choice, q in zip(choices, QUIZ))
            st.success(f"Your score: {score} / {len(QUIZ)}")
            for i, (choice, q) in enumerate(zip(choices, QUIZ), 1):
                label = "Correct" if choice == q["answer"] else "Not answered" if choice is None else "Needs review"
                st.write(f"**{i}. {label}** — {q['why']}")
    with source_tab:
        st.markdown(SAMPLE_LECTURE.read_text())
        st.download_button("Download sample notes", SAMPLE_LECTURE.read_text(), file_name="study-buddy-sample.md", mime="text/markdown")
    with st.expander("How the live app handles a request"):
        st.markdown("**PDF → page-aware chunks → embeddings → ChromaDB retrieval → explanation or quiz → review or grading.**")
        st.write("The router chooses a task; the query enhancer improves the search query; retrieval returns evidence; the explaining and quiz agents produce structured outputs; the review agent checks draft explanations against that evidence.")
        st.caption("The preview above illustrates the experience. Live generation requires a connected AI provider and configured usage limits.")
