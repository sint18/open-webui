# billing/test_pricing.py
from __future__ import annotations
import json, httpx, functools, decimal
import math
import logging
from decimal import Decimal
from typing import Tuple
import tiktoken
import re

log = logging.getLogger(__name__)

PRICE_URL = (
    "https://raw.githubusercontent.com/"
    "BerriAI/litellm/main/model_prices_and_context_window.json"
)

CREDIT_RATE = 0.0015

def calculate_cost(cost_usd: float) -> int:
    return math.ceil(cost_usd / CREDIT_RATE)

# ────────────────────────────────────────────────────────────────
# Internal: fetch-once JSON → {model: {"input_cost_per_token": …}}
# ────────────────────────────────────────────────────────────────
@functools.lru_cache(maxsize=1)
def _load_price_map() -> dict:
    """Download and cache LiteLLM's live price sheet."""
    try:
        resp = httpx.get(PRICE_URL, timeout=10)
        resp.raise_for_status()
        data = json.loads(resp.text)
        log.info(f"Successfully loaded pricing data for {len(data)} models")
        return data  # top level is a dict keyed by model-name
    except httpx.TimeoutException as e:
        log.error(f"Timeout loading price map from {PRICE_URL}: {e}")
        raise ValueError("Unable to load pricing information due to timeout. Please try again later.")
    except httpx.HTTPError as e:
        log.error(f"HTTP error loading price map from {PRICE_URL}: {e}")
        raise ValueError("Unable to load pricing information. Please try again later.")
    except json.JSONDecodeError as e:
        log.error(f"JSON decode error loading price map: {e}")
        raise ValueError("Service configuration is temporarily unavailable. Please try again later.")
    except Exception as e:
        log.error(f"Unexpected error loading price map: {e}")
        raise ValueError("Service is temporarily unavailable. Please try again later.")


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

    try:
        price_map = _load_price_map()
    except Exception as e:
        log.error(f"Failed to load price map: {e}")
        raise ValueError("Service is temporarily unavailable. Please try again later.")

    if model not in price_map:
        log.warning(f"Model '{model}' not found in LiteLLM price map")
        raise ValueError("The requested service is currently unavailable. Please try again later.")

    meta = price_map[model]
    try:
        in_rate = Decimal(str(meta["input_cost_per_token"]))
        out_rate = Decimal(str(meta["output_cost_per_token"]))
    except KeyError as e:
        log.error(f"Price map missing expected key for model '{model}': {e}")
        raise ValueError("Service configuration is incomplete. Please try again later.")

    prompt_cost = Decimal(prompt_tokens) * in_rate
    completion_cost = Decimal(completion_tokens) * out_rate
    return prompt_cost + completion_cost


def extract_prompt_text(messages: list[dict]) -> str:
    """
    Convert messages into a role-tagged prompt string for token estimation.

    - String content → used directly.
    - List content:
      • type == "text"      → part["text"]
      • type == "image_url" → "[Image]"
      • type == "audio_url" → "[Audio]"
      • type == "video_url" → "[Video]"
      • type == "file"      → "[File: filename.ext]"
      • Other parts         → ignored
    """
    def _render_content(content):
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            pieces = []
            for part in content:
                if not isinstance(part, dict):
                    continue
                t = part.get("type")
                if t == "text" and "text" in part:
                    pieces.append(str(part["text"]).strip())
                elif t == "image_url" and isinstance(part.get("image_url"), dict):
                    url = part["image_url"].get("url", "")
                    # base64 or remote images count as one token placeholder
                    pieces.append("[Image]" if url.startswith("data:") else "[Image]")
                elif t == "audio_url":
                    pieces.append("[Audio]")
                elif t == "video_url":
                    pieces.append("[Video]")
                elif t == "file" and isinstance(part.get("file"), dict):
                    name = part["file"].get("name") or part["file"].get("filename")
                    ext = name.split(".")[-1] if name else ""
                    pieces.append(f"[File: {name}]" if name else "[File]")
                # else: skip unknown part types
            return " ".join(pieces).strip()

        return str(content).strip()

    lines = []
    for msg in messages:
        role = str(msg.get("role", "unknown")).strip()
        raw = msg.get("content", "")
        content = _render_content(raw)
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)

#
# def estimate_prompt_tokens(prompt: str, model: str) -> int:
#     """
#     Estimate token count for the prompt using tiktoken or a fallback heuristic.
#     """
#     model = model.lower().strip()
#     try:
#         if "gpt" in model or "openai" in model:
#             encoding = tiktoken.encoding_for_model(model)
#             return len(encoding.encode(prompt))
#     except Exception:
#         pass
#     return max(1, len(prompt) // 4)  # heuristic fallback


def estimate_prompt_tokens(prompt: str, model: str) -> int:
    """
    Estimate token count for the prompt, counting placeholders for
    images, audio, video, and generic files as fixed token costs, plus
    estimating the remaining text with tiktoken or a fallback heuristic.

    Placeholders recognized:
      - [Image]          → 1 token each
      - [Audio]          → 1 token each
      - [Video]          → 1 token each
      - [File: NAME.EXT] → 1 token each

    All other text is tokenized via tiktoken (if available) or
    len(text)//4 fallback.
    """
    # Define fixed costs for each placeholder type
    placeholder_costs = {
        'Image': 16,
        'Audio': 16,
        'Video': 16,
        'File': 4,
    }

    # Regex to find all placeholders of the form [Type] or [File: xyz]
    pattern = re.compile(r'\[(Image|Audio|Video|File)(?:: [^\]]+)?\]')

    total_cost = 0

    # Extract placeholders and count their cost
    def _placeholder_repl(match):
        kind = match.group(1)  # 'Image', 'Audio', 'Video', or 'File'
        nonlocal total_cost
        total_cost += placeholder_costs.get(kind, 1)
        return ""  # remove from prompt for text estimate

    # Remove all placeholders, summing their costs
    text_without_placeholders = pattern.sub(_placeholder_repl, prompt)

    # Estimate tokens for the remaining text
    text = text_without_placeholders.strip()
    text_tokens = 0
    model_key = model.lower().strip()
    if tiktoken and ("gpt" in model_key or "openai" in model_key):
        try:
            enc = tiktoken.encoding_for_model(model_key)
            text_tokens = len(enc.encode(text))
        except Exception:
            text_tokens = max(0, len(text) // 4)
    else:
        text_tokens = max(0, len(text) // 4)
    return total_cost + text_tokens


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


def affordable(model: str, messages: list[dict], user_credit: int, buffer: float = 1.0) -> bool:
    """
    Main function to check if the user can afford an LLM request.
    """
    try:
        # Don't log actual model names in production
        log.debug("Checking if user can afford request")
        prompt_text = extract_prompt_text(messages)
        prompt_tokens = estimate_prompt_tokens(prompt_text, model)
        completion_tokens = estimate_completion_tokens(model, prompt_tokens)

        estimated_cost = estimate_cost(model, prompt_tokens, completion_tokens)
        total_cost_usd = estimated_cost * Decimal(str(buffer))
        log.debug(f"Estimate cost usd: {total_cost_usd}")
        log.debug(f"Estimate cost: {estimated_cost}")
        total_cost_credit = calculate_cost(float(total_cost_usd))
        log.debug(f"Estimate cost total: {total_cost_credit}")

        return total_cost_credit <= user_credit

    except ValueError as e:
        # Don't log actual model name in error - only log internally
        log.error(f"Cost estimation failed for model '{model}': {e}")
        # Re-raise the error so it can be handled by the error handler
        raise e
    except Exception as e:
        log.error(f"Unexpected error in affordability check: {e}")
        # Re-raise the error so it can be handled by the error handler
        raise e
