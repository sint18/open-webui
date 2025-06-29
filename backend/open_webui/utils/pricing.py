# billing/test_pricing.py
from __future__ import annotations
import json, httpx, functools, decimal
from decimal import Decimal
from typing import Tuple

PRICE_URL = (
    "https://raw.githubusercontent.com/"
    "BerriAI/litellm/main/model_prices_and_context_window.json"
)

# ────────────────────────────────────────────────────────────────
# Internal: fetch-once JSON → {model: {"input_cost_per_token": …}}
# ────────────────────────────────────────────────────────────────
@functools.lru_cache(maxsize=1)
def _load_price_map() -> dict:
    """Download and cache LiteLLM's live price sheet."""
    resp = httpx.get(PRICE_URL, timeout=10)
    resp.raise_for_status()
    data = json.loads(resp.text)
    return data  # top level is a dict keyed by model-name


def estimate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> Decimal:
    """
    Return (prompt_cost, completion_cost, total_cost) in USD.
    Uses LiteLLM's public price map; caches the JSON in-process.
    """
    model = model.lower().strip()
    price_map = _load_price_map()

    if model not in price_map:
        raise ValueError(
            f"model '{model}' not found in LiteLLM price map @ {PRICE_URL}"
        )

    meta = price_map[model]
    try:
        in_rate = Decimal(str(meta["input_cost_per_token"]))
        out_rate = Decimal(str(meta["output_cost_per_token"]))
    except KeyError as e:
        raise KeyError(f"price map missing expected key: {e}") from None

    prompt_cost = Decimal(prompt_tokens) * in_rate
    completion_cost = Decimal(completion_tokens) * out_rate
    return prompt_cost + completion_cost
