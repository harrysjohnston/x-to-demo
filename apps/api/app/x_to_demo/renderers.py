"""Deterministic markdown renderers and parsers for x-to-demo artifacts."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from .schemas.code_spec import CodeSpecArtifact
from .schemas.demo_spec import DemoSpecArtifact
from .schemas.feature_spec import FeatureSpecArtifact

if TYPE_CHECKING:
    from pydantic import BaseModel

_CANONICAL_JSON_HEADING = "## Canonical JSON"


def _bullet_lines(values: list[str], *, empty_message: str = "None") -> list[str]:
    if not values:
        return [f"- {empty_message}"]
    return [f"- {value}" for value in values]


def _acceptance_lines(acceptance_criteria: list[dict[str, Any]]) -> list[str]:
    if not acceptance_criteria:
        return ["- None"]

    lines: list[str] = []
    for index, criterion in enumerate(acceptance_criteria, start=1):
        lines.append(f"### AC {index}")
        lines.append(f"- Given: {criterion.get('given', '')}")
        lines.append(f"- When: {criterion.get('when', '')}")
        then_items = criterion.get("then", [])
        if isinstance(then_items, list) and then_items:
            lines.append("- Then:")
            for item in then_items:
                lines.append(f"  - {item}")
        else:
            lines.append("- Then: None")
        lines.append("")

    while lines and not lines[-1]:
        lines.pop()
    return lines


def _canonical_json_block(model: BaseModel) -> list[str]:
    return [
        _CANONICAL_JSON_HEADING,
        "```json",
        json.dumps(model.model_dump(mode="json"), indent=2, sort_keys=True),
        "```",
    ]


def render_feature_spec_markdown(artifact: FeatureSpecArtifact) -> str:
    lines = [
        f"# Phase 1: Input -> Feature Spec: {artifact.feature_name}",
        "",
        "## Summary",
        f"- Objective: {artifact.intent.objective}",
        f"- Outcome: {artifact.intent.desired_outcome}",
        "",
        "## Intent",
        f"- Problem: {artifact.intent.problem}",
        f"- Objective: {artifact.intent.objective}",
        f"- Desired outcome: {artifact.intent.desired_outcome}",
        f"- Target persona: {artifact.intent.target_persona}",
        "",
        "## External Behavior",
        "### Inputs",
        *_bullet_lines(artifact.external_behavior.inputs),
        "",
        "### Outputs",
        *_bullet_lines(artifact.external_behavior.outputs),
        "",
        "### States",
        *_bullet_lines(artifact.external_behavior.states),
        "",
        "### Errors",
        *_bullet_lines(artifact.external_behavior.errors),
        "",
        "## Acceptance Criteria",
        *_acceptance_lines(
            [criterion.model_dump(mode="json") for criterion in artifact.acceptance_criteria]
        ),
        "",
        "## Invariants",
        *_bullet_lines(artifact.invariants),
        "",
        "## Success Metrics",
        *_bullet_lines(artifact.success_metrics),
        "",
        "## Versioning",
        f"- Version: {artifact.versioning.version}",
        f"- Updated (UTC): {artifact.versioning.updated_at_utc}",
        "- Changelog:",
        *_bullet_lines(artifact.versioning.changelog),
        "",
        *_canonical_json_block(artifact),
    ]
    return "\n".join(lines).strip() + "\n"


def render_demo_spec_markdown(artifact: DemoSpecArtifact) -> str:
    lines = [
        f"# Phase 2: Feature Spec -> Demo Spec: {artifact.feature_name}",
        "",
        "## Summary",
        f"- Overview: {artifact.demo_overview}",
        f"- Format: {artifact.demo_format}",
        "",
        "## Demo Overview",
        artifact.demo_overview,
        "",
        "## Demo Scope",
        "### In Scope",
        *_bullet_lines(artifact.demo_scope.in_scope),
        "",
        "### Out of Scope",
        *_bullet_lines(artifact.demo_scope.out_of_scope),
        "",
        "## Demo Format",
        f"- {artifact.demo_format}",
        "",
        "## Core Flow Steps",
        *_bullet_lines(artifact.core_flow_steps),
        "",
        "## Success Signals",
        *_bullet_lines(artifact.success_signals),
        "",
        "## Example Copy",
        *_bullet_lines(artifact.example_copy),
        "",
        *_canonical_json_block(artifact),
    ]
    return "\n".join(lines).strip() + "\n"


def render_code_spec_markdown(artifact: CodeSpecArtifact) -> str:
    lines = [
        f"# Phase 3: Demo Spec -> Code Spec: {artifact.feature_name}",
        "",
        "## Summary",
        f"- Overview: {artifact.demo_overview}",
        f"- Frontend: {artifact.tech_stack.frontend}",
        f"- Language: {artifact.tech_stack.language}",
        "",
        "## Demo Overview",
        artifact.demo_overview,
        "",
        "## Tech Stack",
        f"- Frontend: {artifact.tech_stack.frontend}",
        f"- Backend: {artifact.tech_stack.backend or 'N/A'}",
        f"- Language: {artifact.tech_stack.language}",
        "",
        "## Project Changes",
        *_bullet_lines(artifact.project_changes),
        "",
        "## Components",
        *_bullet_lines(artifact.components),
        "",
        "## State Model",
        *_bullet_lines(artifact.state_model.fields),
        "",
        "## AI Seam",
        "### Schemas",
        *_bullet_lines(artifact.ai_seam.schemas),
        "",
        "### Contracts",
        *_bullet_lines(artifact.ai_seam.contracts),
        "",
        f"### Mock Strategy\n- {artifact.ai_seam.mock_strategy}",
        "",
        "## Acceptance Tests",
        *_acceptance_lines(
            [criterion.model_dump(mode="json") for criterion in artifact.acceptance_tests]
        ),
        "",
        "## Non Goals",
        *_bullet_lines(artifact.non_goals),
        "",
        *_canonical_json_block(artifact),
    ]
    return "\n".join(lines).strip() + "\n"


def render_markdown(model: BaseModel) -> str:
    """Render deterministic markdown for a supported artifact model."""
    if isinstance(model, FeatureSpecArtifact):
        return render_feature_spec_markdown(model)
    if isinstance(model, DemoSpecArtifact):
        return render_demo_spec_markdown(model)
    if isinstance(model, CodeSpecArtifact):
        return render_code_spec_markdown(model)
    raise TypeError(f"Unsupported artifact model: {type(model).__name__}")


def extract_canonical_json(markdown: str) -> dict[str, Any]:
    """Extract canonical JSON payload embedded in markdown."""
    canonical_section = re.search(
        rf"{re.escape(_CANONICAL_JSON_HEADING)}\s*```json\s*(.*?)\s*```",
        markdown,
        flags=re.IGNORECASE | re.DOTALL,
    )
    raw_block = canonical_section.group(1) if canonical_section else None

    if raw_block is None:
        blocks = re.findall(r"```json\s*(.*?)\s*```", markdown, flags=re.IGNORECASE | re.DOTALL)
        if not blocks:
            raise ValueError("No JSON code block found in markdown")
        raw_block = blocks[-1]

    try:
        payload = json.loads(raw_block)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON block in markdown: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Canonical JSON block must decode to an object")
    return payload


def parse_markdown_to_model(markdown: str, model_type: type[BaseModel]) -> BaseModel:
    """Parse markdown to a model using the embedded canonical JSON block."""
    payload = extract_canonical_json(markdown)
    return model_type.model_validate(payload)
