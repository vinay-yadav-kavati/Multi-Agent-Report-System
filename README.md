# 🔬 Multi-Agent Research Assistant

An AI-powered research assistant built with **LangGraph**, **Google Gemini**, **Tavily Web Search**, and **Streamlit**. It coordinates a multi-agent workflow to search the web, scrape deep article content, synthesize structured reports with citations, and critically evaluate the final output.

---

## 🏛️ Architecture & Agent Workflow

```
[ Research Topic ]
       │
       ▼
1. 🌐 Search Agent (Tavily + Gemini)
   └── Discovers top authoritative sources & URLs
       │
       ▼
2. 📄 Reader Agent (Web Scraper + Gemini)
   └── Inspects & extracts deep page content
       │
       ▼
3. ✍️ Writer Chain (Structured Synthesis)
   └── Drafts comprehensive report with verbatim source links
       │
       ▼
4. 🧐 Critic Chain (Quality Review)
   └── Evaluates report depth, structure & assigns an objective score
```

---

## 🚀 Deployment Guide

### Option 1: Streamlit Community Cloud (Recommended)

1. **Fork or Push** this repository to your GitHub account:
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **"New app"**.
3. Select your repository, branch (`main`), and set the main file path to:
   ```
   app.py
   ```
4. Click **"Advanced settings..."** and configure your **Secrets**:
   ```toml
   GOOGLE_API_KEY = "your-google-api-key"
   TAVILY_API_KEY = "your-tavily-api-key"
   ```
5. Click **"Deploy!"** 🎉

---

### Option 2: Docker Container (Render, Hugging Face Spaces, AWS, GCP)

1. **Build the Docker container:**
   ```bash
   docker build -t multi-agent-researcher .
   ```
2. **Run container with environment variables:**
   ```bash
   docker run -p 8501:8501 \
     -e GOOGLE_API_KEY="your-google-api-key" \
     -e TAVILY_API_KEY="your-tavily-api-key" \
     multi-agent-researcher
   ```
3. Open `http://localhost:8501` in your browser.

---

## 💻 Local Development Setup

### 1. Clone repository & install dependencies

Using **uv** (ultra-fast):
```bash
uv venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS / Linux
uv pip install -r requirements.txt
```

Or using standard **pip**:
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:
```env
GOOGLE_API_KEY="your-google-api-key"
TAVILY_API_KEY="your-tavily-api-key"
```
*(You can get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey) and a free Tavily Search key from [Tavily](https://tavily.com/).)*

### 3. Run the Streamlit Application

```bash
uv run streamlit run app.py
# or
streamlit run app.py
```

### 4. Run CLI Interface (Optional)

```bash
uv run multi-agent
# or
python -m multi_agent
```

---

## 📁 Project Structure

```
├── .streamlit/
│   ├── config.toml           # Streamlit server & theme config
│   └── secrets.toml.example  # Secrets reference template
├── src/
│   └── multi_agent/
│       ├── __init__.py       # CLI entry point
│       ├── agents.py         # Search agent, Reader agent, Writer & Critic chains
│       ├── pipeline.py       # Async pipeline orchestrator
│       └── tools.py          # Tavily search & web scraping tools
├── app.py                    # Streamlit web UI
├── Dockerfile                # Production container spec
├── pyproject.toml            # Project metadata & dependencies
├── requirements.txt          # Python dependencies
└── README.md
```
