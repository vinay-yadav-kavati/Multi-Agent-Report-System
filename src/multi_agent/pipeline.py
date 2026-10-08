import asyncio
import sys
import io
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich import print as rprint
from .agents import build_reader_agent, build_search_agent, writer_chain, critic_chain

# Force UTF-8 on Windows so rich never falls back to the legacy cp1252 renderer.
# Without this, any non-ASCII char in LLM output (₹, ·, —, etc.) crashes the terminal.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

console = Console(highlight=False, force_terminal=True)

def extract_text(content) -> str:
    """Safely extract plain text from an agent message's .content field.
    
    Gemini sometimes returns a list of content blocks like:
      [{'type': 'text', 'text': '...', 'extras': {...}}]
    instead of a plain string. This handles both cases.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(content)

def extract_urls_from_messages(messages: list) -> list[str]:
    """Scan agent messages for ToolMessage content and extract all URLs.

    When the search_agent calls web_search(), LangGraph stores the raw
    tool output as a ToolMessage in the messages list. That raw output
    has lines like 'URL: https://...'. We grab them here before the
    agent's final summarised response drops them.
    """
    urls = []
    for msg in messages:
        # ToolMessage has a 'type' or class name of 'tool'
        msg_type = getattr(msg, "type", "") or type(msg).__name__.lower()
        if "tool" in msg_type:
            raw = extract_text(getattr(msg, "content", ""))
            for line in raw.splitlines():
                line = line.strip()
                if line.lower().startswith("url:"):
                    url = line[4:].strip()
                    if url and url not in urls:
                        urls.append(url)
    return urls

def section(title: str, color: str = "bold cyan"):
    console.print()
    console.print(Rule(f"[{color}]{title}[/{color}]", style=color))
    console.print()

def step_banner(step: int, label: str):
    text = Text()
    text.append(f"  Step {step}  ", style="bold white on blue")
    text.append(f"  {label}", style="bold cyan")
    console.print(text)
    console.print()

async def run_research_pipeline(topic: str) -> dict:
    state = {}

    console.print()
    console.print(Panel(
        f"[bold yellow]Research Topic:[/bold yellow]\n[white]{topic}[/white]",
        title="[bold magenta]>> Multi-Agent Research Pipeline[/bold magenta]",
        border_style="magenta",
        padding=(1, 4),
    ))
    console.print()

    # ── Step 1: Search Agent ──────────────────────────────────────────────────
    step_banner(1, "Search Agent is gathering information...")

    search_agent = build_search_agent()
    search_result = await search_agent.ainvoke({
        "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
    })
    state["search_results"] = extract_text(search_result["messages"][-1].content)

    # Extract raw URLs from tool call messages before the agent summarises them away
    state["source_urls"] = extract_urls_from_messages(search_result["messages"])

    console.print(Panel(
        state["search_results"],
        title="[bold green][ Search Results ][/bold green]",
        border_style="green",
        padding=(1, 2),
    ))

    if state["source_urls"]:
        url_list = "\n".join(f"  {i+1}. {u}" for i, u in enumerate(state["source_urls"]))
        console.print(Panel(
            url_list,
            title="[bold cyan][ Source URLs Found ][/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        ))
    else:
        console.print("[yellow]  No URLs captured from tool messages.[/yellow]")

    # ── Step 2: Reader Agent ──────────────────────────────────────────────────
    step_banner(2, "Reader Agent is scraping top resources...")

    reader_agent = build_reader_agent()

    # Pass explicit list of discovered URLs so reader_agent knows exactly what is available to scrape
    if state["source_urls"]:
        urls_formatted = "\n".join(f"- {u}" for u in state["source_urls"])
    else:
        urls_formatted = "No URLs were found in search."

    reader_prompt = (
        f"Topic: {topic}\n\n"
        f"Discovered Source URLs:\n{urls_formatted}\n\n"
        f"Search Summary:\n{state['search_results']}\n\n"
        f"Task:\n"
        f"1. Select the single most relevant and authoritative webpage URL from the 'Discovered Source URLs' list above.\n"
        f"2. Invoke the `scrape_website` tool on that chosen URL to read its full text.\n"
        f"3. Summarize the detailed insights, data, and context found on that page."
    )

    reader_result = await reader_agent.ainvoke({
        "messages": [("user", reader_prompt)]
    })

    state["scraped_content"] = extract_text(reader_result["messages"][-1].content)

    # Detect which URL was scraped from the tool calls (if any)
    scraped_url = None
    for msg in reader_result.get("messages", []):
        for tc in getattr(msg, "tool_calls", []):
            if tc.get("name") == "scrape_website":
                args = tc.get("args", {})
                if isinstance(args, dict) and "url" in args:
                    scraped_url = args["url"]
                    break

    panel_title = f"[bold green][ Scraped Content: {scraped_url} ][/bold green]" if scraped_url else "[bold green][ Scraped Content ][/bold green]"
    console.print(Panel(
        state["scraped_content"],
        title=panel_title,
        border_style="green",
        padding=(1, 2),
    ))

    # ── Step 3: Writer Chain ──────────────────────────────────────────────────
    step_banner(3, "Writer is drafting the report...")

    # Build sources block from raw URLs captured directly from tool messages
    if state["source_urls"]:
        sources_block = "\n".join(f"{i+1}. {u}" for i, u in enumerate(state["source_urls"]))
    else:
        sources_block = "No URLs were returned by the search tool."

    research_combined = (
        f"SEARCH RESULTS:\n{state['search_results']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}\n\n"
        f"SOURCE URLS (use these exactly in the Sources section):\n{sources_block}"
    )

    writer_result = await writer_chain.ainvoke({
        "topic": topic,
        "research": research_combined
    })
    state["report"] = writer_result

    console.print(Panel(
        state["report"],
        title="[bold magenta][ Final Report ][/bold magenta]",
        border_style="magenta",
        padding=(1, 2),
    ))

    # ── Step 4: Critic Chain ──────────────────────────────────────────────────
    step_banner(4, "Critic is reviewing the report...")

    critic_result = await critic_chain.ainvoke({
        "report": state["report"]
    })
    state["critic_feedback"] = critic_result

    console.print(Panel(
        state["critic_feedback"],
        title="[bold yellow][ Critic Feedback ][/bold yellow]",
        border_style="yellow",
        padding=(1, 2),
    ))

    console.print()
    console.print(Panel(
        "[bold green]>> Pipeline complete![/bold green]",
        border_style="green",
        padding=(0, 2),
    ))
    console.print()

    return state


# Used to test the pipeline individually. Not the entry point.
if __name__ == "__main__":
    topic = input("Enter the topic you want to research on: ")
    asyncio.run(run_research_pipeline(topic))