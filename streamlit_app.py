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

# Make sure we can import from src
import sys
from pathlib import Path as _Path
sys.path.append(str(_Path(__file__).parent / "src"))

from src.workflow import AgentWorkflow
from src.config import config
from src.models import CoordinatorResult


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
        st.dataframe(rows, use_container_width=True)

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
            st.image(chart_path, use_container_width=True)
        else:
            st.info("Chart file not found yet.")

    with st.expander("Generated files"):
        for name, path in output_files.items():
            st.write(f"{name}: {path}")


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
                final_state = _run_workflow(as_of_date)
                _render_results(final_state)
                if errors := final_state.get("errors"):
                    st.warning("Some steps reported warnings/errors:")
                    for e in errors:
                        st.write(f"- {e}")
            except Exception as e:
                st.error(f"Run failed: {e}")

    st.sidebar.caption("Tip: Results also saved under outputs/ as CSV/PNG")


if __name__ == "__main__":
    main()


