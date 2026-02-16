"""
Gradio frontend for the Deep Research Agent.
Enter a stock ticker (e.g. NVDA) or a free-text query to get a structured research report.
Run with: python app.py
"""

import traceback

import gradio as gr

from agent import run_research_sync
from models import ResearchReport


def report_to_markdown(report: ResearchReport) -> str:
    """Format ResearchReport as Markdown in fixed order: exec summary, takeaways, strategic overview, SWOT, implications, sources, financials, drivers, valuation, regulatory, risks, what to watch, additional detail."""
    parts = []

    parts.append("## Executive summary\n\n")
    parts.append(report.executive_summary)
    parts.append("\n\n---\n\n")

    parts.append("## Key takeaways\n\n")
    parts.append(report.key_takeaways)
    parts.append("\n\n---\n\n")

    parts.append("## Strategic overview\n\n")
    parts.append(report.strategic_overview)
    parts.append("\n\n---\n\n")

    parts.append("## SWOT\n\n")
    parts.append("**Strengths**\n\n")
    parts.append(report.swot.strengths)
    parts.append("\n\n**Weaknesses**\n\n")
    parts.append(report.swot.weaknesses)
    parts.append("\n\n**Opportunities**\n\n")
    parts.append(report.swot.opportunities)
    parts.append("\n\n**Threats**\n\n")
    parts.append(report.swot.threats)
    parts.append("\n\n---\n\n")

    parts.append("## Implications and strategic priorities\n\n")
    parts.append(report.implications_and_strategic_priorities)
    parts.append("\n\n---\n\n")

    parts.append("## Sources\n\n")
    if report.sources:
        for s in report.sources:
            parts.append(f"- [{s.source_title}]({s.url})\n")
    else:
        parts.append("(No sources listed.)\n")
    parts.append("\n---\n\n")

    parts.append("## Financial performance\n\n")
    parts.append(report.financial_performance)
    parts.append("\n\n---\n\n")

    parts.append("## Drivers and sensitivities\n\n")
    parts.append(report.drivers_and_sensitivities)
    parts.append("\n\n---\n\n")

    parts.append("## Valuation context and modeling tips\n\n")
    parts.append(report.valuation_context_and_modeling_tips)
    parts.append("\n\n---\n\n")

    parts.append("## Regulatory and legal environment\n\n")
    parts.append(report.regulatory_and_legal)
    parts.append("\n\n---\n\n")

    parts.append("## Risks and uncertainties\n\n")
    parts.append(report.risks_and_uncertainties)
    parts.append("\n\n---\n\n")

    parts.append("## What to watch next\n\n")
    for item in report.what_to_watch_next:
        parts.append(f"- {item}\n")
    if not report.what_to_watch_next:
        parts.append("(None listed.)\n")
    parts.append("\n---\n\n")

    if report.additional_detail:
        parts.append("## More detail\n\n")
        parts.append(report.additional_detail)
        parts.append("\n")

    return "".join(parts)


def research(message: str) -> str:
    """Run deep research and return Markdown report or error message."""
    if not message or not message.strip():
        return "Please enter a stock ticker (e.g. NVDA) or a free-text query."
    try:
        report = run_research_sync(message.strip())
        return report_to_markdown(report)
    except Exception as e:
        return (
            f"**Error:** {e}\n\n"
            f"<details><summary>Traceback</summary>\n\n```\n{traceback.format_exc()}\n```\n</details>"
        )


def main():
    # So you see output in the terminal when running: python app.py
    import sys
    sys.stderr.write(
        "\n  >>> Deep Research Agent started. Submit a query in the browser and watch THIS terminal for [agent] progress.\n\n"
    )
    sys.stderr.flush()

    interface = gr.Interface(
        fn=research,
        inputs=gr.Textbox(
            label="Ticker or query",
            placeholder="e.g. NVDA or 'impact of AI on semiconductor demand'",
            lines=1,
        ),
        outputs=gr.Markdown(label="Research report"),
        title="Deep Research Agent",
        description=(
            "Enter a **stock ticker** (e.g. NVDA, AAPL) or a **free-text query**. "
            "The agent runs multi-step web research via DuckDuckGo and returns a structured report. "
            "Watch the **terminal** for progress (discovery, angles, parallel searches, synthesis)."
        ),
        examples=[["NVDA"], ["AAPL"], ["renewable energy growth 2025"]],
    )
    interface.launch()


if __name__ == "__main__":
    main()
