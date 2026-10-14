"""Static notebook styling and icons; no model calls or user data."""
from html import escape
import streamlit as st

PATHS = {
 'book': '<path d="M12 5c-3-2-7-2-10-1v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1Z"/><path d="M12 5v15"/>',
 'leaf': '<path d="M5 20C4 8 12 3 20 3c0 9-4 14-12 14"/><path d="M5 21 17 7"/>',
 'quiz': '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h4"/>',
 'ask': '<path d="M21 11c0 5-4 8-9 8-2 0-3 0-5-1l-5 3 1-6c-1-1-1-2-1-4 0-5 4-8 10-8s9 3 9 8Z"/>',
 'file': '<path d="M6 2h8l5 5v15H6Z"/><path d="M14 2v6h5M9 12h7M9 16h7"/>',
}

def icon(name):
 return f'<svg class="notebook-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{PATHS.get(name,PATHS["book"])}</svg>'

def page_heading(title, subtitle=""):
 st.markdown(f'<div class="page-heading"><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>',unsafe_allow_html=True)

def apply_theme():
 st.markdown('''<style>
:root {--ink:#292c25;--sage:#536e57;--muted:#64695e;--line:#d9d6c9;--paper:#fffdf7;}
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"]{background:#f5f1e7;color:var(--ink);}
[data-testid="stAppViewContainer"]{background-image:radial-gradient(ellipse at top left,#fbf9f1,transparent 65%);}
[data-testid="stMainBlockContainer"],.block-container{max-width:1280px;padding:2rem 2rem 4rem;}
#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none;}
[data-testid="stHeader"]{background:transparent;}
h1,h2,h3,.page-heading h1,.brand-name,.mode-title,.note-title{font-family:Georgia,'Times New Roman',serif!important;color:var(--ink);font-weight:500;letter-spacing:-.025em;}
p,label,button,input,textarea,[data-testid="stCaptionContainer"]{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}
p{line-height:1.7;}h1{font-size:2.5rem!important;}h2{font-size:1.8rem!important;}h3{font-size:1.35rem!important;}
[data-testid="stCaptionContainer"]{color:var(--muted);}
[data-testid="stIconMaterial"]{font-family:'Material Symbols Rounded'!important;}
[data-testid="stButton"] button,[data-testid="stDownloadButton"] button,[data-testid="stLinkButton"] a {border:1px solid #9eaf99;border-radius:8px;background:#fffdf7;color:#38513f;padding:.55rem 1rem;font-weight:500;min-height:42px;box-shadow:none;}
[data-testid="stButton"] button:hover,[data-testid="stDownloadButton"] button:hover{background:#e8eee1;border-color:var(--sage);color:#2f4835;}
[data-testid="stButton"] button[kind="primary"],[data-testid="stFormSubmitButton"] button{background:var(--sage);color:white;border-color:var(--sage);}
[data-testid="stButton"] button[kind="primary"]:hover{background:#405a44;}
button:disabled{opacity:.5;}button:focus-visible{outline:3px solid #8d9e85!important;outline-offset:3px;}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{background:#fffef9;border:1px solid #c5cab9;border-radius:7px;color:var(--ink);}
[data-baseweb="select"]>div{background:#fffef9;border-color:#c5cab9;border-radius:7px;}
[data-testid="stFileUploader"] section{background:#fcfaf2;border:1px dashed #a3af98;border-radius:9px;padding:1.4rem;}
[data-testid="stFileUploader"] button{border-radius:7px;color:#38513f;}
[data-testid="stExpander"]{border-color:var(--line);border-radius:9px;background:#fdfbf5;}
[data-testid="stAlert"]{border-radius:8px;}
[data-testid="stTabs"] [role="tablist"]{gap:1.25rem;}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:#3e5d43;}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--line);border-radius:12px;}
.st-key-app_header{border-bottom:1px solid var(--line);padding-bottom:1rem;margin-bottom:1rem;}
.brand{display:flex;align-items:center;gap:12px;min-height:44px;}.brand-name{font-size:1.65rem;}.brand-credit{font-size:.78rem;color:var(--muted);padding-left:12px;border-left:1px solid var(--line);}
.notebook-icon{width:28px;height:28px;color:var(--sage);flex-shrink:0;}
.st-key-app_header button{border:none;background:transparent!important;padding:.5rem .55rem;color:var(--muted);min-height:44px;}
.st-key-app_header button[kind="primary"]{color:#324d38!important;border-bottom:2px solid var(--sage);border-radius:0;}
.page-heading{margin:.6rem 0 1.3rem;}.page-heading h1{margin:0 0 .45rem;font-size:clamp(1.8rem,3.6vw,2.8rem)!important;line-height:1.2;}.page-heading p{color:var(--muted);font-size:1rem;margin:0;max-width:760px;}
.eyebrow,.agent-badge{font-size:.72rem;color:var(--sage);letter-spacing:.08em;text-transform:uppercase;margin-bottom:.7rem;}
.st-key-start_notes,.st-key-upload_paper,.st-key-lesson_paper,.st-key-ask_paper,.st-key-quiz_paper,.st-key-sample_lesson_paper,.st-key-sample_quiz_paper,.st-key-sample_source_paper,.st-key-sample_followup_paper{background:var(--paper);padding:1.25rem;box-shadow:0 3px 10px #534b3510;border:1px solid var(--line);border-radius:12px;}
.st-key-notebook_guide,.st-key-evidence_rail,.st-key-sample_notebook_guide{background-color:#fbf9f0;background-image:repeating-linear-gradient(transparent,transparent 31px,#ccd8d288 32px);padding:1.3rem 1.35rem;border:1px solid var(--line);border-radius:10px;box-shadow:2px 3px 9px #534b3510;}
.st-key-notebook_guide,.st-key-evidence_rail,.st-key-sample_notebook_guide{position:relative;border-left:6px solid #cbd4bf;}
.st-key-notebook_guide:after,.st-key-evidence_rail:after{content:"";position:absolute;right:20px;top:-10px;width:10px;height:32px;border:2px solid #b0a48a;border-radius:8px;transform:rotate(18deg);pointer-events:none;}
.notebook-note{position:relative;}.note-title{font-size:1.7rem;margin-bottom:1rem;}.guide-step{display:flex;gap:12px;margin:1.2rem 0;align-items:flex-start;}.step-number{width:28px;height:28px;border-radius:50%;border:1px solid #acb99e;display:flex;align-items:center;justify-content:center;font-family:Georgia,serif;flex-shrink:0;color:#3e5b42;}.step-title{font-family:Georgia,serif;font-size:1.1rem;color:var(--ink);}.step-desc{font-size:.86rem;line-height:1.6;color:var(--muted);margin-top:3px;}
.st-key-mode_study,.st-key-mode_practice,.st-key-mode_ask{background:#fffdf6;border:1px solid var(--line);border-radius:11px;padding:1.1rem 1.2rem;height:100%;}
.mode-card{min-height:122px;}.mode-top{display:flex;align-items:center;gap:12px;}.mode-title{font-size:1.5rem;}.mode-desc{color:var(--muted);font-size:.9rem;line-height:1.6;margin:12px 0 16px;}.mode-card .notebook-icon{width:24px;height:24px;}
.st-key-mode_study button,.st-key-mode_practice button,.st-key-mode_ask button{width:100%;}
.sample-banner{background:#e9eee1;border-left:3px solid #7c9272;padding:.8rem 1rem;border-radius:5px;}
.quiz-feedback,.quiz-answer{padding:1rem;border:1px solid var(--line);border-radius:8px;background:#f7f7ec;margin:1rem 0;}.quiz-feedback.correct{background:#edf2e6;border-color:#c3d0b6;}.quiz-feedback.incorrect{background:#f8eee3;border-color:#dfc7a7;}.quiz-feedback-title,.quiz-answer-label{font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;color:var(--sage);margin-bottom:7px;}.quiz-answer-text{line-height:1.7;}.quiz-toolbar{margin:.8rem 0;}.quiz-intro{color:var(--muted);font-size:.9rem;}
.progress-bar-wrap{height:3px;background:#dedfce;border-radius:3px;margin-bottom:16px;}.progress-bar-fill{height:3px;background:var(--sage);}
.st-key-session_controls{padding:.6rem 0;border-bottom:1px solid var(--line);margin-bottom:1rem;}
@media(max-width:700px){[data-testid="stMainBlockContainer"],.block-container{padding:1rem 1rem 3rem;}.brand-credit{display:none;}.brand-name{font-size:1.4rem;}.page-heading h1{font-size:2rem!important;}[data-testid="stHorizontalBlock"]{flex-wrap:wrap;}.st-key-app_header [data-testid="stHorizontalBlock"]{gap:.3rem;}.st-key-start_notes,.st-key-upload_paper,.st-key-lesson_paper,.st-key-ask_paper,.st-key-quiz_paper{padding:1rem;} }
</style>''',unsafe_allow_html=True)
