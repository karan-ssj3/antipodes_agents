# Antipodes Agents – Detailed Overview & Roadmap

This document expands on the README with deeper architecture details, current feature set, and upcoming enhancements.

## 1) System Orchestration

- Workflow: `src/workflow.py` built on LangGraph
  - Nodes: `data_loader → valuation_agent → sentiment_agent → fundamental_agent → debate_coordinator → coordinator → backtester → output_generator`
  - Deterministic execution with a shared typed state (`AgentWorkflowState`)
  - Errors are captured into `state["errors"]` without crashing downstream steps

## 2) Agents & Coordinator Logic

- Valuation Agent: risk-adjusted momentum (20d return / 60d vol), percentile-normalized
- Sentiment Agent: VADER with 0.9^days recency decay over curated headlines
- Fundamental Agent: composite quality across growth, profitability, leverage, efficiency
- Coordinator: weighted voting over agent ratings with thresholds, converts to BUY/HOLD/SELL
- Debate Coordinator: single, conservative moderation round when an agent is isolated

## 3) Backtesting & Outputs

- Backtest Engine: 90-day forward window from `as_of_date`, equal-weight BUYs, equal-weight benchmark
- Metrics: portfolio, benchmark, active return, simple Sharpe proxy
- Outputs:
  - `outputs/picks.csv` – per-ticker ratings and final decision
  - `outputs/performance.csv` – key metrics
  - `outputs/chart.png` – portfolio vs benchmark bars
  - `outputs/attribution.csv` – per-ticker forward returns and contributions

## 4) Streamlit UI

- `streamlit_app.py` provides:
  - Sidebar controls for date, tickers, weights, forward window
  - Run button to execute the full pipeline and render results
  - LLM Performance Report (markdown) when `OPENAI_API_KEY` is present
  - LLM Optimizer to propose JSON param changes; apply to runtime config
  - Rolling A/B experiments over recent months; CSV export and variant promotion
  - Config versioning: save promoted configs and rollback from sidebar

## 5) LLM Integrations

- Reporter (`src/llm/reporting.py`): grounded attribution report saved to `performance_report.md`
- Optimizer (`src/llm/optimizer.py`):
  - Requests JSON-only output (with response_format), strips code fences if present
  - Returns `{ reasoning, changes }` for safe, bounded parameter adjustments

## 6) Experiments

- Rolling A/B Runner (`src/experiments/ab_runner.py`): compares Baseline vs Variant over multiple dates
- Config Store (`src/experiments/store.py`): persists promoted configs to `outputs/experiments/configs/`

## 7) Data Integrity & Leakage Prevention

- Strict `as_of_date` filtering for prices and news
- Backtest uses forward prices not seen by agents
- Pydantic models enforce schema constraints throughout

## 8) Roadmap (Enhancements)

- Factor-style attribution: quantify portfolio tilts and drivers
- Sensitivity surfaces: visualize stability of returns around param neighborhoods
- More agents: earnings revisions, macro regime, technical patterns
- RAG-based fundamentals/news ingestion with temporal grounding and citations
- CI pipeline with smoke E2E test and linting

## 9) Troubleshooting

- No Streamlit found: ensure `pip install -r requirements.txt` and run `streamlit run streamlit_app.py`
- Missing API keys: set `OPENAI_API_KEY` for LLM features; `FINANCIAL_DATASETS_API_KEY` for live data
- Port in use: run with `--server.port 8502` (or another free port)
