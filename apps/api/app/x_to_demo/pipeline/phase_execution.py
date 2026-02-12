"""Single-phase structured execution for the X-to-Demo pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.services.model_capabilities import supports_reasoning

from .models import PhaseCallMetrics, PipelinePhaseDefinition
from .pricing import estimate_cost
from .prompts import build_phase_prompts, openai_compatible_schema
from .responses import extract_model, extract_status, extract_structured_payload, extract_usage

if TYPE_CHECKING:
    import logging
    from collections.abc import Callable

    from pydantic import BaseModel


def run_structured_phase(
    *,
    phase: PipelinePhaseDefinition,
    phase_input: BaseModel,
    model: str,
    reasoning_effort: str,
    conversation_id: str | None,
    store_responses: bool,
    call_responses: Callable[[dict[str, object], str], object],
    logger: logging.Logger,
) -> tuple[BaseModel, PhaseCallMetrics]:
    """Execute one phase via structured Outputs and return validated model + metrics."""
    logger.info(
        "Starting X-to-Demo phase",
        extra={
            "phase_key": phase.key,
            "model": model,
            "reasoning_effort": reasoning_effort,
        },
    )

    started_at = datetime.now(UTC)
    developer_prompt, user_prompt = build_phase_prompts(phase=phase, phase_input=phase_input)
    payload: dict[str, object] = {
        "model": model,
        "store": store_responses,
        "input": [
            {"role": "developer", "content": developer_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": f"x_to_demo_{phase.key}",
                "schema": openai_compatible_schema(phase.output_model.model_json_schema()),
                "strict": True,
            }
        },
    }
    if supports_reasoning(model):
        payload["reasoning"] = {"effort": reasoning_effort}
    if conversation_id:
        payload["conversation"] = conversation_id

    response = call_responses(payload, phase.key)
    parsed_payload = extract_structured_payload(response)
    output_model = phase.output_model.model_validate(parsed_payload)

    usage = extract_usage(response)
    model_used = extract_model(response) or model
    cost = estimate_cost(model_name=model_used, usage=usage) if usage else None
    status = extract_status(response)
    elapsed_seconds = max((datetime.now(UTC) - started_at).total_seconds(), 0.0)

    logger.info(
        "Completed X-to-Demo phase",
        extra={
            "phase_key": phase.key,
            "model": model_used,
            "status": status,
            "elapsed_seconds": round(elapsed_seconds, 2),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
        },
    )

    return output_model, PhaseCallMetrics(
        phase_key=phase.key,
        model_used=model_used,
        usage=usage,
        cost=cost,
        elapsed_seconds=elapsed_seconds,
        status=status,
    )
