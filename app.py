import streamlit as st
from html import escape
from hashlib import sha256

from document_ingest import extract_pdf, MAX_SESSION_DOCUMENTS
from sample_preview import render_sample
from settings import setting
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
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">

<style>
html, body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main,
.main .block-container {
    background-color: #F5F3EE !important;
    color: #1A1916 !important;
}

#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

.block-container {
    padding: 2.5rem 1.5rem 5rem !important;
    max-width: 760px !important;
}

html, body, p, div, span, label,
[class*="css"], .stMarkdown {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
h1, h2, h3 {
    font-family: 'Instrument Serif', serif !important;
    color: #1A1916 !important;
    letter-spacing: -0.01em;
}

.stButton > button {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    border-radius: 100px !important;
    padding: 10px 22px !important;
    border: 1.5px solid #1A1916 !important;
    background: #FFFFFF !important;
    color: #1A1916 !important;
    box-shadow: none !important;
    transition: all .18s ease !important;
}
.stButton > button:hover {
    background: #1A1916 !important;
    color: #FFFFFF !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }
.stButton > button:disabled {
    opacity: .35 !important;
    cursor: not-allowed !important;
    transform: none !important;
}

.btn-teal .stButton > button {
    background: #5DC8B0 !important;
    border-color: #5DC8B0 !important;
    color: #0D5C50 !important;
}
.btn-teal .stButton > button:hover {
    background: #3DB89A !important;
    border-color: #3DB89A !important;
    color: #fff !important;
}
.btn-dark .stButton > button {
    background: #1A1916 !important;
    border-color: #1A1916 !important;
    color: #FFFFFF !important;
}
.btn-dark .stButton > button:hover {
    background: #333 !important;
    border-color: #333 !important;
}
.btn-ghost .stButton > button {
    border-color: #E5E2DA !important;
    color: #9B9890 !important;
    background: transparent !important;
    font-size: 13px !important;
}
.btn-ghost .stButton > button:hover {
    background: #F0EDE8 !important;
    color: #1A1916 !important;
}

[data-testid="stFileUploader"] {
    border: 2px dashed #D5D2CA !important;
    border-radius: 14px !important;
    background: #FAFAF8 !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #5DC8B0 !important;
}

.stTextInput > div > div > input {
    border-radius: 100px !important;
    border: 1.5px solid #E5E2DA !important;
    padding: 10px 18px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 14px !important;
    background: #FAFAF8 !important;
    color: #1A1916 !important;
}
.stTextInput > div > div > input:focus {
    border-color: #5DC8B0 !important;
    box-shadow: 0 0 0 3px rgba(93,200,176,.15) !important;
}

[data-testid="stAlert"] {
    border-radius: 12px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

.stSpinner > div { color: #5DC8B0 !important; }

.card {
    background: #FFFFFF;
    border: 1px solid #E5E2DA;
    border-radius: 16px;
    padding: 24px 26px;
    margin-bottom: 16px;
    animation: fadeUp .3s ease both;
}
.hero-section { text-align: center; padding: 52px 0 36px; }
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: #F0F0EB;
    color: #6B6960;
    font-size: 11px;
    font-weight: 600;
    padding: 5px 14px;
    border-radius: 100px;
    letter-spacing: .05em;
    text-transform: uppercase;
    margin-bottom: 18px;
}
.live-dot {
    width: 6px; height: 6px;
    background: #5DC8B0;
    border-radius: 50%;
    display: inline-block;
    animation: blink 1.4s ease-in-out infinite;
}
.hero-headline {
    font-family: 'Instrument Serif', serif;
    font-size: 48px;
    line-height: 1.1;
    color: #1A1916;
    margin-bottom: 14px;
}
.hero-headline em { color: #5DC8B0; font-style: italic; }
.hero-sub {
    font-size: 16px;
    color: #7A7870;
    line-height: 1.65;
    max-width: 420px;
    margin: 0 auto 36px;
}
.mode-card {
    background: #FFFFFF;
    border: 1.5px solid #E5E2DA;
    border-radius: 16px;
    padding: 22px 18px;
    text-align: center;
}
.mode-emoji { font-size: 28px; margin-bottom: 10px; }
.mode-title {
    font-family: 'Instrument Serif', serif;
    font-size: 18px;
    color: #1A1916;
    margin-bottom: 5px;
}
.mode-desc { font-size: 12.5px; color: #9B9890; line-height: 1.5; }

.agent-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #EFF9F7;
    color: #0D8A75;
    font-size: 11px;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 100px;
    letter-spacing: .05em;
    text-transform: uppercase;
    margin-bottom: 14px;
}
.progress-bar-wrap {
    height: 3px;
    background: #E5E2DA;
    border-radius: 99px;
    overflow: hidden;
    margin-bottom: 6px;
}
.progress-bar-fill {
    height: 100%;
    background: #5DC8B0;
    border-radius: 99px;
    transition: width .4s ease;
}
.lesson-text {
    font-size: 15px;
    line-height: 1.8;
    color: #4A4840;
    white-space: pre-wrap;
}
.answer-card {
    background: #EFF9F7;
    border: 1px solid #C5EDE4;
    border-radius: 14px;
    padding: 18px 20px;
    margin-top: 16px;
    animation: fadeUp .25s ease both;
}
.answer-who {
    font-size: 10.5px;
    font-weight: 700;
    color: #0D8A75;
    letter-spacing: .07em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.answer-text { font-size: 14.5px; color: #1C4A42; line-height: 1.75; }
.quiz-answer {
    background: #FAFAF8;
    border: 1px solid #E5E2DA;
    border-radius: 14px;
    padding: 14px 16px;
    margin: 10px 0 20px;
}
.quiz-answer-label {
    font-size: 10.5px;
    font-weight: 700;
    color: #9B9890;
    letter-spacing: .07em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.quiz-answer-text {
    font-size: 14px;
    color: #4A4840;
    line-height: 1.7;
}
.quiz-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin: 12px 0 18px;
    flex-wrap: wrap;
}
.quiz-intro {
    font-size: 13px;
    color: #7A7870;
    margin: 0;
}
.quiz-feedback {
    border-radius: 14px;
    padding: 14px 16px;
    margin: 12px 0 20px;
}
.quiz-feedback.correct {
    background: #EFF9F7;
    border: 1px solid #C5EDE4;
}
.quiz-feedback.incorrect {
    background: #FFF5F2;
    border: 1px solid #F3D1C6;
}
.quiz-feedback-title {
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: .07em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.quiz-feedback.correct .quiz-feedback-title,
.quiz-feedback.correct .quiz-answer-text {
    color: #1C4A42;
}
.quiz-feedback.incorrect .quiz-feedback-title,
.quiz-feedback.incorrect .quiz-answer-text {
    color: #7B3B2C;
}
.info-hint {
    background: #F0F0EB;
    border-radius: 12px;
    padding: 14px 16px;
    margin-top: 14px;
}
.info-hint-label {
    font-size: 10.5px;
    font-weight: 700;
    color: #9B9890;
    letter-spacing: .07em;
    text-transform: uppercase;
    margin-bottom: 5px;
}
.info-hint-text { font-size: 12.5px; color: #7A7870; line-height: 1.6; }
.divider { height: 1px; background: #E5E2DA; margin: 28px 0; }

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes blink {
    0%,100% { opacity: 1; }
    50%      { opacity: .25; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def split_sections(text):
    return [s.strip() for s in text.split("\n\n") if s.strip()]

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
    if not review.get("approved"):
        st.warning("The review could not approve this draft. Check the source passages before relying on it.")
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
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "llm_service" not in st.session_state:
    st.session_state.llm_service = LLMService()
if "retrieval_agent" not in st.session_state:
    st.session_state.retrieval_agent = RetrievalAgent()
if "routing_agent" not in st.session_state:
    st.session_state.routing_agent = RoutingAgent(llm_service=st.session_state.llm_service)
if "explaining_agent" not in st.session_state:
    st.session_state.explaining_agent = ExplainingAgent(llm_service=st.session_state.llm_service)
if "quiz_agent" not in st.session_state:
    st.session_state.quiz_agent = QuizAgent(llm_service=st.session_state.llm_service)
if "query_enhancer_agent" not in st.session_state:
    st.session_state.query_enhancer_agent = QueryEnhancerAgent(llm_service=st.session_state.llm_service)
if "response_review_agent" not in st.session_state:
    st.session_state.response_review_agent = ResponseReviewAgent(llm_service=st.session_state.llm_service)

live_ready = st.session_state.llm_service.is_configured()

if st.session_state.page != "sample":
    if not live_ready:
        st.caption("Live AI is not connected yet. Explore the sample preview below.")
    if st.session_state.document_library:
        st.caption("Uploads are held for this session only. Lecture excerpts are sent to the AI provider when you request an AI response.")
        if st.button("Clear my session", key="clear_session"):
            st.session_state.retrieval_agent.close()
            # Preserve this session's LLM budget identity when clearing documents.
            service = st.session_state.llm_service
            st.session_state.clear()
            st.session_state.llm_service = service
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# HOME PAGE
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.page == "sample":
    render_sample()

elif st.session_state.page == "home":

    st.markdown("""
    <div class="hero-section">
        <div class="hero-eyebrow">
            <span class="live-dot"></span>Multi-agent AI tutor
        </div>
        <div class="hero-headline">Learn smarter,<br>not <em>harder.</em></div>
        <div class="hero-sub">
            Upload your lecture notes and let your AI study buddy do the heavy lifting.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Try the sample preview →", key="try_sample", type="primary", use_container_width=True):
        st.session_state.page = "sample"
        st.rerun()
    st.caption("No account or PDF needed · Prewritten examples · About two minutes")

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        st.markdown("""
        <div class="mode-card">
            <div class="mode-emoji">📚</div>
            <div class="mode-title">Study</div>
            <div class="mode-desc">Guided, section-by-section explanations from your own notes.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("Start Studying", use_container_width=True, key="btn_study", disabled=not live_ready):
            st.session_state.mode = "study"
            st.session_state.route = st.session_state.routing_agent.route_mode("study")
            st.session_state.router_result = None
            st.rerun()

    with col2:
        st.markdown("""
        <div class="mode-card">
            <div class="mode-emoji">🧠</div>
            <div class="mode-title">Practice</div>
            <div class="mode-desc">AI-generated quiz questions drawn from your own material.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("Start Practicing", use_container_width=True, key="btn_practice", disabled=not live_ready):
            st.session_state.mode = "practice"
            st.session_state.route = st.session_state.routing_agent.route_mode("practice")
            st.session_state.router_result = None
            st.rerun()

    with col3:
        st.markdown("""
        <div class="mode-card">
            <div class="mode-emoji">✨</div>
            <div class="mode-title">Ask</div>
            <div class="mode-desc">Ask for summaries, navigation, or custom help from the routing agent.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("Ask Study Buddy", use_container_width=True, key="btn_other", disabled=not live_ready):
            st.session_state.mode = "other"
            st.session_state.route = st.session_state.routing_agent.route_mode("other")
            st.session_state.router_result = None
            st.rerun()

    if st.session_state.document_library:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        badge("Session Files · Available")
        st.markdown(
            "<h3 style='font-size:22px;margin-bottom:4px;'>Files in this session</h3>"
            "<p style='font-size:13px;color:#7A7870;margin-bottom:16px;'>"
            "These uploads stay available while the app is open. You can switch between them without re-uploading.</p>",
            unsafe_allow_html=True,
        )

        doc_options = list(st.session_state.document_library.keys())
        default_index = 0
        if st.session_state.active_document_name in doc_options:
            default_index = doc_options.index(st.session_state.active_document_name)

        selected_session_doc = st.selectbox(
            "Available session files",
            doc_options,
            index=default_index,
            key="session_doc_selector",
        )

        selected_doc_meta = st.session_state.document_library[selected_session_doc]
        active_label = "Yes" if selected_session_doc == st.session_state.active_document_name else "No"
        st.caption(
            f"Sections indexed: {selected_doc_meta['section_count']} • Active now: {active_label}"
        )

        if st.button("Use This File", use_container_width=True, key="use_session_doc_btn"):
            try:
                activate_document(selected_session_doc)
                reset_learning_views()
                st.success(f"{selected_session_doc} is now the active file.")
            except Exception as exc:
                show_error(exc)

    # STUDY / PRACTICE DOCUMENT FLOW
    if st.session_state.route in ("explaining", "quiz"):
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        is_study = st.session_state.route == "explaining"
        upload_key = "study_upload" if is_study else "quiz_upload"

        upload_container = st.container()
        with upload_container:
            badge("Routing Agent · " + ("Study" if is_study else "Practice") + " Mode")

            st.markdown(
                "<h3 style='font-size:22px;margin-bottom:4px;'>Upload your material</h3>"
                "<p style='font-size:13px;color:#7A7870;margin-bottom:20px;'>"
                "Text-based PDFs · up to 5 MB and 40 pages · no confidential material.</p>",
                unsafe_allow_html=True,
            )

            existing_docs = list(st.session_state.document_library.keys())
            if existing_docs:
                selected_existing_doc = st.selectbox(
                    "Reuse an uploaded file",
                    existing_docs,
                    index=existing_docs.index(st.session_state.active_document_name)
                    if st.session_state.active_document_name in existing_docs else 0,
                    key=f"existing_doc_{upload_key}",
                )

                if st.button("Use Selected File →", use_container_width=True, key=f"use_existing_{upload_key}"):
                    try:
                        with st.spinner("Loading your saved session document…"):
                            activate_document(selected_existing_doc)
                            reset_learning_views()

                        if is_study:
                            st.session_state.page = "explaining"
                        else:
                            st.session_state.page = "quiz"
                            st.session_state.quiz_query = "Create a practice quiz from this lecture."
                        st.rerun()
                    except Exception as exc:
                        show_error(exc)

                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            uploaded = st.file_uploader(
                "Choose a PDF",
                type="pdf",
                key=upload_key,
                label_visibility="collapsed",
                max_upload_size=5,
            )

            if uploaded:
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                prep = st.button("Prepare Document →", use_container_width=True, key="prep_btn")

                if prep:
                    try:
                        with st.spinner("Reading and indexing your document…"):
                            chunks = save_uploaded_document(uploaded)
                            reset_learning_views()

                        st.success(f"✓ Indexed {len(chunks)} sections from {uploaded.name} — you're ready to go.")

                        if is_study:
                            st.session_state.page = "explaining"
                            st.rerun()
                        else:
                            st.session_state.page = "quiz"
                            st.session_state.quiz_query = "Create a practice quiz from this lecture."
                            st.rerun()
                    except Exception as exc:
                        show_error(exc)

            st.markdown("""
            <div class="info-hint">
                <div class="info-hint-label">How it works</div>
                <div class="info-hint-text">
                    Your PDF is kept in this session and searched for relevant passages.
                    Answers include page references so you can check the source.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # OTHER FLOW: paid work only runs on an explicit submit, never on a rerun.
    elif st.session_state.route == "other":
        st.divider()
        st.subheader("Ask about your lecture")
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


# ─────────────────────────────────────────────────────────────────────────────
# EXPLAINING PAGE
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.page == "explaining":

    if st.button("← Back to home", key="back_btn"):
        st.session_state.page = "home"
        st.session_state.explanation = ""
        st.session_state.retrieved_chunks = []
        st.session_state.lesson_sections = []
        st.session_state.current_section_index = 0
        st.session_state.last_answer = ""
        st.rerun()

    st.markdown("""
    <div style="padding:20px 0 8px;">
        <h1 style="font-size:38px;margin:0 0 6px;">Today's Lesson</h1>
        <p style="font-size:14px;color:#7A7870;margin:0;">
            Work through each section at your own pace, then ask anything.
        </p>
    </div>
    """, unsafe_allow_html=True)

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

        lesson_container = st.container()
        with lesson_container:
            badge("Explaining Agent · Active")
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

    ask_container = st.container()
    with ask_container:
        badge("Explaining Agent · Ask Anything")

        st.markdown(
            "<h3 style='font-size:20px;margin:0 0 4px;'>Have a question?</h3>"
            "<p style='font-size:13px;color:#7A7870;margin:0 0 16px;'>"
            "Ask anything about the material — your agent will find the answer.</p>",
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
        if st.session_state.last_enhanced_query:
            st.caption(
                f"Query Enhancer used: {st.session_state.last_enhanced_query.get('retrieval_query', '')}"
            )
        if st.session_state.last_review_notes:
            st.caption(f"Response Review Agent: {st.session_state.last_review_notes}")
        st.markdown(st.session_state.last_answer)

# ─────────────────────────────────────────────────────────────────────────────
# QUIZ PAGE
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.page == "quiz":

    top_l, top_r = st.columns([1, 3], gap="small")
    with top_l:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("← Back to home", key="quiz_back_btn"):
            st.session_state.page = "home"
            st.session_state.quiz_data = None
            st.session_state.quiz_query = ""
            st.session_state.revealed_answers = {}
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="padding:20px 0 8px;">
        <h1 style="font-size:38px;margin:0 0 6px;">Practice Quiz</h1>
        <p style="font-size:14px;color:#7A7870;margin:0;">
            Test yourself on the key ideas from your uploaded material.
        </p>
    </div>
    """, unsafe_allow_html=True)

    badge("Quiz Agent · Active")
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

    st.markdown('<div class="btn-teal">', unsafe_allow_html=True)
    generate_quiz = st.button("Generate Quiz →", use_container_width=True, key="generate_quiz_btn")
    st.markdown('</div>', unsafe_allow_html=True)

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
        if st.session_state.last_enhanced_query:
            st.caption(
                f"Query Enhancer used: {st.session_state.last_enhanced_query.get('retrieval_query', '')}"
            )
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
                st.radio(
                    "Choose one",
                    question.get("options", []),
                    key=question_key,
                    label_visibility="collapsed",
                    index=None,
                )
            else:
                st.text_input(
                    "Your answer",
                    key=short_answer_key,
                    label_visibility="collapsed",
                    placeholder="Type your answer here",
                    max_chars=2000,
                )

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

if st.session_state.page != "sample" and st.session_state.review_approved is False:
    st.warning("This explanation is an unapproved draft. Verify it against the source passages.")

source_groups = []
if st.session_state.page == "explaining":
    if st.session_state.lesson_sections:
        source_groups.append(("Lesson evidence", st.session_state.lesson_sources))
    if st.session_state.last_answer:
        source_groups.append(("Follow-up evidence", st.session_state.answer_sources))
elif st.session_state.page == "quiz" and st.session_state.quiz_data:
    source_groups.append(("Quiz evidence", st.session_state.quiz_sources))
elif st.session_state.page == "home" and st.session_state.other_payload:
    source_groups.append(("Response evidence", st.session_state.other_payload.get("sources", [])))

if any(sources for _, sources in source_groups):
    with st.expander("Check the source passages"):
        st.caption("These passages were supplied for the displayed result. Check its citations and claims against them.")
        for label, sources in source_groups:
            if sources:
                st.subheader(label)
            for source in sources:
                st.write(f"**{source['document']} · page {source['page']}**")
                st.write(source["text"])

if st.session_state.page == "home":
    st.divider()
    with st.expander("About Study Buddy"):
        st.write("Built by Aya Taje for CS494 Agentic AI at the University of Illinois Chicago.")
        st.write("Six focused agents coordinate routing, query enhancement, retrieval, explanations, quizzes and response review. The live app uses Python, Streamlit, sentence-transformer embeddings and ChromaDB.")
        st.caption("Text-based PDFs work best. AI answers and short-answer grading can be wrong. Uploads do not persist across expired sessions or restarts. No accounts or long-term document library are provided.")
        repository = str(setting("SOURCE_REPOSITORY_URL", ""))
        if repository.startswith("https://github.com/"):
            st.link_button("View the source code", repository)
