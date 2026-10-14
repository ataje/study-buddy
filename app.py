import streamlit as st
from html import escape
from hashlib import sha256
import re

from document_ingest import extract_pdf, MAX_SESSION_DOCUMENTS
from sample_preview import render_sample
from settings import setting
from notebook_ui import apply_theme, icon, page_heading
from llm import LLMService
from agents.routing_agent import RoutingAgent
from rag.retrieval_agent import RetrievalAgent
from agents.explaining_agent import ExplainingAgent
from agents.quiz_agent import QuizAgent
from agents.query_enhancer_agent import QueryEnhancerAgent
from agents.response_review_agent import ResponseReviewAgent

st.set_page_config(
    page_title="Study Buddy",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def split_sections(text):
    # Keep a heading with its content instead of displaying it as a whole lesson step.
    def is_heading(block):
        return "\n" not in block and bool(re.match(r"^(?:#{1,6}\s|\*\*.+\*\*$|\d+[.)]\s)", block))
    groups, current = [], []
    for block in (part.strip() for part in text.split("\n\n")):
        if not block:
            continue
        if is_heading(block) and current and not all(is_heading(part) for part in current):
            groups.append("\n\n".join(current))
            current = []
        current.append(block)
    if current:
        groups.append("\n\n".join(current))
    return groups

def badge(label):
    st.markdown(
        f'<div class="agent-badge"><span class="live-dot"></span>{html_text(label)}</div>',
        unsafe_allow_html=True,
    )

def progress_bar(current, total):
    pct = int((current / total) * 100) if total else 0
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'font-size:12px;color:#9B9890;margin-bottom:8px;">'
        f'<span>Section {current} of {total}</span><span>{pct}%</span></div>'
        f'<div class="progress-bar-wrap">'
        f'<div class="progress-bar-fill" style="width:{pct}%"></div></div>',
        unsafe_allow_html=True,
    )

def html_text(value):
    return escape(str(value)).replace("\n", "<br>")


def show_error(exc):
    if isinstance(exc, (ValueError, RuntimeError)):
        st.error(str(exc))
    else:
        st.error("This step could not be completed. Please try again or use the sample preview.")


def activate_document(doc_name):
    document = st.session_state.document_library.get(doc_name)
    if not document:
        raise ValueError("This document is no longer available. Please upload it again.")
    st.session_state.retrieval_agent.index_document(
        document["text"], pages=document["pages"], document_name=doc_name)
    st.session_state.document_text = document["text"]
    st.session_state.document_ready = True
    st.session_state.active_document_name = doc_name
    st.session_state.router_result = None
    st.session_state.other_payload = None


def save_uploaded_document(uploaded_file):
    library = st.session_state.document_library
    if uploaded_file.name not in library and len(library) >= MAX_SESSION_DOCUMENTS:
        raise ValueError("This demo keeps up to three documents per session. Clear the session to add more.")
    text, pages = extract_pdf(uploaded_file)
    digest = sha256(uploaded_file.getvalue()).hexdigest()
    existing = library.get(uploaded_file.name)
    if existing and existing.get("digest") == digest:
        activate_document(uploaded_file.name)
        return st.session_state.retrieval_agent.chunk_text(text)
    chunks = st.session_state.retrieval_agent.index_document(text, pages=pages, document_name=uploaded_file.name)
    library[uploaded_file.name] = {"text": text, "pages": pages, "section_count": len(chunks), "digest": digest}
    st.session_state.document_text = text
    st.session_state.document_ready = True
    st.session_state.active_document_name = uploaded_file.name
    st.session_state.router_result = None
    st.session_state.other_payload = None
    return chunks


def clear_quiz_inputs():
    st.session_state.quiz_responses = {}
    for key in list(st.session_state):
        if key.startswith(("quiz_question_", "quiz_short_answer_", "quiz_answer_")):
            del st.session_state[key]


def reset_learning_views():
    st.session_state.lesson_attempted = False
    clear_quiz_inputs()
    for key in ("followup_input", "quiz_prompt_input"):
        st.session_state.pop(key, None)
    st.session_state.explanation = ""
    st.session_state.retrieved_chunks = []
    st.session_state.lesson_sections = []
    st.session_state.current_section_index = 0
    st.session_state.last_answer = ""
    st.session_state.last_enhanced_query = None
    st.session_state.last_review_notes = ""
    st.session_state.review_approved = None
    st.session_state.lesson_sources = []
    st.session_state.answer_sources = []
    st.session_state.quiz_sources = []
    st.session_state.quiz_data = None
    st.session_state.quiz_query = ""
    st.session_state.revealed_answers = {}
    st.session_state.quiz_feedback = {}


def enhance_query(user_query, intent="general"):
    preview = st.session_state.document_text[:1200] if st.session_state.document_text else ""
    enhancement = st.session_state.query_enhancer_agent.enhance_query(
        user_query=user_query,
        document_preview=preview,
        intent=intent,
    )
    st.session_state.last_enhanced_query = enhancement
    return enhancement


def review_explanation(user_query, draft_response, retrieved_chunks):
    review = st.session_state.response_review_agent.review_explanation(
        user_query=user_query,
        draft_response=draft_response,
        retrieved_chunks=retrieved_chunks,
    )
    st.session_state.last_review_notes = review.get("notes", "")
    st.session_state.review_approved = review.get("approved") is True
    st.session_state.answer_sources = list(st.session_state.retrieval_agent.last_sources)
    return review.get("final_response", draft_response)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
defaults = {
    "lesson_sources": [],
    "answer_sources": [],
    "quiz_sources": [],
    "lesson_attempted": False,
    "other_payload": None,
    "mode": None,
    "route": None,
    "page": "home",
    "document_ready": False,
    "document_text": "",
    "retrieved_chunks": [],
    "explanation": "",
    "lesson_sections": [],
    "current_section_index": 0,
    "last_answer": "",
    "last_enhanced_query": None,
    "last_review_notes": "",
    "review_approved": None,
    "other_query": "",
    "router_result": None,
    "quiz_data": None,
    "quiz_query": "",
    "revealed_answers": {},
    "document_library": {},
    "active_document_name": None,
    "quiz_feedback": {},
    "quiz_responses": {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "llm_service" not in st.session_state:
    st.session_state.llm_service = LLMService()
elif type(st.session_state.llm_service).__name__ == "LLMService" and type(st.session_state.llm_service) is not LLMService:
    # Keep quota identity when local code reloads replace a Python class.
    previous_service = st.session_state.llm_service
    replacement = LLMService(budget=previous_service.budget)
    replacement.client = previous_service.client
    st.session_state.llm_service = replacement
if "retrieval_agent" not in st.session_state:
    st.session_state.retrieval_agent = RetrievalAgent()
st.session_state.routing_agent = RoutingAgent(llm_service=st.session_state.llm_service)
st.session_state.explaining_agent = ExplainingAgent(llm_service=st.session_state.llm_service)
st.session_state.quiz_agent = QuizAgent(llm_service=st.session_state.llm_service)
st.session_state.query_enhancer_agent = QueryEnhancerAgent(llm_service=st.session_state.llm_service)
st.session_state.response_review_agent = ResponseReviewAgent(llm_service=st.session_state.llm_service)

live_ready = st.session_state.llm_service.is_configured()

def render_ask():
    page_heading("What would you like to understand?", "Ask about your lecture. Check the evidence alongside each answer.")
    other_query = st.text_input("Your request", placeholder="Summarize this lecture, find a concept, or quiz me", max_chars=2000)
    submit_other = st.button("Submit Request →", key="submit_other")
    if submit_other and other_query.strip():
        st.session_state.other_query = other_query
        st.session_state.other_payload = None
        result = st.session_state.routing_agent.llm_router_decision(
            other_query, bool(st.session_state.document_text),
            doc_context={"summary_preview": st.session_state.document_text[:1000], "candidate_headings": []},
            app_state={"current_section": st.session_state.current_section_index, "mode": "general"})
        st.session_state.router_result = result
        selected = result.get("selected_agent", "clarification_agent")
        try:
            if selected == "clarification_agent":
                st.session_state.other_payload = {"message": result.get("clarification_question") or "Please add more detail."}
            elif selected == "navigation_agent":
                if st.session_state.lesson_sections:
                    step = -1 if "previous" in other_query.lower() or "back" in other_query.lower() else 1
                    st.session_state.current_section_index = max(0, min(len(st.session_state.lesson_sections) - 1, st.session_state.current_section_index + step))
                    st.session_state.page = "explaining"
                    st.rerun()
                else:
                    st.session_state.other_payload = {"message": "Start a lesson in Study mode before navigating its sections."}
            else:
                if not st.session_state.document_ready:
                    raise ValueError("Please prepare a lecture in Study or Practice first.")
                intent = "quiz" if selected == "quiz_agent" else "retrieve" if selected == "retrieval_agent" else "explain"
                with st.spinner("Finding evidence in your lecture…"):
                    enhancement = enhance_query(other_query, intent)
                    if enhancement.get("needs_clarification"):
                        raise ValueError(enhancement.get("clarification_question") or "Please add more detail.")
                    chunks = st.session_state.retrieval_agent.retrieve(enhancement["retrieval_query"], top_k=5)
                    st.session_state.retrieved_chunks = chunks
                    if selected == "quiz_agent":
                        quiz = st.session_state.quiz_agent.generate_quiz(chunks)
                        clear_quiz_inputs()
                        st.session_state.quiz_data = quiz
                        st.session_state.quiz_sources = list(st.session_state.retrieval_agent.last_sources)
                        st.session_state.quiz_query = other_query
                        st.session_state.revealed_answers = {}
                        st.session_state.quiz_feedback = {}
                        st.session_state.page = "quiz"
                        st.rerun()
                    elif selected == "retrieval_agent" and not any(word in other_query.lower() for word in ("summar", "overview")):
                        st.session_state.other_payload = {"passages": chunks, "sources": list(st.session_state.retrieval_agent.last_sources)}
                    else:
                        draft = st.session_state.explaining_agent.answer_followup(enhancement["enhanced_query"], chunks)
                        answer = review_explanation(enhancement["enhanced_query"], draft, chunks)
                        st.session_state.other_payload = {"answer": answer, "sources": list(st.session_state.retrieval_agent.last_sources)}
        except Exception as exc:
            show_error(exc)
    payload = st.session_state.other_payload
    if payload:
        if payload.get("message"):
            st.info(payload["message"])
        if payload.get("answer"):
            st.markdown(payload["answer"])
        for passage in payload.get("passages", []):
            st.write(passage)
    if st.session_state.router_result:
        with st.expander("View the workflow"):
            st.write("Selected task:", st.session_state.router_result.get("selected_agent"))
            if st.session_state.last_enhanced_query:
                st.write("Search query:", st.session_state.last_enhanced_query.get("retrieval_query"))

def render_lesson():
    page_heading("Let’s make this lecture click.", "Work through your notes at your own pace, with evidence close by.")
    if not st.session_state.explanation and not st.session_state.lesson_attempted:
        st.session_state.lesson_attempted = True
        try:
            with st.spinner("Retrieving content and preparing your lesson…"):
                chunks = st.session_state.retrieval_agent.retrieve(
                    "main topic of the lecture", top_k=5
                )
                st.session_state.retrieved_chunks = chunks
                draft_explanation = st.session_state.explaining_agent.generate_full_lesson(chunks)
                explanation = review_explanation(
                    "Teach the main topic of the lecture.",
                    draft_explanation,
                    chunks,
                )
                st.session_state.explanation = explanation
                st.session_state.lesson_sources = list(st.session_state.retrieval_agent.last_sources)
                st.session_state.lesson_sections = split_sections(explanation)
                st.session_state.current_section_index = 0
        except Exception as exc:
            show_error(exc)

    if not st.session_state.lesson_sections:
        if st.button("Try preparing the lesson again", key="retry_lesson", disabled=not live_ready):
            st.session_state.lesson_attempted = False
            st.rerun()

    if st.session_state.lesson_sections:
        idx = st.session_state.current_section_index
        total = len(st.session_state.lesson_sections)

        lesson_container = st.container(border=True, key="lesson_paper")
        with lesson_container:
            badge("Your lesson")
            progress_bar(idx + 1, total)

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            st.markdown(st.session_state.lesson_sections[idx])
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

            nav_l, nav_r = st.columns(2, gap="small")
            with nav_l:
                if st.button("← Previous", disabled=(idx == 0), use_container_width=True, key="prev"):
                    st.session_state.current_section_index -= 1
                    st.rerun()

            with nav_r:
                if idx < total - 1:
                    if st.button("Next →", use_container_width=True, key="next"):
                        st.session_state.current_section_index += 1
                        st.rerun()
                else:
                    st.button("✓ Lesson Complete", use_container_width=True, disabled=True, key="done")

    ask_container = st.container(border=True, key="ask_paper")
    with ask_container:
        badge("A little more clarity")

        st.markdown(
            "<h3 style='font-size:20px;margin:0 0 4px;'>Have a question?</h3>"
            "<p style='font-size:13px;color:#7A7870;margin:0 0 16px;'>"
            "Ask about the material. Study Buddy will look for supporting evidence.</p>",
            unsafe_allow_html=True,
        )

        followup = st.text_input(
            "Ask",
            placeholder="e.g. Can you explain this more simply?",
            key="followup_input",
            max_chars=2000,
            label_visibility="collapsed",
        )

        ask = st.button("Ask →", use_container_width=True, key="ask_btn")

    if ask and followup.strip():
        try:
            with st.spinner("Thinking…"):
                enhancement = enhance_query(followup, intent="explain")
                if enhancement.get("retrieval_query"):
                    followup_chunks = st.session_state.retrieval_agent.retrieve(
                        enhancement["retrieval_query"],
                        top_k=5,
                    )
                else:
                    followup_chunks = st.session_state.retrieved_chunks
                st.session_state.retrieved_chunks = followup_chunks
                draft_answer = st.session_state.explaining_agent.answer_followup(
                    enhancement["enhanced_query"],
                    followup_chunks
                )
                answer = review_explanation(
                    enhancement["enhanced_query"],
                    draft_answer,
                    followup_chunks,
                )
            st.session_state.last_answer = answer
        except Exception as exc:
            show_error(exc)

    if st.session_state.last_answer:
        st.markdown(st.session_state.last_answer)


def render_quiz():
    page_heading("A little practice, a clearer picture.", "Use your notes, explain in your own words, and check the evidence.")
    badge("Practice gently")
    st.markdown(
        """
        <div class="quiz-toolbar">
            <p class="quiz-intro">Choose a focus area or generate a mixed quiz from the full lecture.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    quiz_prompt = st.text_input(
        "Quiz topic",
        value=st.session_state.quiz_query or "Create a practice quiz from this lecture.",
        placeholder="e.g. Focus on the main concepts and definitions",
        label_visibility="collapsed",
        key="quiz_prompt_input",
        max_chars=2000,
    )

    generate_quiz = st.button("Generate Quiz →", use_container_width=True, key="generate_quiz_btn", type="primary")

    if generate_quiz and quiz_prompt.strip():
        st.session_state.quiz_query = quiz_prompt
        try:
            with st.spinner("Retrieving content and writing your quiz…"):
                enhancement = enhance_query(quiz_prompt, intent="quiz")
                quiz_chunks = st.session_state.retrieval_agent.retrieve(
                    enhancement["retrieval_query"],
                    top_k=5,
                )
                st.session_state.retrieved_chunks = quiz_chunks
                quiz = st.session_state.quiz_agent.generate_quiz(quiz_chunks)
                clear_quiz_inputs()
                st.session_state.quiz_data = quiz
                st.session_state.quiz_sources = list(st.session_state.retrieval_agent.last_sources)
                st.session_state.revealed_answers = {}
                st.session_state.quiz_feedback = {}
        except Exception as exc:
            show_error(exc)

    quiz_data = st.session_state.quiz_data
    if quiz_data:
        st.caption("Check your understanding, then compare the answers with your notes.")
        st.markdown(f"### {quiz_data.get('title', 'Practice Quiz')}")
        total_questions = len(quiz_data.get("questions", []))
        graded_feedback = [
            value for value in st.session_state.quiz_feedback.values()
            if isinstance(value, dict) and "score" in value
        ]
        if graded_feedback:
            score_total = sum(item.get("score", 0.0) for item in graded_feedback)
            st.caption(f"Current score: {score_total:.1f} / {total_questions}")

        for idx, question in enumerate(quiz_data.get("questions", []), start=1):
            question_key = f"quiz_question_{idx}"
            short_answer_key = f"quiz_short_answer_{idx}"
            feedback_key = f"quiz_feedback_{idx}"

            st.markdown(f"**Question {idx}.** {question.get('question', '')}")
            if question.get("type") == "multiple_choice":
                options = question.get("options", [])
                saved_answer = st.session_state.quiz_responses.get(question_key)
                response = st.radio(
                    "Choose one", options, key=question_key,
                    label_visibility="collapsed",
                    index=options.index(saved_answer) if saved_answer in options else None,
                )
                st.session_state.quiz_responses[question_key] = response
            else:
                response = st.text_area(
                    "Your answer",
                    value=st.session_state.quiz_responses.get(short_answer_key, ""),
                    key=short_answer_key,
                    label_visibility="collapsed",
                    placeholder="Type your answer here",
                    max_chars=2000,
                )
                st.session_state.quiz_responses[short_answer_key] = response

            if st.button("Check answer", key=f"check_answer_{idx}"):
                try:
                    student_answer = (
                        st.session_state.get(question_key)
                        if question.get("type") == "multiple_choice"
                        else st.session_state.get(short_answer_key)
                    )
                    st.session_state.quiz_feedback[feedback_key] = (
                        st.session_state.quiz_agent.check_answer(question, student_answer)
                    )
                    st.rerun()
                except Exception as exc:
                    show_error(exc)

            feedback = st.session_state.quiz_feedback.get(feedback_key)
            if feedback:
                feedback_class = "correct" if feedback.get("is_correct") else "incorrect"
                feedback_title = "Correct" if feedback.get("is_correct") else "Needs review"
                feedback_html = f"""
                <div class="quiz-feedback {feedback_class}">
                    <div class="quiz-feedback-title">{feedback_title}</div>
                    <div class="quiz-answer-text">{html_text(feedback.get("feedback", ""))}</div>
                """
                if not feedback.get("is_correct"):
                    feedback_html += (
                        f'<div class="quiz-answer-label" style="margin-top:12px;">Correct answer</div>'
                        f'<div class="quiz-answer-text">{html_text(feedback.get("correct_answer", ""))}</div>'
                    )
                explanation = feedback.get("explanation")
                if explanation:
                    feedback_html += (
                        f'<div class="quiz-answer-label" style="margin-top:12px;">Why</div>'
                        f'<div class="quiz-answer-text">{html_text(explanation)}</div>'
                    )
                feedback_html += "</div>"
                st.markdown(feedback_html, unsafe_allow_html=True)

            answer_key = f"quiz_answer_{idx}"
            is_revealed = st.session_state.revealed_answers.get(answer_key, False)

            answer_label = "Hide answer" if is_revealed else "Show answer"
            if st.button(answer_label, key=f"toggle_answer_{idx}"):
                st.session_state.revealed_answers[answer_key] = not is_revealed
                st.rerun()

            if st.session_state.revealed_answers.get(answer_key, False):
                explanation = question.get("explanation")
                answer_html = f"""
                <div class="quiz-answer">
                    <div class="quiz-answer-label">Answer</div>
                    <div class="quiz-answer-text">{html_text(question.get("answer", ""))}</div>
                """
                if explanation:
                    answer_html += (
                        f'<div class="quiz-answer-label" style="margin-top:12px;">Why</div>'
                        f'<div class="quiz-answer-text">{html_text(explanation)}</div>'
                    )
                answer_html += "</div>"
                st.markdown(answer_html, unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

def choose_mode(mode):
    st.session_state.mode = mode
    st.session_state.route = st.session_state.routing_agent.route_mode(mode)
    st.session_state.router_result = None
    if st.session_state.document_ready:
        st.session_state.page = {"study": "explaining", "practice": "quiz", "other": "ask"}[mode]
    else:
        st.session_state.page = "upload"
    st.rerun()


def render_guide():
    st.markdown('<div class="notebook-note"><div class="note-title">How it works</div>' + ''.join(
        f'<div class="guide-step"><span class="step-number">{i}</span><div><div class="step-title">{title}</div><div class="step-desc">{desc}</div></div></div>'
        for i,title,desc in [(1,"Upload your notes","Add a text-based lecture PDF to begin."),(2,"Choose how to study","Understand concepts, practice questions, or ask about your lecture."),(3,"Check the source","Use page references and source passages to verify the answer.")]
    ) + '</div>',unsafe_allow_html=True)


def render_upload(home=False):
    left,right=st.columns([1.35,1],gap="large")
    with left:
        with st.container(border=True,key="start_notes" if home else "upload_paper"):
            st.subheader("Start with your notes")
            st.caption("Text-based PDFs · up to 5 MB and 40 pages")
            uploaded=st.file_uploader("Choose a PDF",type="pdf",key="notebook_upload",max_upload_size=5)
            st.caption("Relevant lecture excerpts are sent to the AI provider when you request an AI response. Avoid confidential material.")
            if st.button("Prepare my notes →",key="prep_btn",type="primary",disabled=not uploaded or not live_ready,use_container_width=True):
                try:
                    with st.spinner("Reading and preparing your lecture…"):
                        save_uploaded_document(uploaded)
                        reset_learning_views()
                    mode=st.session_state.mode or "study"
                    st.session_state.route=st.session_state.routing_agent.route_mode(mode)
                    st.session_state.page={"study":"explaining","practice":"quiz","other":"ask"}[mode]
                    st.rerun()
                except Exception as exc:
                    show_error(exc)
            if not live_ready:
                st.info("Live AI is not connected. You can still explore the sample lesson.")
            if st.button("Explore a sample lesson →",key="try_sample"):
                st.session_state.page="sample"
                st.rerun()
            st.caption("Prewritten examples · no upload or API call needed")
    with right:
        with st.container(border=True,key="notebook_guide"):
            render_guide()
    if st.session_state.document_library:
        st.subheader("Your notes in this session")
        options=list(st.session_state.document_library)
        selected=st.selectbox("Choose a document",options,index=options.index(st.session_state.active_document_name),key="session_doc_selector")
        if st.button("Use this document →",key="use_session_doc_btn"):
            try:
                if selected != st.session_state.active_document_name:
                    with st.spinner("Preparing this document…"):
                        activate_document(selected)
                        reset_learning_views()
                st.session_state.page={"study":"explaining","practice":"quiz","other":"ask"}.get(st.session_state.mode,"explaining")
                st.rerun()
            except Exception as exc:
                show_error(exc)


def render_evidence():
    groups=[]
    if st.session_state.page=="explaining":
        if st.session_state.lesson_sections: groups.append(("Lesson evidence",st.session_state.lesson_sources))
        if st.session_state.last_answer: groups.append(("Follow-up evidence",st.session_state.answer_sources))
    elif st.session_state.page=="quiz" and st.session_state.quiz_data:
        groups.append(("Quiz evidence",st.session_state.quiz_sources))
    elif st.session_state.other_payload:
        groups.append(("Answer evidence",st.session_state.other_payload.get("sources",[])))
    with st.container(border=True,key="evidence_rail"):
        st.markdown('<div class="note-title">Evidence from your notes</div>',unsafe_allow_html=True)
        if st.session_state.active_document_name:
            st.caption(st.session_state.active_document_name)
        if not any(sources for _,sources in groups):
            st.write("Source passages will appear here after a lesson, question, or quiz.")
        for label,sources in groups:
            if not sources: continue
            st.markdown(f"**{label}**")
            for i,source in enumerate(sources):
                with st.expander(f"Page {source['page']} · passage {i+1}",expanded=i==0):
                    st.write(source["text"])
        st.caption("These are the passages supplied for the displayed result. Verify important claims against your original lecture.")


with st.container(key="app_header"):
    brand,nav=st.columns([1.3,1],gap="large")
    with brand:
        st.markdown('<div class="brand">'+icon("book")+'<span class="brand-name">Study Buddy</span><span class="brand-credit">By Aya Taje</span></div>',unsafe_allow_html=True)
    with nav:
        for col,(label,mode,page) in zip(st.columns(4,gap="small"),[("Home",None,"home"),("Study","study","explaining"),("Practice","practice","quiz"),("Ask","other","ask")]):
            with col:
                if st.button(label,key="nav_"+label.lower(),type="primary" if st.session_state.page==page else "secondary",disabled=bool(mode) and not live_ready,use_container_width=True):
                    if mode: choose_mode(mode)
                    else:
                        st.session_state.page="home"
                        st.session_state.route=None
                        st.rerun()

if st.session_state.document_library and st.session_state.page!="sample":
    with st.container(key="session_controls"):
        caption_col,switch_col,clear_col=st.columns([4,1,1.1])
        with caption_col: st.caption("Current notes: "+str(st.session_state.active_document_name)+" · this session only")
        with switch_col:
            if st.button("Switch notes",key="switch_notes"):
                st.session_state.page="upload"
                st.rerun()
        with clear_col:
            if st.button("Clear session",key="clear_session"):
                st.session_state.retrieval_agent.close()
                service=st.session_state.llm_service
                st.session_state.clear()
                st.session_state.llm_service=service
                st.rerun()

if st.session_state.page=="sample":
    render_sample()
elif st.session_state.page=="home" and st.session_state.route!="other":
    page_heading("Make sense of your lecture notes.","Understand concepts, practice questions, and ask with evidence.")
    render_upload(home=True)
    st.write("")
    modes=[("Study","study","book","Turn your notes into clear explanations.","Start Studying","btn_study"),("Practice","practice","quiz","Practice the ideas with questions from your notes.","Start Practicing","btn_practice"),("Ask","other","ask","Ask a question and see the supporting evidence.","Ask Study Buddy","btn_other")]
    for col,(label,mode,ic,desc,action,key) in zip(st.columns(3,gap="medium"),modes):
        with col:
            with st.container(key="mode_"+("ask" if mode=="other" else mode)):
                st.markdown('<div class="mode-card"><div class="mode-top">'+icon(ic)+f'<div class="mode-title">{label}</div></div><div class="mode-desc">{desc}</div></div>',unsafe_allow_html=True)
                if st.button(action,key=key,disabled=not live_ready,use_container_width=True): choose_mode(mode)
elif st.session_state.page=="upload":
    page_heading("Start with your notes.","Choose a lecture PDF, then decide how you want to study.")
    render_upload()
else:
    work_area,source_area=st.columns([3,1.15],gap="large")
    with work_area:
        if st.session_state.page=="explaining": render_lesson()
        elif st.session_state.page=="quiz":
            with st.container(border=True,key="quiz_paper"): render_quiz()
        else:
            with st.container(border=True,key="ask_paper"): render_ask()
        displayed_explanation = st.session_state.page == "explaining" or bool((st.session_state.other_payload or {}).get("answer"))
        if displayed_explanation and st.session_state.review_approved is False:
            st.warning("This explanation is an unapproved draft. Verify it against the source passages.")
    with source_area: render_evidence()

if st.session_state.page in ("home","upload"):
    st.divider()
    with st.expander("About Study Buddy"):
        st.write("Created and developed by Aya Taje for CS494 Agentic AI at the University of Illinois Chicago.")
        st.write("Six focused agents coordinate routing, query enhancement, retrieval, explanations, quizzes and response review. Built with Python, Streamlit, sentence-transformer embeddings and ChromaDB.")
        st.caption("AI answers and short-answer grading can be wrong. Your uploads are available for this session only and are lost on expiry or restart.")
        repository=str(setting("SOURCE_REPOSITORY_URL","https://github.com/ataje/study-buddy"))
        if repository.startswith("https://github.com/"): st.link_button("View the source code",repository)
