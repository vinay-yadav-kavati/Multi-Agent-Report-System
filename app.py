import asyncio
import os
import sys
from dotenv import load_dotenv
import streamlit as st

# ── Load local environment variables (.env) ──────────────────────────────────
load_dotenv()

# ── Ensure src directory is in sys.path ──────────────────────────────────────
SRC_PATH = os.path.join(os.path.dirname(__file__), "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# ── Page config (must be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🔬",
    layout="wide",
)

# ── Safely Mirror Streamlit Secrets to os.environ ────────────────────────────
try:
    for key in ["GOOGLE_API_KEY", "GEMINI_API_KEY", "TAVILY_API_KEY"]:
        if key not in os.environ and key in st.secrets:
            os.environ[key] = str(st.secrets[key])
except Exception:
    # Catches StreamlitSecretNotFoundError when running locally without secrets.toml
    pass

# Normalize GEMINI_API_KEY and GOOGLE_API_KEY so either works
if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
elif "GOOGLE_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

# ── Inline CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #0f1117;
    color: #e2e8f0;
}

.app-header {
    text-align: center;
    padding: 0.8rem 0 0.5rem;
}
.app-header h1 {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}
.app-header p {
    color: #94a3b8;
    font-size: 0.85rem;
    margin: 0;
}

/* Compact Step Cards in 4 columns */
.step-card {
    background: #171b26;
    border: 1px solid #283144;
    border-radius: 10px;
    padding: 0.75rem 0.85rem;
    min-height: 95px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.25s ease;
    margin-bottom: 0.4rem;
}
.step-card.working {
    border-color: #3b82f6;
    background: #172138;
    box-shadow: 0 0 14px rgba(59, 130, 246, 0.25);
}
.step-card.done {
    border-color: #10b981;
    background: #122322;
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.15);
}
.step-card.pending {
    opacity: 0.6;
}

.step-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.4rem;
    margin-bottom: 0.35rem;
}
.step-title {
    font-weight: 600;
    font-size: 0.85rem;
    color: #f1f5f9;
    display: flex;
    align-items: center;
    gap: 0.35rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.badge {
    display: inline-block;
    padding: 0.15rem 0.45rem;
    border-radius: 6px;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    flex-shrink: 0;
}
.badge-working { background: #1d4ed8; color: #bfdbfe; }
.badge-done    { background: #065f46; color: #6ee7b7; }
.badge-pending { background: #334155; color: #94a3b8; }

.step-desc {
    font-size: 0.77rem;
    color: #94a3b8;
    line-height: 1.35;
}

.report-box {
    background: #111827;
    border: 1px solid #374151;
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    line-height: 1.75;
    white-space: pre-wrap;
    font-size: 0.88rem;
    color: #d1d5db;
    max-height: 480px;
    overflow-y: auto;
}

.score-badge {
    display: inline-block;
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    color: white;
    font-size: 1.4rem;
    font-weight: 700;
    padding: 0.4rem 1rem;
    border-radius: 10px;
    margin-bottom: 0.8rem;
}

.url-pill {
    display: inline-block;
    background: #1e3a5f;
    color: #7dd3fc;
    border-radius: 6px;
    padding: 0.2rem 0.6rem;
    font-size: 0.78rem;
    margin: 0.2rem 0.2rem 0.2rem 0;
    word-break: break-all;
    text-decoration: none;
}

.stTextInput > div > div > input {
    background: #1e2333 !important;
    border: 1px solid #4a5568 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
    padding: 0.5rem 0.8rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 2px rgba(124,58,237,0.25) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.4rem !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    transition: opacity 0.2s ease !important;
    width: 100%;
}
.stButton > button:hover { opacity: 0.88 !important; }

hr {
    margin: 0.75rem 0 !important;
    border-color: #2d3748 !important;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #1e2333; }
::-webkit-scrollbar-thumb { background: #4a5568; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar: API Keys & Configuration ────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    has_google = bool(os.getenv("GOOGLE_API_KEY"))
    has_tavily = bool(os.getenv("TAVILY_API_KEY"))

    st.markdown("#### API Key Status")
    st.markdown(
        f"- **Gemini API:** {'🟢 Configured' if has_google else '⚠️ Missing'}\n"
        f"- **Tavily API:** {'🟢 Configured' if has_tavily else '⚠️ Missing'}"
    )

    with st.expander("🔑 Provide Custom API Keys", expanded=(not has_google or not has_tavily)):
        st.caption("You can supply keys here for this session if not configured in environment or Streamlit secrets:")
        user_google = st.text_input(
            "Google AI Studio Key",
            type="password",
            placeholder="AIzaSy...",
            help="Free key from https://aistudio.google.com/apikey",
        )
        if user_google.strip():
            os.environ["GOOGLE_API_KEY"] = user_google.strip()

        user_tavily = st.text_input(
            "Tavily Search Key",
            type="password",
            placeholder="tvly-...",
            help="Free key from https://tavily.com",
        )
        if user_tavily.strip():
            os.environ["TAVILY_API_KEY"] = user_tavily.strip()

    st.divider()
    st.markdown("#### 🧠 Architecture")
    st.markdown("""
    - **Step 1:** 🌐 Search Agent (Tavily)
    - **Step 2:** 📄 Reader Agent (Web Scraper)
    - **Step 3:** ✍️ Writer Chain (Synthesis)
    - **Step 4:** 🧐 Critic Chain (Quality Scoring)
    """)
    st.divider()
    st.caption("Multi-Agent Research Assistant · Ready for Deployment")

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <h1>🔬 Multi-Agent Research Assistant</h1>
  <p>Powered by Gemini &nbsp;·&nbsp; Tavily Search &nbsp;·&nbsp; LangGraph</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Input ────────────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])
with col_input:
    topic = st.text_input(
        "Research Topic",
        placeholder="e.g. Impact of AI on healthcare in 2025",
        label_visibility="collapsed",
    )
with col_btn:
    run_btn = st.button("▶  Run", use_container_width=True)

st.divider()

# ── Pipeline steps metadata & work-based taglines ───────────────────────────
STEPS_META = [
    {
        "icon": "🌐",
        "title": "Search Agent",
        "pending_desc": "Standing by to search web sources via Tavily",
        "working_desc": "Searching the web for recent information using Tavily...",
        "done_desc": "Discovered key web sources & article links",
    },
    {
        "icon": "📄",
        "title": "Reader Agent",
        "pending_desc": "Standing by to scrape authoritative webpage",
        "working_desc": "Scraping deep article content from authoritative source...",
        "done_desc": "Extracted in-depth webpage insights",
    },
    {
        "icon": "✍️",
        "title": "Writer Chain",
        "pending_desc": "Standing by to synthesize findings",
        "working_desc": "Synthesizing research into structured report...",
        "done_desc": "Drafted structured report with citations",
    },
    {
        "icon": "🧐",
        "title": "Critic Chain",
        "pending_desc": "Standing by to evaluate report quality",
        "working_desc": "Evaluating structure, depth & scoring report...",
        "done_desc": "Completed critical review & scoring",
    },
]


def render_step(ph, idx: int, status: str):
    meta = STEPS_META[idx]
    if status == "working":
        badge_class = "badge-working"
        badge_text = "WORKING"
        desc = meta["working_desc"]
    elif status == "done":
        badge_class = "badge-done"
        badge_text = "DONE"
        desc = meta["done_desc"]
    else:
        badge_class = "badge-pending"
        badge_text = "WAITING"
        desc = meta["pending_desc"]

    card_class = f"step-card {status}"

    with ph:
        st.markdown(f"""
        <div class="{card_class}">
          <div class="step-header">
            <span class="step-title">{meta['icon']} Step {idx + 1}: {meta['title']}</span>
            <span class="badge {badge_class}">{badge_text}</span>
          </div>
          <div class="step-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)


# ── Run pipeline ──────────────────────────────────────────────────────────────
if run_btn:
    if not topic.strip():
        st.warning("Please enter a research topic first.")
        st.stop()

    missing_keys = []
    if not os.getenv("GOOGLE_API_KEY"):
        missing_keys.append("GOOGLE_API_KEY")
    if not os.getenv("TAVILY_API_KEY"):
        missing_keys.append("TAVILY_API_KEY")

    if missing_keys:
        st.error(f"Missing API Key(s): {', '.join(missing_keys)}. Please add them to your environment variables or Streamlit secrets.")
        st.stop()

    # 4 compact side-by-side columns to minimize vertical space above results
    cols = st.columns(4)
    step_placeholders = [cols[i].empty() for i in range(4)]
    statuses = ["pending"] * 4

    # Initial render
    for i in range(4):
        render_step(step_placeholders[i], i, statuses[i])

    async def run_pipeline():
        from multi_agent.agents import (
            build_search_agent, build_reader_agent, writer_chain, critic_chain
        )
        from multi_agent.pipeline import extract_text, extract_urls_from_messages

        # ── Step 1: Search Agent ──────────────────────────────────────────
        statuses[0] = "working"
        render_step(step_placeholders[0], 0, statuses[0])

        search_agent  = build_search_agent()
        search_result = await search_agent.ainvoke({
            "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
        })
        search_results = extract_text(search_result["messages"][-1].content)
        source_urls    = extract_urls_from_messages(search_result["messages"])

        statuses[0] = "done"
        render_step(step_placeholders[0], 0, statuses[0])

        # ── Step 2: Reader Agent ──────────────────────────────────────────
        statuses[1] = "working"
        render_step(step_placeholders[1], 1, statuses[1])

        reader_agent  = build_reader_agent()
        urls_fmt      = "\n".join(f"- {u}" for u in source_urls) if source_urls else "No URLs found."
        reader_prompt = (
            f"Topic: {topic}\n\n"
            f"Discovered Source URLs:\n{urls_fmt}\n\n"
            f"Search Summary:\n{search_results}\n\n"
            f"Task:\n"
            f"1. Select the single most relevant and authoritative webpage URL.\n"
            f"2. Invoke the `scrape_website` tool on that URL.\n"
            f"3. Summarize the detailed insights found on that page."
        )
        reader_result   = await reader_agent.ainvoke({"messages": [("user", reader_prompt)]})
        scraped_content = extract_text(reader_result["messages"][-1].content)

        scraped_url = None
        for msg in reader_result.get("messages", []):
            for tc in getattr(msg, "tool_calls", []):
                if tc.get("name") == "scrape_website":
                    args = tc.get("args", {})
                    if isinstance(args, dict) and "url" in args:
                        scraped_url = args["url"]

        statuses[1] = "done"
        render_step(step_placeholders[1], 1, statuses[1])

        # ── Step 3: Writer Chain ──────────────────────────────────────────
        statuses[2] = "working"
        render_step(step_placeholders[2], 2, statuses[2])

        sources_block     = "\n".join(f"{i+1}. {u}" for i, u in enumerate(source_urls)) if source_urls else "No URLs returned."
        research_combined = (
            f"SEARCH RESULTS:\n{search_results}\n\n"
            f"DETAILED SCRAPED CONTENT:\n{scraped_content}\n\n"
            f"SOURCE URLS (use these exactly in the Sources section):\n{sources_block}"
        )
        report = await writer_chain.ainvoke({"topic": topic, "research": research_combined})

        statuses[2] = "done"
        render_step(step_placeholders[2], 2, statuses[2])

        # ── Step 4: Critic Chain ──────────────────────────────────────────
        statuses[3] = "working"
        render_step(step_placeholders[3], 3, statuses[3])

        critic_feedback = await critic_chain.ainvoke({"report": report})

        statuses[3] = "done"
        render_step(step_placeholders[3], 3, statuses[3])

        return {
            "search_results":  search_results,
            "source_urls":     source_urls,
            "scraped_content": scraped_content,
            "scraped_url":     scraped_url,
            "report":          report,
            "critic_feedback": critic_feedback,
        }

    state = asyncio.run(run_pipeline())

    # ── Results tabs ──────────────────────────────────────────────────────────
    st.divider()
    st.markdown("## 📊 Results")

    tab1, tab2, tab3, tab4 = st.tabs(["📰 Final Report", "🧐 Critic Review", "🌐 Search Results", "📄 Scraped Content"])

    with tab1:
        st.markdown("### Final Research Report")
        st.markdown(f'<div class="report-box">{state["report"]}</div>', unsafe_allow_html=True)
        if state["source_urls"]:
            st.markdown("**Sources:**")
            pills = " ".join(f'<a href="{u}" target="_blank" class="url-pill">{u}</a>' for u in state["source_urls"])
            st.markdown(pills, unsafe_allow_html=True)

    with tab2:
        feedback = state["critic_feedback"]
        score_line = next((ln for ln in feedback.splitlines() if ln.strip().lower().startswith("score:")), None)
        if score_line:
            score_val = score_line.replace("Score:", "").replace("score:", "").strip()
            st.markdown(f'<div class="score-badge">Score: {score_val}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="report-box">{feedback}</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown("### Web Search Results")
        st.markdown(f'<div class="report-box">{state["search_results"]}</div>', unsafe_allow_html=True)
        if state["source_urls"]:
            st.markdown("**URLs found:**")
            for i, url in enumerate(state["source_urls"], 1):
                st.markdown(f"{i}. [{url}]({url})")

    with tab4:
        label = f"Scraped from: {state['scraped_url']}" if state.get("scraped_url") else "Scraped Content"
        st.markdown(f"### {label}")
        st.markdown(f'<div class="report-box">{state["scraped_content"]}</div>', unsafe_allow_html=True)

# ── Idle state ────────────────────────────────────────────────────────────────
else:
    cols = st.columns(4)
    for i in range(4):
        render_step(cols[i].empty(), i, "pending")

    st.markdown("""
    <div style="text-align:center;padding:1.5rem 0;color:#64748b;font-size:0.9rem;">
      Enter a research topic above and click <strong style="color:#a78bfa;">▶ Run</strong> to start the pipeline.
    </div>
    """, unsafe_allow_html=True)
