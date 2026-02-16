"""
Pydantic models for the deep research agent pipeline.
Used as structured outputs for ticker resolution, search angles, and final report.
"""

from pydantic import BaseModel, Field


class ResolvedQuery(BaseModel):
    """Result of resolving a ticker or free-text query for discovery."""

    is_ticker: bool = Field(description="True if the input was a stock ticker symbol.")
    company_context: str | None = Field(
        default=None,
        description="For a ticker: company name and brief context (e.g. 'NVIDIA, semiconductors, GPUs, AI'). None for free-text.",
    )
    resolved_query: str = Field(
        description="Query string to use for discovery search (company context + topic for ticker, or original query for free-text)."
    )


class SearchAngles(BaseModel):
    """3-4 non-overlapping search angles (keywords/phrases) for deep-dive searches."""

    angles: list[str] = Field(
        description="Exactly 3 to 4 distinct search angles. For stocks: e.g. SWOT analysis, last 12 months stock performance, competition and market positioning, latest quarterly results and forward guidance.",
        min_length=3,
        max_length=4,
    )


class Evidence(BaseModel):
    """One evidence bullet with citation (url + source title)."""

    bullet: str = Field(description="Short evidence sentence.")
    url: str = Field(description="URL of the source.")
    source_title: str = Field(description="Title of the source (e.g. article or page title).")


class Source(BaseModel):
    """A cited source (url + title) for the Sources section."""

    source_title: str = Field(description="Title of the source.")
    url: str = Field(description="URL of the source.")


class SWOT(BaseModel):
    """SWOT: Strengths, Weaknesses, Opportunities, Threats."""

    strengths: str = Field(description="Strengths (concise; bullets or short paragraph).")
    weaknesses: str = Field(description="Weaknesses (concise; bullets or short paragraph).")
    opportunities: str = Field(description="Opportunities (concise; bullets or short paragraph).")
    threats: str = Field(description="Threats (concise; bullets or short paragraph).")


class ResearchReport(BaseModel):
    """Structured deep research report with fixed sections: exec summary, takeaways, strategic overview, SWOT, implications, sources, financials, drivers, valuation, regulatory, risks, what to watch, additional detail."""

    executive_summary: str = Field(
        description="Concise executive summary (2-4 sentences)."
    )
    key_takeaways: str = Field(
        description="Key takeaways (bullet points or short numbered list as a single string)."
    )
    strategic_overview: str = Field(
        description="Strategic overview: market position, strategy, competitive context (concise)."
    )
    swot: SWOT = Field(
        description="SWOT analysis: strengths, weaknesses, opportunities, threats (each concise)."
    )
    implications_and_strategic_priorities: str = Field(
        description="Implications and strategic priorities (summary, concise)."
    )
    sources: list[Source] = Field(
        default_factory=list,
        description="List of cited sources (title + url). Use exact URLs from the provided search results.",
    )
    financial_performance: str = Field(
        description="Financial performance (concise): key metrics, recent results, trends."
    )
    drivers_and_sensitivities: str = Field(
        description="Key drivers and sensitivities (revenue/earnings drivers, key assumptions, sensitivities)."
    )
    valuation_context_and_modeling_tips: str = Field(
        description="Valuation context and modeling tips (multiples, key inputs, modeling notes)."
    )
    regulatory_and_legal: str = Field(
        description="Regulatory and legal environment (relevant regulations, litigation, compliance)."
    )
    risks_and_uncertainties: str = Field(
        description="Risks and uncertainties; include conflicting information where relevant."
    )
    what_to_watch_next: list[str] = Field(
        description="Concrete follow-ups: next earnings, key metrics, regulatory dates, etc.",
        default_factory=list,
    )
    additional_detail: str = Field(
        default="",
        description="More detailed and concise information: extra context, nuances, or supporting detail.",
    )
