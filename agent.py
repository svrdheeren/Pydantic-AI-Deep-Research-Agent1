"""
Deep research agent: Python-orchestrated pipeline using Pydantic AI and DuckDuckGo.
Input: ticker (e.g. NVDA) or free-text query.
Output: structured ResearchReport (exec summary, sections with citations, risks, what to watch).
"""

import asyncio
import os
import re
import sys
from typing import Any

from dotenv import load_dotenv
from ddgs import DDGS
from pydantic_ai import Agent

from models import (
    ResolvedQuery,
    ResearchReport,
    SearchAngles,
)

load_dotenv()

MODEL = os.getenv("MODEL", "openai:gpt-5-mini")

# Heuristic: 2-5 uppercase letters = ticker
TICKER_PATTERN = re.compile(r"^[A-Z]{2,5}$")


def _is_ticker(input_str: str) -> bool:
    stripped = input_str.strip().upper()
    return bool(TICKER_PATTERN.match(stripped))


def _ddgs_text(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Sync DuckDuckGo text search. Run from thread for parallel calls."""
    return DDGS().text(query, max_results=max_results)


# --- Ticker resolution agent ---
resolve_agent = Agent(
    MODEL,
    output_type=ResolvedQuery,
    instructions=(
        "You resolve user input into a query for web search. "
        "If the input is a stock ticker (e.g. NVDA, AAPL), set is_ticker=True, "
        "provide company_context with company name and brief context (e.g. 'NVIDIA, semiconductors, GPUs, AI'), "
        "and resolved_query as a short search phrase combining company and context. "
        "If the input is a general question or topic, set is_ticker=False, company_context=None, "
        "and resolved_query to the user's query as-is (cleaned up if needed)."
    ),
)

# --- Angle-generation agent ---
angle_agent = Agent(
    MODEL,
    output_type=SearchAngles,
    instructions=(
        "From the discovery search results below, produce exactly 3 to 4 non-overlapping search angles (keywords or short phrases). "
        "For a stock/company: include angles such as: SWOT analysis, last 12 months stock performance, "
        "competition and market positioning, latest quarterly results and forward guidance. "
        "For a general topic: derive analogous angles that cover different aspects. "
        "Output only the structured list of angles; no other text."
    ),
)

# --- Report-synthesis agent ---
report_agent = Agent(
    MODEL,
    output_type=ResearchReport,
    instructions=(
        "You are a research analyst. Using ONLY the provided search results (no external knowledge), "
        "produce a structured research report with these sections. Be concise and detailed where it adds value. "
        "Fill every field. "
        "executive_summary: 2-4 sentences. "
        "key_takeaways: bullet or numbered list as one string. "
        "strategic_overview: market position, strategy, competition (concise). "
        "swot: strengths, weaknesses, opportunities, threats (each a short paragraph or bullets as one string). "
        "implications_and_strategic_priorities: summary of implications and priorities. "
        "sources: list of ALL cited sources from the search results with exact url and source_title (title of page/article). "
        "financial_performance: concise key metrics, recent results, trends. "
        "drivers_and_sensitivities: key drivers and sensitivities. "
        "valuation_context_and_modeling_tips: multiples, key inputs, modeling tips. "
        "regulatory_and_legal: relevant regulations, litigation, compliance. "
        "risks_and_uncertainties: risks and conflicting info. "
        "what_to_watch_next: concrete list (earnings dates, metrics, regulatory events). "
        "additional_detail: any extra detail or nuance. "
        "Prefer primary sources for financials (earnings, SEC filings, investor relations). Use exact URLs from the provided results for sources."
    ),
)


def _format_discovery_for_angles(discovery_results: list[dict[str, Any]]) -> str:
    lines = []
    for i, r in enumerate(discovery_results[:15], 1):
        title = r.get("title", "")
        href = r.get("href", "")
        body = r.get("body", "")
        lines.append(f"{i}. {title}\n   URL: {href}\n   {body}")
    return "\n\n".join(lines)


def _format_all_for_report(
    resolved_query: str,
    discovery_results: list[dict[str, Any]],
    angle_to_results: list[tuple[str, list[dict[str, Any]]]],
) -> str:
    parts = [
        f"Resolved query: {resolved_query}",
        "\n--- Discovery search results ---",
        _format_discovery_for_angles(discovery_results),
    ]
    for angle, results in angle_to_results:
        parts.append(f"\n--- Deep-dive angle: {angle} ---")
        for i, r in enumerate(results[:8], 1):
            title = r.get("title", "")
            href = r.get("href", "")
            body = r.get("body", "")
            parts.append(f"{i}. {title}\n   URL: {href}\n   {body}")
    return "\n".join(parts)


def _log(msg: str) -> None:
    """Print progress to terminal (stderr, unbuffered) so user sees the agent working."""
    sys.stderr.write(f"  [agent] {msg}\n")
    sys.stderr.flush()


async def run_research_async(query: str) -> ResearchReport:
    """Run the full pipeline: normalize -> discovery -> angles -> parallel searches -> report."""
    raw = query.strip()
    if not raw:
        raise ValueError("Query cannot be empty.")

    _log(f"Input: {raw!r}")

    # 1) Normalize: detect ticker and optionally resolve
    if _is_ticker(raw):
        _log("Detected ticker. Resolving to company and context...")
        resolve_result = await resolve_agent.run(
            f"Resolve this stock ticker for web search: {raw}"
        )
        resolved = resolve_result.output
        if not resolved:
            raise ValueError(f"Failed to resolve ticker: {raw}")
        resolved_query = resolved.resolved_query
        _log(f"Resolved: {resolved_query}")
    else:
        resolved_query = raw
        _log("Treating input as free-text query.")

    # 2) Discovery search
    _log("Running discovery search (DuckDuckGo)...")
    discovery_results = await asyncio.to_thread(
        _ddgs_text, resolved_query, 10
    )
    _log(f"Discovery: {len(discovery_results)} results.")

    if not discovery_results:
        raise ValueError("Discovery search returned no results.")

    # 3) Angle-generation agent
    _log("Generating 3-4 search angles...")
    discovery_text = _format_discovery_for_angles(discovery_results)
    angle_prompt = (
        f"Discovery search results for: {resolved_query}\n\n{discovery_text}\n\n"
        "Produce 3-4 non-overlapping search angles (keywords/phrases) for deep-dive searches."
    )
    angle_result = await angle_agent.run(angle_prompt)
    angles_out = angle_result.output
    if not angles_out or not angles_out.angles:
        raise ValueError("Angle agent produced no angles.")
    _log(f"Angles: {angles_out.angles}")

    # 4) Parallel deep-dive searches
    n = len(angles_out.angles)
    _log(f"Running {n} parallel deep-dive searches (DuckDuckGo)...")

    async def search_one(angle: str) -> tuple[str, list[dict[str, Any]]]:
        results = await asyncio.to_thread(_ddgs_text, angle, 10)
        return (angle, results)

    angle_to_results = await asyncio.gather(
        *[search_one(a) for a in angles_out.angles]
    )
    _log("Deep-dive searches done.")

    # 5) Report-synthesis agent
    _log("Synthesizing structured report...")
    report_context = _format_all_for_report(
        resolved_query, discovery_results, angle_to_results
    )
    report_prompt = (
        f"Produce a structured research report from the following search results.\n\n"
        f"{report_context}"
    )
    report_result = await report_agent.run(report_prompt)
    report = report_result.output
    if not report:
        raise ValueError("Report agent produced no output.")

    _log("Report ready.")
    return report


def run_research_sync(query: str) -> ResearchReport:
    """Synchronous entrypoint for Gradio: runs async pipeline via asyncio.run."""
    return asyncio.run(run_research_async(query))


if __name__ == "__main__":
    # Run from terminal to see [agent] progress:  python agent.py NVDA
    import sys
    query = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else "NVDA"
    if not query:
        sys.stderr.write("Usage: python agent.py <ticker or query>\n")
        sys.exit(1)
    sys.stderr.write(f"Running research for: {query!r}\n\n")
    sys.stderr.flush()
    report = run_research_sync(query)
    # Print report snippet to terminal
    sys.stdout.write("\n--- REPORT ---\n")
    sys.stdout.write(report.executive_summary + "\n")
    sys.stdout.write("\nKey takeaways:\n" + report.key_takeaways + "\n")
    sys.stdout.write("\n[REST IN UI OR FORMAT WITH report_to_markdown]\n")
