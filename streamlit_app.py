#!/usr/bin/env python3
"""
Streamlit UI for Antipodes AI Agent System

Run with:
  streamlit run streamlit_app.py
"""

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List

import streamlit as st
from dotenv import load_dotenv
load_dotenv()  # Ensure OPENAI_API_KEY from .env is available to config

# Make sure we can import from src
import sys
from pathlib import Path as _Path
sys.path.append(str(_Path(__file__).parent / "src"))

from src.workflow import AgentWorkflow
from src.config import config
from src.models import CoordinatorResult
from src.experiments.ab_runner import VariantConfig, run_rolling_ab


def _run_workflow(as_of_date: date) -> dict:
    workflow = AgentWorkflow()
    return workflow.run(as_of_date)


def _render_results(final_state: dict) -> None:
    results: List[CoordinatorResult] = final_state["coordinator_results"]
    backtest = final_state["backtest_result"]
    output_files = final_state.get("output_files", {})

    st.subheader("Trading Decisions")
    rows = []
    for r in results:
        rows.append({
            "ticker": r.ticker,
            "valuation": f"{r.valuation_rating.value} ({r.valuation_score:.3f})",
            "sentiment": f"{r.sentiment_rating.value} ({r.sentiment_score:.3f})",
            "fundamental": f"{r.fundamental_rating.value} ({r.fundamental_score:.3f})",
            "final": r.final_rating.value,
            "final_score": round(r.final_score, 3),
        })
    if rows:
        st.dataframe(rows, width='stretch')

    st.subheader("Backtest Performance")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Portfolio Return", f"{backtest.portfolio_return:.2%}")
    k2.metric("Benchmark Return", f"{backtest.benchmark_return:.2%}")
    k3.metric("Active Return", f"{backtest.active_return:.2%}")
    k4.metric("Sharpe (proxy)", f"{backtest.sharpe_ratio:.3f}")

    st.caption(f"Period: {backtest.start_date} → {backtest.end_date} | BUY positions: {backtest.num_buy_positions}")

    if chart_path := output_files.get("chart"):
        st.subheader("Performance Chart")
        if Path(chart_path).exists():
            st.image(chart_path, width='stretch')
        else:
            st.info("Chart file not found yet.")

    if report_path := output_files.get("llm_report"):
        st.subheader("LLM Performance Report")
        try:
            md = Path(report_path).read_text()
            st.markdown(md)
        except Exception as _:
            st.info("Report not available.")

    with st.expander("Generated files"):
        for name, path in output_files.items():
            st.write(f"{name}: {path}")
        # Offer downloads when available
        for key in ("picks", "performance", "attribution"):
            p = output_files.get(key)
            if p and Path(p).exists():
                try:
                    data = Path(p).read_bytes()
                    st.download_button(label=f"Download {key}.csv", data=data, file_name=Path(p).name)
                except Exception:
                    pass


def _collect_recent_performance() -> dict:
    perf_csv = Path("outputs/performance.csv")
    if not perf_csv.exists():
        return {}
    try:
        import pandas as pd
        df = pd.read_csv(perf_csv)
        return {row["metric"]: row["value"] for _, row in df.iterrows()}
    except Exception:
        return {}


def _collect_market_context() -> dict:
    return {
        "universe": config.trading.tickers,
        "forward_window_days": config.trading.forward_window_days,
    }


def main() -> None:
    st.set_page_config(page_title="Antipodes Agents", layout="wide")
    st.title("Antipodes AI Agent System")
    st.caption("Multi-agent analysis, coordination, and backtesting")

    with st.sidebar:
        st.header("Parameters")
        default_date = date(2025, 7, 1)
        as_of_date = st.date_input("Decision date", value=default_date, min_value=date(2020, 1, 1))

        st.divider()
        st.header("Universe & Weights")
        # Allow quick override of tickers (write back to config at runtime)
        tickers = st.text_input("Tickers (comma-separated)", ", ".join(config.trading.tickers))

        col1, col2, col3 = st.columns(3)
        with col1:
            vw = st.number_input("Valuation w", value=float(config.trading.valuation_weight), min_value=0.0, max_value=1.0, step=0.05)
        with col2:
            sw = st.number_input("Sentiment w", value=float(config.trading.sentiment_weight), min_value=0.0, max_value=1.0, step=0.05)
        with col3:
            fw = st.number_input("Fundamental w", value=float(config.trading.fundamental_weight), min_value=0.0, max_value=1.0, step=0.05)

        fwd = st.number_input("Forward window (days)", value=int(config.trading.forward_window_days), min_value=7, max_value=365, step=1)

        st.divider()
        llm_report_toggle = st.toggle("Generate LLM performance report (uses OpenAI API)", value=True)
        run_btn = st.button("Run Analysis", type="primary")

    # Apply sidebar config overrides
    try:
        parsed = [t.strip().upper() for t in tickers.split(",") if t.strip()]
        if parsed:
            config.trading.tickers = parsed
        config.trading.valuation_weight = float(vw)
        config.trading.sentiment_weight = float(sw)
        config.trading.fundamental_weight = float(fw)
        config.trading.forward_window_days = int(fwd)
    except Exception as _:
        st.warning("Invalid configuration input; using defaults.")

    if run_btn:
        with st.spinner("Running multi-agent workflow..."):
            try:
                # Temporarily disable LLM report by unsetting key if toggle is off
                original_key = config.api.openai_api_key
                if not llm_report_toggle:
                    config.api.openai_api_key = None
                final_state = _run_workflow(as_of_date)
                config.api.openai_api_key = original_key

                _render_results(final_state)
                if errors := final_state.get("errors"):
                    st.warning("Some steps reported warnings/errors:")
                    for e in errors:
                        st.write(f"- {e}")
            except Exception as e:
                st.error(f"Run failed: {e}")

    st.divider()
    st.subheader("LLM Optimizer (recommendations)")
    st.caption("Proposes small parameter changes; requires manual apply.")
    opt_col1, opt_col2 = st.columns([1, 1])
    with opt_col1:
        if st.button("Get optimization suggestions"):
            try:
                from src.llm.optimizer import LLMOptimizer
                perf = _collect_recent_performance()
                ctx = _collect_market_context()
                optimizer = LLMOptimizer()
                suggestion = optimizer.optimize_parameters(perf, ctx)
                st.session_state["last_suggestion"] = suggestion
            except Exception as e:
                st.error(f"Optimizer failed: {e}")
    with opt_col2:
        if st.button("Apply last suggestion"):
            suggestion = st.session_state.get("last_suggestion")
            if not suggestion or not isinstance(suggestion, dict) or "changes" not in suggestion:
                st.warning("No valid suggestion to apply.")
            else:
                changes = suggestion["changes"]
                try:
                    config.trading.valuation_weight = float(changes.get("valuation_weight", config.trading.valuation_weight))
                    config.trading.sentiment_weight = float(changes.get("sentiment_weight", config.trading.sentiment_weight))
                    config.trading.fundamental_weight = float(changes.get("fundamental_weight", config.trading.fundamental_weight))
                    config.trading.buy_threshold = float(changes.get("buy_threshold", config.trading.buy_threshold))
                    config.trading.sell_threshold = float(changes.get("sell_threshold", config.trading.sell_threshold))
                    config.trading.forward_window_days = int(changes.get("forward_window_days", config.trading.forward_window_days))
                    st.success("Applied suggestions to runtime config. Re-run analysis to evaluate.")
                except Exception as _:
                    st.error("Failed to apply suggestion values.")

    if st.session_state.get("last_suggestion"):
        st.write("Last suggestion:")
        st.json(st.session_state["last_suggestion"])

    st.divider()
    st.subheader("A/B Experiments (rolling)")
    st.caption("Compare baseline vs variant across multiple decision dates.")
    with st.expander("Run A/B"):
        c1, c2 = st.columns(2)
        with c1:
            lookback_months = st.number_input("Number of past months (decision dates)", value=3, min_value=1, max_value=24)
            uplift_threshold = st.number_input("Promote if average active return uplift >=", value=0.005, step=0.001, format="%.3f")
        with c2:
            use_last_suggestion = st.toggle("Use last optimizer suggestion as Variant B", value=True)

        baseline = VariantConfig(name="Baseline", values={})
        if use_last_suggestion and st.session_state.get("last_suggestion"):
            changes = st.session_state["last_suggestion"].get("changes", {})
        else:
            changes = {}
        variant = VariantConfig(name="Variant", values=changes)

        if st.button("Run rolling A/B"):
            try:
                # build recent monthly dates ending at chosen as_of_date
                end_date = as_of_date
                dates = []
                for i in range(int(lookback_months)):
                    # pick the 1st of each prior month for determinism
                    month = (end_date.month - i - 1) % 12 + 1
                    year = end_date.year + ((end_date.month - i - 1) // 12)
                    d = date(year, month, 1)
                    dates.append(d)
                dates = sorted(list(set(dates)))

                with st.spinner("Running A/B experiments..."):
                    res = run_rolling_ab(dates, baseline, variant)

                import pandas as pd
                df_a = pd.DataFrame(res["A"]).set_index("date")
                df_b = pd.DataFrame(res["B"]).set_index("date")
                comp = pd.concat({"A": df_a, "B": df_b}, axis=1)
                comp["uplift_active_return"] = comp["B"]["active_return"] - comp["A"]["active_return"]
                st.dataframe(comp.reset_index(), width='stretch')

                avg_uplift = comp["uplift_active_return"].mean()
                st.metric("Average uplift (active return)", f"{avg_uplift:.2%}")

                # Export CSV
                try:
                    csv_bytes = comp.reset_index().to_csv(index=False).encode()
                    st.download_button("Download A/B results CSV", data=csv_bytes, file_name="ab_results.csv")
                except Exception:
                    pass

                # Promote variant if threshold met
                if avg_uplift >= uplift_threshold and changes:
                    if st.button("Promote Variant (apply params)"):
                        try:
                            # Apply same logic as optimizer apply
                            config.trading.valuation_weight = float(changes.get("valuation_weight", config.trading.valuation_weight))
                            config.trading.sentiment_weight = float(changes.get("sentiment_weight", config.trading.sentiment_weight))
                            config.trading.fundamental_weight = float(changes.get("fundamental_weight", config.trading.fundamental_weight))
                            config.trading.buy_threshold = float(changes.get("buy_threshold", config.trading.buy_threshold))
                            config.trading.sell_threshold = float(changes.get("sell_threshold", config.trading.sell_threshold))
                            config.trading.forward_window_days = int(changes.get("forward_window_days", config.trading.forward_window_days))
                            st.success("Variant promoted to runtime config. Re-run analysis to evaluate.")
                        except Exception:
                            st.error("Failed to promote variant.")
                elif not changes:
                    st.info("No variant changes provided.")
                else:
                    st.info("Variant did not meet uplift threshold; not promoting.")

            except Exception as e:
                st.error(f"A/B run failed: {e}")

    st.sidebar.caption("Tip: Results also saved under outputs/ as CSV/PNG")


if __name__ == "__main__":
    main()


