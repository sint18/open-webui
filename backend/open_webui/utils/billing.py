import asyncio
import math

from datetime import datetime
from functools import wraps

import aiohttp
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from fastapi import Request, HTTPException, status, Response

from env import LITELLM_URL, LITELLM_MASTER_KEY
from open_webui.models.billing import StatusEnum
from open_webui.models.billing import UserCredits, CreditTransactions, CreditTransactionForm
from open_webui.utils.auth import get_current_user, get_http_authorization_cred
import logging
import json
from typing import Optional, Dict, Any, List, AsyncGenerator

log = logging.getLogger(__name__)

CREDIT_RATE = 0.0015


def calculate_cost(cost_usd: float) -> int:
    return math.ceil(cost_usd / CREDIT_RATE)


async def check_balance(user_id: str, min_credits: int = 1) -> Optional[int]:
    # Check balance
    my_credits = UserCredits.get_user_credits(user_id)

    if my_credits.status != StatusEnum.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Subscription has ended. Please contact support for further assistance.",
        )

    # Check if subscription period has ended
    now = datetime.now()
    if my_credits.current_period_end and now > datetime.fromtimestamp(my_credits.current_period_end):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Subscription period has ended",
        )

    if not my_credits or my_credits.credit_balance < min_credits:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits",
        )
    return my_credits.credit_balance


async def _lookup_cost(request_id: str) -> Optional[float]:
    """Fetch request cost from LiteLLM's spend logs endpoint"""
    try:
        headers = {
            "Authorization": f"Bearer {LITELLM_MASTER_KEY}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            print(f"Lookup cost from LiteLLM spend logs endpoint for request_id: {request_id}")
            async with session.get(f"{LITELLM_URL}/spend/logs?request_id={request_id}", headers=headers) as response:
                if response.status == 200:
                    # Read the response content only once
                    text_content = await response.text()
                    print(f"Raw response: {text_content}")

                    try:
                        logs = json.loads(text_content)
                        print(f"Parsed logs: {logs}")

                        if isinstance(logs, list) and logs:
                            spend = logs[0].get('spend')
                            if spend is not None:
                                return float(spend)
                            else:
                                print(f"No 'spend' field found in first log entry: {logs[0]}")
                        else:
                            print(f"Unexpected logs format. Expected list, got: {type(logs)}")
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse JSON response: {e}")
                    except AttributeError as e:
                        print(f"No logs found in response: {e}")
                        print(f"No logs found in response, logs: {logs}")
                else:
                    print(f"Unexpected status code: {response.status}")
                    print(f"Response content: {await response.text()}")
    except Exception as e:
        log.error(f"Error fetching cost from LiteLLM: {e}", exc_info=True)
    return None


async def _lookup_cost_with_retry(request_id: str,
                                  retries: int = 10,
                                  base_delay: float = 5) -> float | None:
    """
    Try /spend/logs several times (exponential back-off) before giving up.
    """
    delay = base_delay
    for _ in range(retries):
        cost = await _lookup_cost(request_id)
        if cost is not None:
            return cost
        await asyncio.sleep(delay)
        delay *= 2  # 100 ms → 200 ms → 400 ms …
    return None


def _extract_request_id_from_body(response: Response) -> str | None:
    """
    Try to grab the `id` field from a **non-streaming** response.

    Works for FastAPI/Starlette `JSONResponse`, `PlainTextResponse`, etc.,
    as well as Pydantic models (FastAPI encodes them as JSONResponse).
    """
    body: bytes | None = getattr(response, "body", None)
    if not body:
        return None

    try:  # 1) JSON encoded?
        obj = json.loads(body)
        if isinstance(obj, dict):
            return obj.get("id")
    except Exception:
        pass

    try:  # 2) Plain string that *is* JSON
        obj = json.loads(body.decode())
        if isinstance(obj, dict):
            return obj.get("id")
    except Exception:
        pass

    return None


async def process_billing(
        user_id: str, cost_usd: float, model_name: str
) -> None:
    """Unmodified billing logic you provided."""
    try:
        # headers = response_metadata.get("headers", {})

        credits_to_charge = calculate_cost(cost_usd)
        print(credits_to_charge)
        updated = UserCredits.update_credits(user_id, -credits_to_charge)
        if not updated:
            log.error(f"Failed to debit credits for user {user_id}")
            return

        CreditTransactions.insert_transaction(
            user_id,
            CreditTransactionForm(
                delta=-credits_to_charge,
                usd_spend=cost_usd,
                model_name=model_name,
            ),
        )
    except Exception as e:
        log.error(f"Error processing billing: {e}")


def requires_credits(min_credits: int = 1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('user')
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User context required"
                )

            model_name = kwargs.get('form_data', {}).get('model') or kwargs.get('body', {}).get('model', '')

            # Check credits before processing
            await check_balance(user.id, min_credits)

            # Call the original function
            response = await func(*args, **kwargs)

            # Checking response type
            if not isinstance(response, StreamingResponse):
                request_id = _extract_request_id_from_body(response)
                if request_id:
                    cost_usd = await _lookup_cost_with_retry(request_id)
                    if cost_usd is None:
                        cost_usd = float(0)

                    if cost_usd is not None:
                        # bill *now*, inside the request-handling coroutine
                        await process_billing(user.id, cost_usd, model_name)
                return response

            # 4. Streaming responses – bill *after* they finish
            # -------------  STREAMING  -----‐----------------------------------------
            original_iter = response.body_iterator
            # For Billing
            captured: dict = {"id": None}  # to store the request_id

            async def capture_and_forward():
                """
                Pass chunks straight through **once** while trying to pull `"id"`
                out of the last `data: {...}` message of the SSE stream.
                """
                async for chunk in original_iter:
                    try:
                        # SSE chunks look like:  b'data: {...}\n\n'
                        if chunk.startswith(b"data:"):
                            payload = chunk[5:].strip()  # drop 'data:'
                            # ignore the special terminator 'data: [DONE]'
                            if payload and payload != b"[DONE]":
                                obj = json.loads(payload)
                                if "id" in obj and captured["id"] is None:
                                    captured["id"] = obj["id"]
                    except Exception:
                        pass  # never break the stream for parse errors
                    yield chunk

            response.body_iterator = capture_and_forward()

            async def finalize():
                if captured["id"]:
                    print(captured)
                    cost_usd = await _lookup_cost_with_retry(captured["id"])
                    print(cost_usd)
                    # 3b. fallback to header set by LiteLLM middleware
                    if cost_usd is None:
                        cost_usd = float(0)

                    if cost_usd is not None:
                        await process_billing(user.id, cost_usd, model_name)

            response.background = BackgroundTask(finalize)
            return response

        return wrapper

    return decorator


class BillingMiddleware:
    AI_ENDPOINTS = {
        "/api/chat/completions",
        "/api/audio/speech",
        "/api/v1/audio/speech",
        "/api/v1/audio/transcriptions",
        "/openai/models"
    }

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Only handle HTTP
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Pre-buffer the entire request body so we can parse and then replay it
        body_chunks: List[Dict[str, Any]] = []
        more_body = True
        while more_body:
            message = await receive()
            body_chunks.append(message)
            more_body = message.get("more_body", False)

        # Parse JSON body for model_name (if any)
        concatenated = b"".join(chunk.get("body", b"") for chunk in body_chunks)
        try:
            body_data = json.loads(concatenated) if concatenated else {}
        except json.JSONDecodeError:
            body_data = {}
        model_name = body_data.get("model", "")

        # Create a new receive that replays buffered messages, then yields new ones
        replay_index = 0

        async def replay_receive() -> Dict[str, Any]:
            nonlocal replay_index
            if replay_index < len(body_chunks):
                msg = body_chunks[replay_index]
                replay_index += 1
                return msg
            return await receive()

        request = Request(scope, receive=replay_receive)

        # Only target AI endpoints
        if not any(request.url.path.endswith(ep) for ep in self.AI_ENDPOINTS):
            return await self.app(scope, replay_receive, send)

        # Authenticate user
        auth_header = request.headers.get("Authorization")
        try:
            user = get_current_user(
                request, None, get_http_authorization_cred(auth_header)
            )
            if not user:
                raise Exception()
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        # Check balance
        credits = UserCredits.get_user_credits(user.id)
        if not credits or credits.credit_balance < 1:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits",
            )

        # Prepare to capture response metadata
        response_metadata: Dict[str, Any] = {}
        is_streaming = False
        headers_sent = False

        async def wrapped_send(message: Dict[str, Any]) -> None:
            nonlocal headers_sent, is_streaming
            print(message.get("headers"))
            if message["type"] == "http.response.start":
                headers_sent = True

                # Strip Content-Length to avoid mismatches
                raw_headers = message["headers"]
                filtered = [
                    (k, v) for k, v in raw_headers if k.lower() != b"content-length"
                ]
                message["headers"] = filtered

                # Record status & headers for billing logic
                response_metadata.update({
                    "status": message["status"],
                    "headers": dict(filtered),
                })

                # Detect streaming by SSE content-type :contentReference[oaicite:5]{index=5}
                ct = dict(filtered).get(b"content-type", b"").decode()
                is_streaming = "text/event-stream" in ct

            elif message["type"] == "http.response.body":
                # Non-streaming: bill when full body sent
                if not is_streaming and not message.get("more_body", False):
                    print(message.get("headers"))
                    await process_billing(user.id, response_metadata, model_name)

                # Streaming: bill when the final chunk arrives :contentReference[oaicite:6]{index=6}
                if is_streaming and not message.get("more_body", False):
                    print(message.get("headers"))
                    await process_billing(user.id, response_metadata, model_name)

            await send(message)

        # Call the downstream app with replay_receive and wrapped_send
        await self.app(scope, replay_receive, wrapped_send)
