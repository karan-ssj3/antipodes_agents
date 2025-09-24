from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Tuple

from ..workflow import AgentWorkflow
from ..config import config


@dataclass
class VariantConfig:
    name: str
    values: Dict[str, float]


def _apply_trading_overrides(overrides: Dict[str, float]) -> Dict[str, float]:
    """Apply overrides to runtime config.trading, return previous values to restore."""
    prev = {
        "valuation_weight": config.trading.valuation_weight,
        "sentiment_weight": config.trading.sentiment_weight,
        "fundamental_weight": config.trading.fundamental_weight,
        "buy_threshold": config.trading.buy_threshold,
        "sell_threshold": config.trading.sell_threshold,
        "forward_window_days": config.trading.forward_window_days,
    }
    if "valuation_weight" in overrides:
        config.trading.valuation_weight = float(overrides["valuation_weight"]) 
    if "sentiment_weight" in overrides:
        config.trading.sentiment_weight = float(overrides["sentiment_weight"]) 
    if "fundamental_weight" in overrides:
        config.trading.fundamental_weight = float(overrides["fundamental_weight"]) 
    if "buy_threshold" in overrides:
        config.trading.buy_threshold = float(overrides["buy_threshold"]) 
    if "sell_threshold" in overrides:
        config.trading.sell_threshold = float(overrides["sell_threshold"]) 
    if "forward_window_days" in overrides:
        config.trading.forward_window_days = int(overrides["forward_window_days"]) 
    return prev


def _restore_trading(prev: Dict[str, float]) -> None:
    config.trading.valuation_weight = float(prev["valuation_weight"]) 
    config.trading.sentiment_weight = float(prev["sentiment_weight"]) 
    config.trading.fundamental_weight = float(prev["fundamental_weight"]) 
    config.trading.buy_threshold = float(prev["buy_threshold"]) 
    config.trading.sell_threshold = float(prev["sell_threshold"]) 
    config.trading.forward_window_days = int(prev["forward_window_days"]) 


def run_rolling_ab(
    dates: List[date],
    variant_a: VariantConfig,
    variant_b: VariantConfig,
) -> Dict[str, List[Dict[str, float]]]:
    """Run workflow for each date under two parameter variants and compare results.

    Returns a dict with per-date metrics for A and B.
    """
    results = {"A": [], "B": []}
    for d in dates:
        # Variant A
        prev = _apply_trading_overrides(variant_a.values)
        wf = AgentWorkflow()
        state_a = wf.run(d)
        br_a = state_a["backtest_result"]
        results["A"].append({
            "date": d.isoformat(),
            "portfolio_return": br_a.portfolio_return,
            "benchmark_return": br_a.benchmark_return,
            "active_return": br_a.active_return,
            "sharpe": br_a.sharpe_ratio,
        })
        _restore_trading(prev)

        # Variant B
        prev = _apply_trading_overrides(variant_b.values)
        wf = AgentWorkflow()
        state_b = wf.run(d)
        br_b = state_b["backtest_result"]
        results["B"].append({
            "date": d.isoformat(),
            "portfolio_return": br_b.portfolio_return,
            "benchmark_return": br_b.benchmark_return,
            "active_return": br_b.active_return,
            "sharpe": br_b.sharpe_ratio,
        })
        _restore_trading(prev)

    return results


