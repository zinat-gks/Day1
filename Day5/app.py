"""
Yessenov Foundation Grant Assistant — Streamlit chat on gemma4 + RAG.

Run:  streamlit run app.py

UI/UX layer only. All retrieval, model calls and anti-hallucination logic live
in rag.py (untouched). The brief's hard rule holds: answer only from Foundation
data and say so when unknown. Fully bilingual UI (English / Russian).
"""

import base64
from datetime import datetime

import requests
import streamlit as st

import config as c
import rag

st.set_page_config(page_title="Yessenov Grant Assistant", page_icon="🎓",
                   layout="wide", initial_sidebar_state="expanded")

# ============================================================================
# BRAND ASSETS  (inline SVG logo / avatars — swap for the real logo file if you
# have one: replace these data URIs)
# ============================================================================
def _uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def _png_uri(path: str) -> str:
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


# Official Foundation logo (transparent background) for the sidebar.
SIDEBAR_LOGO = _png_uri("assets/yessenov_logo.png")

OWL = ("<path d='M24 11c-1.6-2.4-4-3.6-4-3.6s.3 2.4 1.3 3.9C18.5 12.4 17 15 17 18"
       "c0 4 3.1 7 7 7s7-3 7-7c0-3-1.5-5.6-4.3-6.7C27.7 9.8 28 7.4 28 7.4S25.6 8.6 24 11z' fill='%FILL%'/>"
       "<circle cx='21' cy='18' r='1.7' fill='%EYE%'/><circle cx='27' cy='18' r='1.7' fill='%EYE%'/>")

ASSIST_AVATAR = _uri(
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'>"
    "<circle cx='24' cy='24' r='24' fill='#6D44C4'/>"
    + OWL.replace("%FILL%", "#FFFFFF").replace("%EYE%", "#6D44C4") + "</svg>")

USER_AVATAR = _uri(
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'>"
    "<rect width='48' height='48' rx='13' fill='#F4ECCB'/>"
    "<circle cx='19' cy='21' r='2.2' fill='#C79A3E'/><circle cx='29' cy='21' r='2.2' fill='#C79A3E'/>"
    "<path d='M18 29c2 2.4 10 2.4 12 0' stroke='#C79A3E' stroke-width='2' fill='none' stroke-linecap='round'/></svg>")

# ============================================================================
# TRANSLATIONS  (every UI string in both languages)
# ============================================================================
T = {
    "en": {
        "title": "Yessenov Foundation Assistant",
        "welcome": ("Welcome! I'm here to help you find information about grants, scholarships, "
                    "programs, eligibility, deadlines, and application rules."),
        "chip_programs": "📖 Programs", "chip_eligibility": "🧑 Eligibility",
        "chip_deadlines": "📅 Deadlines", "chip_apply": "📄 How to apply",
        "q_programs": "What programs are available?",
        "q_eligibility": "Who can apply for the Yessenov Scholarship?",
        "q_deadlines": "What are the application deadlines?",
        "q_apply": "How do I apply and what documents are required?",
        "new_conversation": "💬  New conversation", "email_summary": "📧  Email summary",
        "send_admin": "Send to admin", "sent_ok": "Sent ✅", "no_convo": "No conversation yet.",
        "sending": "Sending…",
        "disclaimer": "🛡️ Answers are based only on collected Foundation data.",
        "copyright": "© Yessenov Foundation",
        "you": "You", "assistant": "Yessenov Foundation Assistant",
        "sources": "📄 Sources ({n})  ·  click to view",
        "searching": "Searching Foundation data…",
        "input_placeholder": "Ask about grants, scholarships, eligibility, deadlines…",
        "private": "🔒 Your conversations are private and secure.",
        "error": "⚠️ Sorry, I couldn't reach the model just now. Please try again.",
        "theme_light": "☀️ Light", "theme_dark": "🌙 Dark",
    },
    "ru": {
        "title": "Yessenov Foundation Assistant",
        "welcome": ("Здравствуйте! Я помогу найти информацию о грантах, стипендиях, программах, "
                    "требованиях, дедлайнах и правилах подачи заявок."),
        "chip_programs": "📖 Программы", "chip_eligibility": "🧑 Кто может подать",
        "chip_deadlines": "📅 Дедлайны", "chip_apply": "📄 Как подать заявку",
        "q_programs": "Какие программы доступны?",
        "q_eligibility": "Кто может подать на стипендию Есенова?",
        "q_deadlines": "Какие дедлайны подачи заявок?",
        "q_apply": "Как подать заявку и какие документы нужны?",
        "new_conversation": "💬  Новый разговор", "email_summary": "📧  Сводка на почту",
        "send_admin": "Отправить администратору", "sent_ok": "Отправлено ✅",
        "no_convo": "Пока нет разговора.", "sending": "Отправка…",
        "disclaimer": "🛡️ Ответы основаны только на собранных данных фонда.",
        "copyright": "© Фонд Yessenov",
        "you": "Вы", "assistant": "Yessenov Foundation Assistant",
        "sources": "📄 Источники ({n})  ·  нажмите, чтобы открыть",
        "searching": "Идёт поиск по данным фонда…",
        "input_placeholder": "Спросите о грантах, стипендиях, требованиях, дедлайнах…",
        "private": "🔒 Ваши разговоры конфиденциальны и защищены.",
        "error": "⚠️ Извините, не удалось связаться с моделью. Попробуйте ещё раз.",
        "theme_light": "☀️ Светлая", "theme_dark": "🌙 Тёмная",
    },
}

# ============================================================================
# THEME PALETTES  (Yessenov purple identity — Light by default, elegant Dark)
# ============================================================================
THEMES = {
    "Light": dict(
        appBg="#F6F6FA", sideA="#4A2A8C", sideB="#371E6B", sideText="#FFFFFF",
        sideMuted="rgba(255,255,255,.66)", sideBtn="rgba(255,255,255,.12)",
        title="#5B3B9B", primary="#6D44C4", orange="#E96A45",
        card="#FFFFFF", cardBorder="#ECEAF3", text="#322E47", sub="#8B8699",
        userBg="#ECE9F8", userBorder="#E1DBF2",
        chipBg="#FFFFFF", chipBorder="#E7E4F0", chipText="#4A4660", chipIcon="#6D44C4",
        srcBg="#FAF9FD", srcBorder="#ECEAF3",
        shadow="0 1px 2px rgba(40,30,80,.05), 0 10px 30px rgba(40,30,80,.05)"),
    "Dark": dict(
        appBg="#15122A", sideA="#2A1A52", sideB="#1A1138", sideText="#FFFFFF",
        sideMuted="rgba(255,255,255,.6)", sideBtn="rgba(255,255,255,.1)",
        title="#BCA8EE", primary="#8B5CF6", orange="#E96A45",
        card="#211C3C", cardBorder="#332A54", text="#E9E6F5", sub="#A39FC0",
        userBg="#2A2350", userBorder="#3A2F66",
        chipBg="#211C3C", chipBorder="#332A54", chipText="#D3CDEC", chipIcon="#BCA8EE",
        srcBg="#1C1838", srcBorder="#332A54",
        shadow="0 1px 2px rgba(0,0,0,.3), 0 12px 34px rgba(0,0,0,.28)"),
}

_TOKENS = {
    "appBg": "APPBG", "sideA": "SIDEA", "sideB": "SIDEB", "sideText": "SIDETEXT",
    "sideMuted": "SIDEMUTED", "sideBtn": "SIDEBTN", "title": "TITLE", "primary": "PRIMARY",
    "orange": "ORANGE", "card": "CARD", "cardBorder": "CARDBORDER", "text": "TEXT",
    "sub": "SUB", "userBg": "USERBG", "userBorder": "USERBORDER", "chipBg": "CHIPBG",
    "chipBorder": "CHIPBORDER", "chipText": "CHIPTEXT", "chipIcon": "CHIPICON",
    "srcBg": "SRCBG", "srcBorder": "SRCBORDER", "shadow": "SHADOW",
}


def inject_css(t: dict):
    css = """
    /* ---------- fonts ---------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"], .stApp, button, input, textarea {
        font-family:'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif; }

    /* ---------- page ---------- */
    .stApp { background:__APPBG__; }
    #MainMenu, [data-testid="stToolbar"], footer, [data-testid="stHeader"] { visibility:hidden; height:0; }
    .block-container { max-width:1120px; padding:1.4rem 2rem 7rem; }
    h1,h2,h3,p,li,span,label,div { color:__TEXT__; }

    /* ---------- left sidebar (brand) ---------- */
    section[data-testid="stSidebar"] { width:300px !important; border:none; }
    section[data-testid="stSidebar"] > div { background:linear-gradient(180deg,__SIDEA__,__SIDEB__); }
    section[data-testid="stSidebar"] * { color:__SIDETEXT__; }
    .side-logo { text-align:center; padding:1.6rem .6rem .8rem; }
    .side-logo img { width:90%; max-width:230px; height:auto; }
    section[data-testid="stSidebar"] .stButton>button {
        background:__SIDEBTN__; border:1px solid rgba(255,255,255,.16); color:#fff; border-radius:11px;
        width:100%; padding:.55rem; font-weight:500; box-shadow:none; }
    section[data-testid="stSidebar"] .stButton>button:hover { background:rgba(255,255,255,.2); border-color:rgba(255,255,255,.3); }
    section[data-testid="stSidebar"] [data-testid="stPopover"] > button {
        background:__SIDEBTN__; border:1px solid rgba(255,255,255,.16); color:#fff !important;
        border-radius:11px; width:100%; box-shadow:none; }
    section[data-testid="stSidebar"] [data-testid="stPopover"] > button:hover { background:rgba(255,255,255,.2); }
    section[data-testid="stSidebar"] [data-testid="stPopover"] > button * { color:#fff !important; }
    .side-foot { color:__SIDEMUTED__ !important; font-size:.8rem; }
    .side-foot * { color:__SIDEMUTED__ !important; }
    .side-div { border-top:1px solid rgba(255,255,255,.14); margin:.8rem 0; }

    /* ---------- top bar ---------- */
    .topbar { display:flex; align-items:center; gap:.7rem; padding-bottom:.2rem; }
    .topbar .mark { width:40px; height:40px; border-radius:11px; background:__ORANGE__; color:#fff !important;
        display:inline-flex; align-items:center; justify-content:center; font-weight:700; font-size:1.25rem; }
    .topbar .t { font-size:1.5rem; font-weight:700; color:__TITLE__ !important; }
    .welcome { font-size:1.18rem; color:__TEXT__; margin:1rem 0 1.3rem; max-width:62ch; line-height:1.55; }

    /* ---------- suggestion chips ---------- */
    div[data-testid="stHorizontalBlock"] .stButton>button {
        background:__CHIPBG__; border:1px solid __CHIPBORDER__; color:__CHIPTEXT__ !important;
        border-radius:999px; padding:.55rem 1.1rem; font-weight:600; font-size:.92rem;
        box-shadow:__SHADOW__; }
    div[data-testid="stHorizontalBlock"] .stButton>button:hover { border-color:__PRIMARY__; color:__PRIMARY__ !important; }

    /* ---------- chat cards ---------- */
    [data-testid="stChatMessage"] { border-radius:16px; padding:.7rem 1.2rem .8rem; margin:.5rem 0; gap:.8rem; }
    [data-testid="stChatMessage"]:has(.user-badge) { background:__USERBG__; border:1px solid __USERBORDER__; }
    [data-testid="stChatMessage"]:has(.assistant-badge) { background:__CARD__; border:1px solid __CARDBORDER__; box-shadow:__SHADOW__; }
    [data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] li { color:__TEXT__ !important; line-height:1.6; font-size:.97rem; }
    [data-testid="stChatMessageContent"] li { margin-bottom:.35rem; }
    .msg-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:.2rem; }
    .msg-head .who { font-weight:700; font-size:.96rem; color:__TITLE__ !important; }
    .msg-head .meta { font-size:.78rem; color:__SUB__ !important; }
    .msg-head .meta * { color:__SUB__ !important; }

    /* ---------- calm 'I don't know' ---------- */
    .calm { background:__SRCBG__; border:1px solid __SRCBORDER__; border-radius:12px; padding:.7rem .9rem;
        color:__SUB__ !important; font-size:.95rem; display:flex; gap:.5rem; }
    .calm span { color:__SUB__ !important; }

    /* ---------- sources ---------- */
    [data-testid="stExpander"] { border:none !important; background:transparent !important; }
    [data-testid="stExpander"] details { background:__SRCBG__; border:1px solid __SRCBORDER__; border-radius:12px; }
    [data-testid="stExpander"] summary { color:__TEXT__ !important; font-weight:600; font-size:.92rem; padding:.3rem .2rem; }
    [data-testid="stExpander"] summary p { color:__TEXT__ !important; font-weight:600; }
    .yh-src a { color:__PRIMARY__ !important; text-decoration:none; font-size:.84rem; display:block; padding:3px 0; word-break:break-all; }
    .yh-src a:hover { text-decoration:underline; }

    /* ---------- input bar ---------- */
    [data-testid="stChatInput"] { background:__CARD__; border:1.5px solid __CARDBORDER__; border-radius:30px;
        box-shadow:__SHADOW__; }
    [data-testid="stChatInput"] textarea { color:__TEXT__ !important; font-size:.98rem; }
    [data-testid="stChatInputSubmitButton"] { background:__PRIMARY__ !important; border-radius:50% !important; }
    [data-testid="stChatInputSubmitButton"] svg { color:#fff !important; fill:#fff !important; }
    .priv { text-align:center; color:__SUB__ !important; font-size:.82rem; margin-top:.5rem; }
    .priv span { color:__SUB__ !important; }

    /* ---------- top-right controls (themed for light AND dark) ---------- */
    [data-testid="stSelectbox"] label { display:none; }
    [data-baseweb="select"] > div { background:__CARD__ !important; border:1px solid __CARDBORDER__ !important; }
    [data-baseweb="select"] div, [data-baseweb="select"] span, [data-baseweb="select"] svg {
        color:__TEXT__ !important; fill:__TEXT__ !important; }
    [data-baseweb="popover"] [role="listbox"], [data-baseweb="menu"] { background:__CARD__ !important; }
    [data-baseweb="menu"] li { color:__TEXT__ !important; }
    [data-baseweb="menu"] li:hover { background:__SRCBG__ !important; }
    """
    for k, v in t.items():
        css = css.replace("__" + _TOKENS[k] + "__", v)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ============================================================================
# STATE
# ============================================================================
st.session_state.setdefault("messages", [])
st.session_state.setdefault("theme", "Light")
st.session_state.setdefault("lang", "en")
st.session_state.setdefault("pending", None)

CALM_PHRASES = ("don't have that information", "нет такой информации",
                "I can only help with questions about", "don't know based on")


def is_calm(text):
    return any(p in text for p in CALM_PHRASES)


# ============================================================================
# EMAIL (MailerSend REST; only on explicit click)
# ============================================================================
def send_summary_email(summary_text):
    payload = {"from": {"email": c.FROM_EMAIL, "name": c.FROM_NAME},
               "to": [{"email": c.ADMIN_EMAIL, "name": "Admin"}],
               "subject": "Yessenov grant chat — conversation summary",
               "text": summary_text, "html": "<pre>" + summary_text + "</pre>"}
    try:
        r = requests.post("https://api.mailersend.com/v1/email",
                          headers={"Authorization": f"Bearer {c.MAILERSEND_KEY}",
                                   "Content-Type": "application/json"}, json=payload, timeout=30)
        return (r.status_code in (200, 202)), f"{r.status_code}: {r.text[:160]}"
    except Exception as e:
        return False, str(e)


def summarize_conversation(history):
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    try:
        return rag.chat([{"role": "system", "content": "Summarize this support chat in 4-6 lines for a "
                          "foundation administrator. Note what the user asked and any application interest."},
                         {"role": "user", "content": convo}], temperature=0.2)
    except Exception as e:
        return f"(summary failed: {e})\n\n{convo}"


# ============================================================================
# TOP BAR  — controls read FIRST (so language/theme apply on the first click),
# then the title renders in the chosen language.
# ============================================================================
left, right = st.columns([2.4, 1])
with right:
    cc = st.columns(2)
    with cc[0]:
        lang = st.selectbox("Language", ["en", "ru"], key="lang",
                            format_func=lambda x: {"en": "🌐 English", "ru": "🌐 Русский"}[x])
    with cc[1]:
        theme = st.selectbox("Theme", ["Light", "Dark"], key="theme",
                             format_func=lambda x: T[lang]["theme_light"] if x == "Light"
                             else T[lang]["theme_dark"])
L = T[lang]
with left:
    st.markdown(f'<div class="topbar"><span class="mark">Y</span>'
                f'<span class="t">{L["title"]}</span></div>', unsafe_allow_html=True)

# CSS injected here — after theme is known, so a switch takes effect immediately
inject_css(THEMES[theme])

# ============================================================================
# SIDEBAR (brand panel) — localized
# ============================================================================
with st.sidebar:
    st.markdown(f'<div class="side-logo"><img src="{SIDEBAR_LOGO}"/></div>',
                unsafe_allow_html=True)
    st.write("")
    if st.button(L["new_conversation"], use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()
    with st.popover(L["email_summary"], use_container_width=True):
        if st.button(L["send_admin"]):
            if st.session_state["messages"]:
                with st.spinner(L["sending"]):
                    ok, info = send_summary_email(summarize_conversation(st.session_state["messages"]))
                st.success(L["sent_ok"]) if ok else st.error(info)
            else:
                st.warning(L["no_convo"])
    st.markdown('<div style="height:34vh"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="side-foot">{L["disclaimer"]}</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-div"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="side-foot">{L["copyright"]}</div>', unsafe_allow_html=True)


# ============================================================================
# WELCOME + SUGGESTION CHIPS (localized; chip questions in the chosen language)
# ============================================================================
st.markdown(f'<div class="welcome">{L["welcome"]}</div>', unsafe_allow_html=True)
st.markdown('<div style="height:.45rem"></div>', unsafe_allow_html=True)

CHIPS = [(L["chip_programs"], L["q_programs"]), (L["chip_eligibility"], L["q_eligibility"]),
         (L["chip_deadlines"], L["q_deadlines"]), (L["chip_apply"], L["q_apply"])]
chip_cols = st.columns(len(CHIPS))
for col, (label, q) in zip(chip_cols, CHIPS):
    with col:
        if st.button(label, use_container_width=True):
            st.session_state["pending"] = q
            st.rerun()

st.write("")
top_k = 6  # fixed; tune in rag.py if needed


# ============================================================================
# RENDER HELPERS
# ============================================================================
def render_sources(urls):
    if urls:
        with st.expander(L["sources"].format(n=len(urls))):
            links = "".join(f'<a href="{u}" target="_blank">🔗 {u}</a>' for u in urls)
            st.markdown(f'<div class="yh-src">{links}</div>', unsafe_allow_html=True)


def render_user(text, ts):
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(f'<div class="user-badge msg-head"><span class="who">{L["you"]}</span>'
                    f'<span class="meta">{ts} ✓✓</span></div>', unsafe_allow_html=True)
        st.markdown(text)


def render_assistant(text, urls, ts):
    with st.chat_message("assistant", avatar=ASSIST_AVATAR):
        st.markdown(f'<div class="assistant-badge msg-head"><span class="who">{L["assistant"]}</span>'
                    f'<span class="meta">{ts} ⧉</span></div>', unsafe_allow_html=True)
        if is_calm(text):
            st.markdown(f'<div class="calm">💡 <span>{text}</span></div>', unsafe_allow_html=True)
        elif text.startswith("⚠️"):
            st.markdown(f'<div class="calm">⚠️ <span>{text[2:].strip()}</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(text)
        render_sources(urls)


# ============================================================================
# HISTORY
# ============================================================================
for m in st.session_state["messages"]:
    if m["role"] == "user":
        render_user(m["content"], m.get("ts", ""))
    else:
        render_assistant(m["content"], m.get("sources", []), m.get("ts", ""))


# ============================================================================
# NEW TURN
# ============================================================================
pending = st.session_state.pop("pending", None)
typed = st.chat_input(L["input_placeholder"])
prompt = typed or pending

if prompt:
    now = datetime.now().strftime("%I:%M %p")
    st.session_state["messages"].append({"role": "user", "content": prompt, "ts": now})
    render_user(prompt, now)

    with st.spinner(L["searching"]):
        try:
            history = [{"role": m["role"], "content": m["content"]}
                       for m in st.session_state["messages"][:-1]]
            ans, hits = rag.answer(prompt, history=history, k=top_k, lang=lang)
        except Exception:
            ans, hits = L["error"], []

    urls = list(dict.fromkeys(m["source_url"] for _, m in hits)) if hits else []
    ats = datetime.now().strftime("%I:%M %p")
    render_assistant(ans, urls, ats)
    st.session_state["messages"].append({"role": "assistant", "content": ans, "sources": urls, "ts": ats})

st.markdown(f'<div class="priv">{L["private"]}</div>', unsafe_allow_html=True)
