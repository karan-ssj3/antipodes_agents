from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from openai import OpenAI

from ..config import config


class LLMOptimizer:
    """Proposes parameter changes based on recent performance/context.

    Returns a structured dict with suggested changes without auto-applying.
    """

    def __init__(self, model: str | None = None):
        self.model = model or "gpt-4o-mini"
        self.client = OpenAI(api_key=config.api.openai_api_key)

    def optimize_parameters(self, recent_performance: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            "You are a cautious quant assistant. Propose small, reasoned parameter adjustments "
            "as JSON only. Include 'reasoning' and a 'changes' object with keys: "
            "valuation_weight, sentiment_weight, fundamental_weight, buy_threshold, sell_threshold, forward_window_days. "
            "Bounds: weights in [0,1] and sum ~1, thresholds in [0,1], forward_window_days in [30,180]. "
            "Prefer minimal changes unless clearly beneficial."
        )

        context = {
            "current": {
                "valuation_weight": config.trading.valuation_weight,
                "sentiment_weight": config.trading.sentiment_weight,
                "fundamental_weight": config.trading.fundamental_weight,
                "buy_threshold": config.trading.buy_threshold,
                "sell_threshold": config.trading.sell_threshold,
                "forward_window_days": config.trading.forward_window_days,
            },
            "recent_performance": recent_performance,
            "market_context": market_context,
        }

        completion = self.client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Respond with JSON only, no prose."},
                {"role": "user", "content": f"{prompt}\n\nContext: {context}"},
            ],
        )

        raw = completion.choices[0].message.content or "{}"
        # Remove common code-fence wrappers if present
        def _strip_code_fences(text: str) -> str:
            t = text.strip()
            if t.startswith("```"):
                t = t.lstrip("`")
                # remove optional language tag like json\n
                if "\n" in t:
                    first_nl = t.find("\n")
                    t = t[first_nl + 1 :]
                # remove trailing fences
                if t.endswith("```"):
                    t = t[: -3]
            return t.strip()

        cleaned = _strip_code_fences(raw)
        # Basic guard: ensure we return a dict
        try:
            import json

            parsed = json.loads(cleaned)
            if not isinstance(parsed, dict):
                return {"error": "Non-dict response", "raw": raw}
            return parsed
        except Exception:
            return {"error": "Invalid JSON from model", "raw": raw}


