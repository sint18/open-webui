# billing/test_pricing.py
from __future__ import annotations
import json, httpx, functools, decimal
from decimal import Decimal
from typing import Tuple
import tiktoken

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


def extract_prompt_text(messages: list[dict]) -> str:
    """
    Convert messages into a role-tagged prompt string for accurate estimation.
    """
    parts = []
    for msg in messages:
        role = msg.get("role", "unknown").strip()
        content = msg.get("content", "").strip()
        if content:
            parts.append(f"{role}: {content}")
    return "\n".join(parts)


def estimate_prompt_tokens(prompt: str, model: str) -> int:
    """
    Estimate token count for the prompt using tiktoken or a fallback heuristic.
    """
    model = model.lower().strip()
    try:
        if "gpt" in model or "openai" in model:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(prompt))
    except Exception:
        pass
    return max(1, len(prompt) // 4)  # heuristic fallback


def estimate_completion_tokens(model: str, prompt_tokens: int) -> int:
    """
    Estimate average completion tokens based on model name or prompt length.
    """
    model = model.lower().strip()

    if "gpt-4" in model:
        return 250
    elif "gpt-3.5" in model:
        return 120
    elif "claude" in model:
        return 280
    elif "gemini" in model:
        return 200
    elif "mistral" in model or "mixtral" in model:
        return 100
    elif "llama" in model or "gemma" in model:
        return 100

    # Fallback heuristic
    estimated = int(prompt_tokens * 0.8)
    return max(50, min(estimated, 500))


def affordable(model: str, messages: list[dict], user_credit_usd: int, buffer: float = 1.0) -> bool:
    """
    Main function to check if the user can afford an LLM request.
    """
    print("Checking if user can afford an LLM request.")
    prompt_text = extract_prompt_text(messages)
    prompt_tokens = estimate_prompt_tokens(prompt_text, model)
    completion_tokens = estimate_completion_tokens(model, prompt_tokens)

    estimated_cost = estimate_cost(model, prompt_tokens, completion_tokens)
    total_cost = estimated_cost * Decimal(str(buffer))

    return total_cost <= user_credit_usd
