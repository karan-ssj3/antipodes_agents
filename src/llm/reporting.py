from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import List

from openai import OpenAI

from ..models import CoordinatorResult, MarketData, BacktestResult
from ..backtesting import BacktestEngine
from ..config import config


class LLMBacktestReporter:
    """
    Generates a markdown performance report using an LLM, grounded on
    numeric results from the backtest and simple per-ticker attribution.
    """

    def __init__(self, model: str | None = None, output_dir: str = "outputs"):
        self.model = model or "gpt-4o-mini"
        self.client = OpenAI()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def _per_ticker_forward_returns(
        self,
        market_data: MarketData,
        as_of_date: date,
    ) -> dict[str, float]:
        engine = BacktestEngine()
        start = as_of_date + timedelta(days=1)
        end = as_of_date + timedelta(days=config.trading.forward_window_days)
        returns: dict[str, float] = {}
        for ticker in config.trading.tickers:
            r = engine._calculate_ticker_return(ticker, market_data, start, end)
            returns[ticker] = r
        return returns

    def generate_performance_report(
        self,
        backtest_result: BacktestResult,
        coordinator_results: List[CoordinatorResult],
        market_data: MarketData,
        as_of_date: date,
    ) -> str:
        per_ticker = self._per_ticker_forward_returns(market_data, as_of_date)
        buys = [r.ticker for r in coordinator_results if r.final_rating.value == "BUY"]
        holds = [r.ticker for r in coordinator_results if r.final_rating.value == "HOLD"]
        sells = [r.ticker for r in coordinator_results if r.final_rating.value == "SELL"]

        prompt = f"""
        You are a precise, non-fabricating quant research assistant. Produce a concise markdown
        report attributing portfolio performance and suggesting next steps.

        Context (exact numbers, do not invent):
        - As-Of Date: {as_of_date}
        - Period: {backtest_result.start_date} to {backtest_result.end_date}
        - Portfolio Return: {backtest_result.portfolio_return:.6f}
        - Benchmark Return: {backtest_result.benchmark_return:.6f}
        - Active Return: {backtest_result.active_return:.6f}
        - Sharpe Proxy: {backtest_result.sharpe_ratio:.6f}
        - BUY: {buys}
        - HOLD: {holds}
        - SELL: {sells}
        - Per-ticker forward returns: {per_ticker}

        Requirements:
        - Keep it grounded in provided numbers only.
        - Include: brief overview, key drivers (top +/- contributors), risks, and 3 actionable suggestions.
        - Prefer bullet points, short paragraphs, and avoid hype.
        - Output valid GitHub-flavored markdown only.
        """

        completion = self.client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            messages=[
                {"role": "system", "content": "You are a precise quant research assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        text = completion.choices[0].message.content or ""
        return text

    def save_report(self, markdown_text: str) -> str:
        path = self.output_dir / "performance_report.md"
        path.write_text(markdown_text)
        return str(path)


