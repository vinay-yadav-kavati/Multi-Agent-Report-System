import asyncio
import sys
import io
from rich.console import Console
from rich.panel import Panel
from multi_agent.pipeline import run_research_pipeline

# Force UTF-8 on Windows to prevent cp1252 UnicodeEncodeErrors
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

console = Console(highlight=False, force_terminal=True)

# Entry point
def main() -> None:
    console.print()
    console.print(Panel(
        "[bold cyan]Welcome to the[/bold cyan] [bold magenta]Multi-Agent Research Assistant[/bold magenta]\n"
        "[dim]Powered by Gemini + Tavily | LangGraph pipeline[/dim]",
        border_style="bright_blue",
        padding=(1, 4),
    ))
    console.print()
    topic = console.input("[bold yellow]>> Enter the topic you want to research:[/bold yellow] ")
    asyncio.run(run_research_pipeline(topic))
