from langchain.tools import tool
from tavily import AsyncTavilyClient
import os
import socket
import requests
import asyncio
import time
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from rich import print

load_dotenv()

def configure_network():
    """Automatically switches between Hostel Proxy and Mobile Hotspot.
    Uses a very short timeout so it never blocks startup.
    """
    proxy_host = "studentnet.rgukt.ac.in"
    proxy_port = 3128
    try:
        # 0.3s timeout — fast enough to not slow startup
        with socket.create_connection((proxy_host, proxy_port), timeout=0.3):
            print("[cyan]Network: Hostel Proxy reachable. Using proxy...[/cyan]")
    except Exception:
        # If proxy is unreachable (Mobile Hotspot), remove proxy env vars
        for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
            os.environ.pop(key, None)
        print("[cyan]Network: Mobile Hotspot detected. Using direct connection...[/cyan]")

configure_network()

def get_tavily_client() -> AsyncTavilyClient:
    return AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
async def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic.
    Returns Titles, URLs and content snippets. Always include full URLs in output.
    """
    client = get_tavily_client()
    results = await client.search(query=query, max_results=5)
    out = []

    for r in results['results']:
        out.append(f"Title: {r['title']}")
        out.append(f"URL: {r['url']}")
        out.append(f"Snippet: {r['content'][:400]}")
        out.append("---")
    return "\n".join(out)

@tool
async def scrape_website(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }
        )
        if resp.status_code >= 400:
            return f"Failed to scrape {url} (HTTP {resp.status_code})"
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        if not text:
            return f"No readable text found at {url}"
        return text[:3000]
    except Exception as e:
        return f"Error scraping website: {str(e)}"


# --- Test block (run this file directly to test tools) ---
async def main():
    start = time.perf_counter()
    result = await web_search.ainvoke("How covid pandemic affected India?")
    elapsed = time.perf_counter() - start
    print(result)
    print(f"\n[bold green]Response time: {elapsed:.2f}s[/bold green]")

if __name__ == "__main__":
    asyncio.run(main())