# Pydantic-AI-Deep-Research-Agent1

A **deep research agent** built with **Pydantic AI** and **OpenAI gpt-5-mini**, with a **Gradio** UI. It accepts either a **stock ticker** (e.g. NVDA) or a **free-text query**, runs multi-step web research using **DuckDuckGo**, and returns a structured report: executive summary, key findings per section with citations (url + source title), risks/uncertainties, and "what to watch next."

## Easy setup

### 1. Create a virtual environment (recommended)

```bash
python -m venv .venv
```

- **Windows (PowerShell):**  
  `& .\.venv\Scripts\Activate.ps1`  
  If you get "running scripts is disabled", either:
  - **Option A:** Use CMD and run `.venv\Scripts\activate.bat`, or
  - **Option B:** In PowerShell run:  
    `Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process`  
    then run `& .\.venv\Scripts\Activate.ps1` again (Bypass lasts only for that session).
- **Windows (CMD):**  
  `.venv\Scripts\activate.bat`
- **macOS/Linux:**  
  `source .venv/bin/activate`

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your OpenAI API key

1. Copy the example env file:
   ```bash
   copy .env.example .env
   ```
   (On macOS/Linux use `cp .env.example .env`.)

2. Open `.env` and set your key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```
   Get a key from [OpenAI API keys](https://platform.openai.com/api-keys).

### 4. Run the app

```bash
python app.py
```

Open the URL shown in the terminal (e.g. `http://127.0.0.1:7860`) in your browser. Enter a ticker (e.g. **NVDA**) or a free-text query to get a structured research report.

**See the agent working in the terminal:** When you submit a query in the browser, progress lines like `[agent] Running discovery search...` appear in the **same terminal** where you ran `python app.py`. If you don’t see them, run the pipeline from the CLI instead:

```bash
python agent.py NVDA
```

(or `python agent.py "your query"`). All `[agent]` progress is printed to the terminal; the report summary is printed at the end.

---

## How it works

1. **Input:** You enter a stock ticker (e.g. NVDA) or a free-text query.
2. **Ticker vs query:** The app detects tickers (2–5 uppercase letters) and resolves them to company name and context (e.g. "NVIDIA, semiconductors, GPUs, AI").
3. **Discovery:** One DuckDuckGo search is run for the resolved query.
4. **Angles:** The LLM produces 3–4 non-overlapping search angles from the discovery results (e.g. for a stock: SWOT, performance, competition, quarterly results).
5. **Parallel deep dives:** A separate DuckDuckGo search is run for each angle (in parallel).
6. **Report:** The LLM synthesizes a structured report from all results: executive summary, sections with key findings and cited evidence (url + source title), risks/uncertainties, and what to watch next. Primary sources are preferred for financials; evidence items include citations.

All web search is done via **DuckDuckGo** (using the `ddgs` package).

---

## Project layout

| File               | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| `agent.py`         | Pipeline: ticker resolution, discovery, angle agent, parallel searches, report agent; `run_research_sync()` entrypoint. Run `python agent.py NVDA` to see [agent] progress in the terminal. |
| `models.py`        | Pydantic models: `ResolvedQuery`, `SearchAngles`, `Evidence`, `Source`, `SWOT`, `ResearchReport` |
| `app.py`           | Gradio UI: single text input (ticker or query), Markdown report output  |
| `requirements.txt` | Python dependencies (pydantic-ai, gradio, python-dotenv, ddgs)          |
| `.env`             | Your API key (not committed to git)                                     |
| `.env.example`     | Template for `.env`                                                     |
| `doc.md`           | Pydantic AI docs (reference)                                             |

## Optional

- **Different model:** In `.env` set e.g. `MODEL=openai:gpt-4o-mini` (or another OpenAI model id).
- **Instructions:** Edit the `instructions` on the resolve, angle, or report agents in `agent.py`.

## Troubleshooting

- **"API key must be provided"** — Make sure `.env` exists and contains `OPENAI_API_KEY=sk-...`.
- **Model not found** — If `gpt-5-mini` is not available in your region, set `MODEL=openai:gpt-4o-mini` in `.env`.
- **Discovery/search returned no results** — DuckDuckGo may be rate-limiting or the query may need rephrasing; try again or use a different query.
