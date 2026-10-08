from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .tools import web_search, scrape_website
import os
import warnings
from dotenv import load_dotenv

load_dotenv()

# Suppress AFC warning — we are aware it's used via create_agent
warnings.filterwarnings(
    "ignore",
    message=".*Direct use of automatic function calling.*"
)

#model setup
def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-flash-lite-latest",
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.2,
    )

#first agent — web search
def build_search_agent():
    return create_agent(
        model=get_llm(),
        tools=[web_search],
        system_prompt=(
            "You are an expert web research agent. Use the `web_search` tool to gather reliable, detailed, and factual information. "
            "In your final response, provide a thorough summary of the findings and make sure to mention the source URLs discovered."
        ),
    )

#second agent — website reader/scraper
def build_reader_agent():
    return create_agent(
        model=get_llm(),
        tools=[scrape_website],
        system_prompt=(
            "You are a website research and reading agent. You will be provided with a research topic, a list of available URLs, and a search summary. "
            "Select the most authoritative and informative article URL from the list, call the `scrape_website` tool on it to read its content, "
            "and provide a detailed summary of the key findings, data, and context extracted from that page."
        ),
    )

#writer chain
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report with these exact sections:
- Introduction
- Key Findings (minimum 3 well-explained points with data/stats if available)
- Conclusion
- Sources

IMPORTANT for Sources section:
Extract every URL that appears in the Research Gathered section above and list them as numbered bullet points.
If a URL starts with 'http', include it exactly as-is.
Do not write generic descriptions — list the actual URLs.

Be detailed, factual and professional."""),
])

class _LazyChain:
    """Invokes chains dynamically with the current LLM instance so API keys
    configured at runtime or via Streamlit secrets are immediately used.
    """
    def __init__(self, prompt):
        self.prompt = prompt

    def _get_chain(self):
        return self.prompt | get_llm() | StrOutputParser()

    async def ainvoke(self, *args, **kwargs):
        return await self._get_chain().ainvoke(*args, **kwargs)

    def invoke(self, *args, **kwargs):
        return self._get_chain().invoke(*args, **kwargs)

writer_chain = _LazyChain(writer_prompt)

#critic chain
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = _LazyChain(critic_prompt)