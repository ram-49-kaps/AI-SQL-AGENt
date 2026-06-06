"""
Streamlit UI for the AI SQL Agent.

A clean, minimal interface for querying the company database
using natural language. Connects to the FastAPI backend.

Run:
    streamlit run streamlit_app.py

Requires the FastAPI server running at http://localhost:8000
"""

import uuid
import streamlit as st
import requests
import pandas as pd

# ─── Configuration ───────────────────────────────────────────────
API_URL = "http://localhost:8000"
QUERY_ENDPOINT = f"{API_URL}/query"

# ─── Page Config ─────────────────────────────────────────────────
st.set_page_config(
    page_title="AI SQL Agent",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }

    .stApp {
        background: #000000;
    }

    /* ── Header ──────────────────────────────────────── */
    .hero-container {
        text-align: center;
        padding: 2.5rem 1rem 0.5rem;
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.03em;
        margin-bottom: 0.4rem;
    }

    .hero-subtitle {
        font-size: 0.95rem;
        color: #666666;
        font-weight: 400;
        letter-spacing: 0.01em;
    }

    .divider {
        height: 1px;
        background: #1A1A1A;
        border: none;
        margin: 1.2rem 0 1.5rem;
    }

    /* ── Chat Messages ───────────────────────────────── */
    .user-msg {
        background: #FFFFFF;
        color: #000000;
        border-radius: 12px 12px 2px 12px;
        padding: 0.9rem 1.2rem;
        margin: 0.6rem 0;
        font-size: 0.92rem;
        font-weight: 500;
        line-height: 1.5;
    }

    .bot-msg {
        background: #0A0A0A;
        border: 1px solid #1A1A1A;
        border-radius: 12px 12px 12px 2px;
        padding: 1rem 1.3rem;
        margin: 0.6rem 0;
        color: #D4D4D4;
    }

    /* ── SQL Block ───────────────────────────────────── */
    .sql-container {
        background: #0A0A0A;
        border: 1px solid #222222;
        border-radius: 8px;
        padding: 0.9rem 1.1rem;
        margin: 0.7rem 0;
        overflow-x: auto;
    }

    .sql-container code {
        font-family: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace !important;
        font-size: 0.82rem;
        color: #E5E5E5;
        line-height: 1.6;
    }

    .label {
        font-size: 0.65rem;
        font-weight: 600;
        color: #555555;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.4rem;
        display: block;
    }

    /* ── Metric Cards ────────────────────────────────── */
    .metric-row {
        display: flex;
        gap: 0.7rem;
        margin: 0.7rem 0;
    }

    .metric-card {
        background: #0A0A0A;
        border: 1px solid #1A1A1A;
        border-radius: 8px;
        padding: 0.7rem 1rem;
        flex: 1;
        text-align: center;
    }

    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #FFFFFF;
        font-variant-numeric: tabular-nums;
    }

    .metric-label {
        font-size: 0.6rem;
        font-weight: 500;
        color: #555555;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.15rem;
    }

    /* ── Explanation ─────────────────────────────────── */
    .explanation-box {
        background: #0A0A0A;
        border-left: 2px solid #333333;
        border-radius: 0 8px 8px 0;
        padding: 0.9rem 1.2rem;
        margin: 0.7rem 0;
        color: #999999;
        font-size: 0.88rem;
        line-height: 1.65;
    }

    /* ── Ambiguity / Error ───────────────────────────── */
    .ambiguity-box {
        background: #0A0A0A;
        border: 1px solid #333333;
        border-left: 3px solid #888888;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.3rem;
        margin: 0.7rem 0;
        color: #AAAAAA;
        font-size: 0.9rem;
    }

    .error-box {
        background: #0A0A0A;
        border: 1px solid #333333;
        border-left: 3px solid #FF4444;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.3rem;
        margin: 0.7rem 0;
        color: #CC8888;
        font-size: 0.9rem;
    }

    /* ── Sidebar ─────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: #050505;
        border-right: 1px solid #1A1A1A;
    }

    .sidebar-title {
        font-size: 1rem;
        font-weight: 600;
        color: #FFFFFF;
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem;
    }

    .sidebar-sub {
        font-size: 0.72rem;
        color: #555555;
        letter-spacing: 0.02em;
    }

    .section-header {
        font-size: 0.65rem;
        font-weight: 600;
        color: #444444;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin: 1.8rem 0 0.6rem;
    }

    .sample-q {
        background: #0A0A0A;
        border: 1px solid #1A1A1A;
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
        margin: 0.35rem 0;
        color: #999999;
        font-size: 0.8rem;
        line-height: 1.4;
    }

    /* ── Status ──────────────────────────────────────── */
    .status-indicator {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        margin-right: 6px;
        vertical-align: middle;
    }

    .status-on { background: #FFFFFF; }
    .status-off { background: #444444; }

    .status-text {
        font-size: 0.72rem;
        color: #555555;
    }

    /* ── Follow-up label ─────────────────────────────── */
    .followup-header {
        font-size: 0.65rem;
        font-weight: 600;
        color: #444444;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 1rem 0 0.5rem;
    }

    /* ── Welcome state ───────────────────────────────── */
    .welcome-text {
        text-align: center;
        padding: 4rem 1rem 1rem;
    }

    .welcome-heading {
        font-size: 1.15rem;
        color: #555555;
        font-weight: 400;
        margin-bottom: 0.4rem;
    }

    .welcome-sub {
        font-size: 0.82rem;
        color: #333333;
        max-width: 460px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* ── Dataframe ───────────────────────────────────── */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* ── Input ───────────────────────────────────────── */
    .stChatInput > div {
        border-radius: 12px !important;
        border-color: #222222 !important;
        background: #0A0A0A !important;
    }

    .stChatInput > div:focus-within {
        border-color: #444444 !important;
        box-shadow: none !important;
    }

    /* ── Buttons ─────────────────────────────────────── */
    .stButton > button {
        background: #FFFFFF !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.8rem !important;
        padding: 0.45rem 0.9rem !important;
        transition: opacity 0.2s ease !important;
    }

    .stButton > button:hover {
        opacity: 0.85 !important;
    }

    /* ── Hide Streamlit chrome ───────────────────────── */
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    footer { visibility: hidden; }

    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #222222; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ─── Session State ───────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []


# ─── Helpers ─────────────────────────────────────────────────────
def check_api_health() -> bool:
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        return r.status_code == 200 and r.json().get("status") == "healthy"
    except Exception:
        return False


def query_agent(question: str) -> dict:
    try:
        response = requests.post(
            QUERY_ENDPOINT,
            json={"question": question},
            headers={
                "Content-Type": "application/json",
                "X-Session-Id": st.session_state.session_id,
            },
            timeout=60,
        )
        return response.json()
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Cannot connect to the API server. Start it with: python run.py",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def render_response(data: dict):
    """Render a structured response."""

    # ── Ambiguity ────────────────────────────────────
    if "suggestions" in data and data.get("message"):
        st.markdown(f"""
        <div class="ambiguity-box">
            <span class="label">Ambiguous query</span>
            {data.get('reason', 'This question could be interpreted in multiple ways.')}
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="followup-header">Suggestions</div>', unsafe_allow_html=True)
        for suggestion in data.get("suggestions", []):
            if st.button(suggestion, key=f"sug_{hash(suggestion)}"):
                handle_question(suggestion)
                st.rerun()
        return

    # ── Error ────────────────────────────────────────
    if not data.get("success") and "error" in data:
        st.markdown(f"""
        <div class="error-box">
            <span class="label">Error</span>
            {data['error']}
        </div>
        """, unsafe_allow_html=True)

        if data.get("generated_sql"):
            st.markdown(f"""
            <div class="sql-container">
                <span class="label">Generated SQL</span>
                <code>{data['generated_sql']}</code>
            </div>
            """, unsafe_allow_html=True)
        return

    # ── Success ──────────────────────────────────────

    # Metrics
    row_count = data.get("row_count", 0)
    exec_time = data.get("execution_time", "-")
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-value">{row_count}</div>
            <div class="metric-label">Rows</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{exec_time}</div>
            <div class="metric-label">Time</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # SQL
    if data.get("generated_sql"):
        st.markdown(f"""
        <div class="sql-container">
            <span class="label">Generated SQL</span>
            <code>{data['generated_sql']}</code>
        </div>
        """, unsafe_allow_html=True)

    # Explanation
    if data.get("explanation"):
        st.markdown(f"""
        <div class="explanation-box">
            <span class="label">Explanation</span>
            {data['explanation']}
        </div>
        """, unsafe_allow_html=True)

    # Results table
    results = data.get("result", [])
    if results:
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Follow-up questions
    follow_ups = data.get("follow_up_questions", [])
    if follow_ups:
        st.markdown('<div class="followup-header">Follow-up questions</div>', unsafe_allow_html=True)
        cols = st.columns(min(len(follow_ups), 3))
        for i, q in enumerate(follow_ups):
            with cols[i % 3]:
                if st.button(q, key=f"fu_{hash(q)}_{i}"):
                    handle_question(q)
                    st.rerun()


def handle_question(question: str):
    st.session_state.messages.append({"role": "user", "content": question})
    response = query_agent(question)
    st.session_state.messages.append({"role": "assistant", "content": response})


# ─── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 1.2rem 0 0.5rem;">
        <div class="sidebar-title">AI SQL Agent</div>
        <div class="sidebar-sub">Natural Language to SQL</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # API Status
    is_online = check_api_health()
    dot = "status-on" if is_online else "status-off"
    label = "Connected" if is_online else "Offline"
    st.markdown(f"""
    <div class="status-text">
        <span class="status-indicator {dot}"></span>{label}
    </div>
    """, unsafe_allow_html=True)

    if not is_online:
        st.warning("Start the API: `python run.py`")

    # Sample questions
    st.markdown('<div class="section-header">Sample queries</div>', unsafe_allow_html=True)

    sample_questions = [
        "How many employees are in Engineering?",
        "List all projects that are overdue.",
        "Which department has the highest average salary?",
        "Show employees hired after January 2023.",
        "Show all active projects assigned to Engineering employees.",
        "What is the total salary budget by department?",
    ]

    for q in sample_questions:
        st.markdown(f'<div class="sample-q">{q}</div>', unsafe_allow_html=True)
        if st.button("Ask", key=f"s_{hash(q)}"):
            handle_question(q)
            st.rerun()

    st.markdown('<div class="section-header">Session</div>', unsafe_allow_html=True)
    st.caption(f"`{st.session_state.session_id[:8]}`")

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size: 0.65rem; color: #333333; padding: 0.3rem 0;">
        Powered by Groq Llama 3 — FastAPI + Streamlit
    </div>
    """, unsafe_allow_html=True)


# ─── Main Content ────────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-title">AI SQL Agent</div>
    <div class="hero-subtitle">Ask questions about your company database in plain English</div>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

# ── Chat History ─────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-text">
        <div class="welcome-heading">Ask me anything about your company data</div>
        <div class="welcome-sub">
            Query employees, departments, and projects using natural language.
            Try salaries, headcounts, deadlines, or project statuses.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    cols = st.columns(2)
    quick_starts = [
        "How many employees are in each department?",
        "Which department has the highest average salary?",
        "List all overdue projects.",
        "Show employees hired after January 2023.",
    ]
    for i, q in enumerate(quick_starts):
        with cols[i % 2]:
            if st.button(q, key=f"qs_{i}", use_container_width=True):
                handle_question(q)
                st.rerun()

else:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            with st.container():
                render_response(msg["content"])
            st.markdown("")

# ── Chat Input ───────────────────────────────────────────────────
if prompt := st.chat_input("Ask a question about your database...", key="main_input"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f'<div class="user-msg">{prompt}</div>', unsafe_allow_html=True)

    with st.spinner("Generating..."):
        response = query_agent(prompt)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
