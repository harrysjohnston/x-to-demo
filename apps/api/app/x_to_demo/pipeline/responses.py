"""Responses API helpers for structured phase execution."""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import logging
    from collections.abc import Callable

    from .models import PhaseKey


def call_responses_with_progress_logs(
    *,
    create_call: Callable[..., object],
    payload: dict[str, object],
    phase_key: PhaseKey,
    response_wait_log_interval_seconds: float,
    default_model: str,
    executor_cls: type[ThreadPoolExecutor] | Any = ThreadPoolExecutor,
    logger: logging.Logger,
) -> object:
    """Call Responses API and periodically emit wait logs while awaiting completion."""
    start_time = datetime.now(UTC)
    with executor_cls(max_workers=1) as executor:
        future = executor.submit(create_call, **payload)
        elapsed_seconds = 0.0
        while True:
            try:
                return future.result(timeout=response_wait_log_interval_seconds)
            except FutureTimeoutError:
                elapsed_seconds += response_wait_log_interval_seconds
                logger.info(
                    "Awaiting OpenAI response",
                    extra={
                        "phase_key": phase_key,
                        "model": str(payload.get("model", default_model)),
                        "elapsed_seconds": int(elapsed_seconds),
                        "started_at": start_time.isoformat(),
                    },
                )


def create_conversation_id(*, responses_client: object, run_id: str, user_id: int) -> str | None:
    """Create a conversation when the client supports it, otherwise return `None`."""
    conversations_api = getattr(responses_client, "conversations", None)
    if conversations_api is None:
        return None

    try:
        conversation = conversations_api.create(
            metadata={
                "pipeline": "x-to-demo",
                "run_id": run_id,
                "user_id": str(user_id),
            }
        )
    except Exception:
        return None

    if isinstance(conversation, dict):
        raw_id = conversation.get("id")
    else:
        raw_id = getattr(conversation, "id", None)
    return str(raw_id) if raw_id else None


def extract_structured_payload(response: object) -> dict[str, Any]:
    """Extract the structured JSON object from a polymorphic response payload."""
    output_parsed = getattr(response, "output_parsed", None)
    if isinstance(output_parsed, dict):
        return output_parsed
    if hasattr(output_parsed, "model_dump"):
        payload = output_parsed.model_dump(mode="json")
        if isinstance(payload, dict):
            return payload

    response_payload = response_to_dict(response)
    parsed_in_payload = response_payload.get("output_parsed")
    if isinstance(parsed_in_payload, dict):
        return parsed_in_payload

    output_text = extract_output_text(response)
    if not output_text:
        raise RuntimeError("Responses API returned an empty structured output")

    candidate = output_text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
        candidate = re.sub(r"\s*```$", "", candidate)

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Structured output was not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("Structured output must decode to a JSON object")
    return payload


def extract_output_text(response: object) -> str:
    """Extract output text from polymorphic Responses API payloads."""
    direct_output_text = getattr(response, "output_text", None)
    if isinstance(direct_output_text, str) and direct_output_text.strip():
        return direct_output_text.strip()

    payload = response
    if hasattr(response, "model_dump"):
        payload = response.model_dump()

    if not isinstance(payload, dict):
        return ""

    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    chunks: list[str] = []
    output_items = payload.get("output", [])
    if not isinstance(output_items, list):
        return ""

    for item in output_items:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "message":
            continue
        content = item.get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            block_text = block.get("text")
            if isinstance(block_text, str) and block_text.strip():
                chunks.append(block_text.strip())

    return "\n\n".join(chunks).strip()


def response_to_dict(response: object) -> dict[str, Any]:
    """Normalize SDK response objects and dict-like payloads into a dictionary."""
    if isinstance(response, dict):
        return response
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if hasattr(response, "to_dict"):
        return response.to_dict()
    if hasattr(response, "json"):
        try:
            payload = json.loads(response.json())
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}
    return {}


def extract_usage(response: object) -> dict[str, int]:
    """Extract token usage from object or dict payloads."""
    usage = getattr(response, "usage", None)
    if usage is None:
        usage = response_to_dict(response).get("usage")
    if usage is None:
        return {}

    if isinstance(usage, dict):
        details = usage.get("input_tokens_details") or {}
        cached = details.get("cached_tokens")
        if cached is None:
            cached = usage.get("cached_input_tokens")
        return {
            "input_tokens": int(usage.get("input_tokens", 0) or 0),
            "output_tokens": int(usage.get("output_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", 0) or 0),
            "reasoning_tokens": int(usage.get("reasoning_tokens", 0) or 0),
            "cached_input_tokens": int(cached or 0),
        }

    details = getattr(usage, "input_tokens_details", None)
    cached = getattr(details, "cached_tokens", None) if details else None
    if cached is None:
        cached = getattr(usage, "cached_input_tokens", None)
    return {
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
        "reasoning_tokens": int(getattr(usage, "reasoning_tokens", 0) or 0),
        "cached_input_tokens": int(cached or 0),
    }


def extract_model(response: object) -> str | None:
    """Extract the model identifier from response payloads."""
    model_used = getattr(response, "model", None)
    if isinstance(model_used, str) and model_used:
        return model_used
    payload_model = response_to_dict(response).get("model")
    return payload_model if isinstance(payload_model, str) and payload_model else None


def extract_status(response: object) -> str:
    """Extract response status with a safe default."""
    status = getattr(response, "status", None)
    if isinstance(status, str) and status:
        return status
    payload_status = response_to_dict(response).get("status")
    if isinstance(payload_status, str) and payload_status:
        return payload_status
    return "completed"
