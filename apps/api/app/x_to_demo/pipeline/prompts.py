"""Prompt and schema helpers for structured X-to-Demo phase calls."""

from __future__ import annotations

import copy
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel

    from .models import PipelinePhaseDefinition

_GLOBAL_HARD_RULES: tuple[str, ...] = (
    "Treat AI/technical innovation as the central value of the proposed demo app.",
    "Constrain scope to one to three headline items only.",
    "Exclude non-essential plumbing by default (auth, billing, observability, queues, admin, CI/CD, and similar).",
    "Require minimalist browser-compatible UI with system dark/light theme support.",
    "Use smartphone-framed browser view only when the proposal is mobile-like.",
    "Walkthrough means an in-app interactive UI tour (auto-start, retriggerable, cancellable), not a presenter script.",
    "Walkthrough must be reliable: never get stuck, support stepping start-to-finish, allow cancel anytime, and support retriggering; include deterministic automated tests validating this and correct UI highlight targets.",
    "Use tools only when absolutely necessary; if used, require synthetic data and UI-visible tool call/results.",
    "Keep tooling decisions consistent across phases; do not introduce tools later if earlier phase output says no tools.",
    "Preserve stable headline capability identifiers across phases.",
    "No inert buttons: every interactive element must have defined behavior and automated test coverage.",
    "Validate every OpenAI request before sending (model name, required fields, strict schema constraints) and fail fast with a clear UI-visible error message; no silent failures.",
    "CodeSpec must include two-tier OpenAI tests: mocked tests run by default and low-cost live smoke tests are opt-in only when OPENAI_API_KEY (and optional explicit flag) is set; skipped live tests must not fail the default suite.",
    "Output one valid JSON object that matches the schema exactly.",
    "Do not add fields, wrappers, markdown, or prose outside schema fields.",
    "Do not invent acceptance criteria or requirements beyond the provided schema and input.",
)

_PHASE3_API_DECISION_GUIDE: tuple[str, ...] = (
    "Responses API: choose for request/response interactions (text or multimodal), simple tool calls, structured outputs, and minimal orchestration.",
    "Realtime API: choose when the demo includes live audio (voice input/output), low-latency streaming UX, or turn-taking.",
    "Agents SDK: choose when multi-step tool loops, planning, stateful agent behavior, retries, background tasks, memory, or multi-tool orchestration are required.",
    "Must map each headline demo item to selected API(s) and justify each mapping.",
)

_PHASE_RULES: dict[str, tuple[str, ...]] = {
    "feature_spec": (
        "Select one to three headline AI capabilities and center the artifact around them.",
        "Define guardrails summary and a tooling need assessment with explicit yes/no reasoning.",
        "Define stable headline capability identifiers for reuse in later phases.",
        "Keep acceptance criteria explicitly tied to the selected headline capabilities.",
    ),
    "demo_spec": (
        "Map each headline capability into a concise demo item with a clear AI moment.",
        "Define minimalist views only; include omitted/hidden elements intentionally.",
        "Delineate AI vs non-AI components and describe where innovation lives.",
        "Require interactive walkthrough details with auto-start + retrigger + cancellation controls.",
        "DemoSpec must include interaction_contracts covering every minimalist view and list every button/control with expected behavior, observable UI/state change, enable/disable rules with disabled explanation, and loading behavior.",
        "Interaction contracts must be complete (no 'and other controls' language) and screen_name must match minimalist_views[*].name.",
        "Confirm system theme support and conditional smartphone framing behavior.",
        "Make the demo runnable on first launch with synthetic seed data, default first-run inputs, and expected outputs.",
        "Provide explicit consistency trace back to phase-1 capability identifiers.",
        "Carry forward tooling decision from phase 1 without contradiction.",
    ),
    "code_spec": (
        "Select at least one OpenAI API from responses, realtime, agents and justify the selection.",
        "Apply the API decision guide and provide per-headline API mappings with non-hand-wavy rationale.",
        "Specify prompt pack, schema-driven structured outputs, parsing/validation, and guardrail behavior.",
        "Describe walkthrough implementation mechanics (highlighting, step model, auto-start/retrigger).",
        "WalkthroughImplementation must include an explicit state machine model (states, transitions, guards) covering auto-start, next/back, cancel, finish, retrigger, invalid transitions, and step-index bounds safety.",
        "Implement deterministic synthetic data loading and first-run auto-population with reset/rerun controls.",
        "Map each headline capability to prompts, walkthrough steps, and tests using stable identifiers.",
        "Require a top-level tooling plan that stays consistent with prior phase tooling decisions.",
        "OpenAIIntegration must include request_validation with concrete preflight checks, fail-fast behavior, UI error state contract, and a debug logging policy that never persists sensitive content.",
        "TestingStrategy must include openai_test_tiers: mocked tests for request formation/parsing/guardrails/tool-call display (when applicable), plus opt-in live smoke tests proving real request success, parse success, and UI/state updates.",
        "Mandate a concrete testing strategy: tests written alongside implementation, run continuously during build, and failures block completion.",
        "Testing output must include per-module plan, acceptance-scope limits to headline items, explicit mocking instructions, and verifiable test commands.",
        "TestingStrategy must include a dedicated deterministic walkthrough test suite covering auto-start, next/back, cancel, finish, retrigger, bounds safety, highlight target resolution, and per-step present/visible/enabled checks for intended UI components.",
        "TestingStrategy must include interaction_test_matrix where each DemoSpec control_id has deterministic tests proving enabled => observable UI/state change, disabled => explicit disabled explanation, and loading behavior when applicable.",
        "Do not write vague testing language.",
        "Keep stack guidance as compatibility constraints, not framework mandates.",
    ),
}

_PHASE_PRIORITY_CHECKLIST: dict[str, tuple[str, ...]] = {
    "feature_spec": (
        "Identify 1-3 headline AI capabilities and keep all scope bounded to them.",
        "Define guardrails summary (off-topic, unsafe/disallowed, allowed, refused behavior).",
        "Set stable capability identifiers that later phases will reuse.",
        "Assess tool necessity explicitly; tools are allowed only when necessary.",
    ),
    "demo_spec": (
        "Map headline capabilities into minimalist views and headline demo items.",
        "Specify interactive walkthrough (auto-start on launch, retrigger path, cancellable controls).",
        "Provide synthetic seed data, default first-run inputs, and expected first-run outputs.",
        "Include interaction_contracts for each minimalist view: enumerate every control with behavior + observable change + enable/disable + loading UI.",
        "Ensure screen_name matches DemoExperience.minimalist_views[*].name and contracts cover all views (no omissions).",
        "Delineate AI vs non-AI components and where innovation lives.",
        "Provide consistency trace to phase-1 headline capability identifiers.",
        "Keep tooling decision consistent with phase 1.",
        "Confirm system theme support and device framing (smartphone frame only if mobile-like).",
    ),
    "code_spec": (
        "Choose OpenAI API(s) and initial prompts aligned to headline items.",
        "If any headline item is voice, include Realtime.",
        "If any headline item requires iterative tool-use/planning, include Agents.",
        "Otherwise default to Responses.",
        "Map each headline item to selected API(s) and justify the mapping.",
        "Define structured output schemas, parsing/validation, and post-processing at the AI seam.",
        "Include WalkthroughImplementation.state_machine_model with explicit states/transitions for auto-start, next/back, cancel, finish, retrigger, invalid transitions, and bounds safety.",
        "Specify synthetic data implementation for deterministic first launch and reruns.",
        "Provide per-headline implementation mapping that matches demo-spec capability identifiers.",
        "Keep tooling plan consistent with earlier phases and explain tool-call visibility in UI.",
        "Include OpenAIIntegration.request_validation (preflight checks, fail-fast UI errors, and safe debug logging with no sensitive persistence).",
        "Include TestingStrategy.openai_test_tiers (mocked default plus opt-in live smoke tests gated by OPENAI_API_KEY/flag; skipped tests are safe and non-failing).",
        "Specify guardrails, walkthrough implementation approach, and UI constraints.",
        "Include TestingStrategy.walkthrough_test_suite_requirements covering deterministic walkthrough step-through and correct highlight targets with present/visible/enabled checks.",
        "Include TestingStrategy.interaction_test_matrix mapping every control_id_ref to enabled/disabled/loading expectations.",
        "Set interaction_test_matrix.rule to include: Every button clicked triggers an observable state/UI change OR is explicitly disabled with explanation.",
        "Require a testing strategy with module-by-module plan, deterministic mocks, and verification steps with commands.",
        "State that acceptance scope is limited to headline items and excludes plumbing criteria.",
    ),
}


def build_phase_prompts(
    *, phase: PipelinePhaseDefinition, phase_input: BaseModel
) -> tuple[str, str]:
    """Build developer + user prompts for one structured phase execution."""
    schema_json = openai_compatible_schema(phase.output_model.model_json_schema())
    schema_excerpt = schema_excerpt_json(schema_json)
    input_payload = json.dumps(phase_input.model_dump(mode="json"), indent=2, sort_keys=True)

    developer_prompt = build_phase_developer_prompt(phase)
    user_prompt = build_phase_user_prompt(
        phase=phase,
        schema_excerpt=schema_excerpt,
        input_payload=input_payload,
    )
    return developer_prompt, user_prompt


def build_phase_developer_prompt(phase: PipelinePhaseDefinition) -> str:
    """Build phase-aware developer instructions with anti-drift constraints."""
    phase_rules = _PHASE_RULES.get(phase.key, ())
    rule_lines = [f"{idx}. {rule}" for idx, rule in enumerate(_GLOBAL_HARD_RULES, start=1)]
    phase_start = len(rule_lines) + 1
    rule_lines.extend(
        f"{phase_start + idx}. {rule}" for idx, rule in enumerate(phase_rules, start=0)
    )
    rules_block = "\n".join(rule_lines)
    api_guide_block = ""
    if phase.key == "code_spec":
        api_guide_lines = "\n".join(f"- {line}" for line in _PHASE3_API_DECISION_GUIDE)
        api_guide_block = f"\nAPI decision guide:\n{api_guide_lines}\n"

    return (
        "You are an expert product-to-engineering planning assistant.\n"
        f"Objective: {phase.objective}\n"
        f"Phase key: {phase.key}\n"
        "Hard rules:\n"
        f"{rules_block}\n"
        f"{api_guide_block}"
        "Return JSON only."
    )


def build_phase_user_prompt(
    *, phase: PipelinePhaseDefinition, schema_excerpt: str, input_payload: str
) -> str:
    """Build phase-aware user payload framing with concise priority checklist."""
    checklist = _PHASE_PRIORITY_CHECKLIST.get(phase.key, ())
    checklist_lines = "\n".join(f"- {item}" for item in checklist)

    return (
        f"Phase key: {phase.key}\n"
        f"Phase title: {phase.title}\n\n"
        "Priority checklist (must satisfy all):\n"
        f"{checklist_lines}\n\n"
        "Output schema (source of truth):\n"
        f"```json\n{schema_excerpt}\n```\n\n"
        "Input payload:\n"
        f"```json\n{input_payload}\n```\n\n"
        "Anti-drift reminders:\n"
        "- Return one JSON object matching schema exactly.\n"
        "- Do not add fields.\n"
        "- Do not introduce plumbing.\n"
        "- Do not use vague test language; provide concrete targets, mocks, and verification steps.\n"
        "- Keep scope limited to the same 1-3 headline items.\n\n"
        "Return JSON only."
    )


def schema_excerpt_json(schema_json: dict[str, Any]) -> str:
    """Render a concise schema excerpt to reduce prompt size while preserving constraints."""
    properties = schema_json.get("properties") if isinstance(schema_json, dict) else None
    required = schema_json.get("required") if isinstance(schema_json, dict) else None
    defs = schema_json.get("$defs") if isinstance(schema_json, dict) else None
    excerpt = {
        "title": schema_json.get("title") if isinstance(schema_json, dict) else None,
        "type": schema_json.get("type") if isinstance(schema_json, dict) else None,
        "required": required if isinstance(required, list) else [],
        "properties": properties if isinstance(properties, dict) else {},
    }
    if isinstance(defs, dict):
        excerpt["$defs"] = defs
    return json.dumps(excerpt, indent=2, sort_keys=True)


def openai_compatible_schema(schema_json: dict[str, Any]) -> dict[str, Any]:
    """Ensure generated JSON Schema satisfies strict response_format constraints.

    OpenAI Responses API requires:
    - additionalProperties: false on objects
    - every object schema to have 'required' including every key in 'properties'
    - $ref must be the sole keyword (no description, title, etc. alongside $ref)

    Assumption: schema traversal is recursive across standard JSON Schema container
    keys (properties/$defs/items/allOf/anyOf/oneOf/if-then-else). Unknown custom
    keywords are left untouched.
    """
    normalized = copy.deepcopy(schema_json)
    enforce_no_additional_properties(normalized)
    enforce_required_includes_all_properties(normalized)
    strip_keywords_from_refs(normalized)
    return normalized


def strip_keywords_from_refs(node: object) -> None:
    """Remove keywords like description from schema objects that contain $ref."""
    if isinstance(node, dict):
        if "$ref" in node and len(node) > 1:
            # $ref cannot have sibling keywords; keep only $ref
            ref = node["$ref"]
            node.clear()
            node["$ref"] = ref

        for key in ("properties", "$defs", "definitions", "patternProperties"):
            value = node.get(key)
            if isinstance(value, dict):
                for child in value.values():
                    strip_keywords_from_refs(child)

        for key in ("items", "additionalItems", "contains", "if", "then", "else", "not"):
            if key in node:
                strip_keywords_from_refs(node[key])

        for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
            value = node.get(key)
            if isinstance(value, list):
                for child in value:
                    strip_keywords_from_refs(child)

    elif isinstance(node, list):
        for child in node:
            strip_keywords_from_refs(child)


def enforce_required_includes_all_properties(node: object) -> None:
    """Ensure every object schema has required=[...all property keys...]."""
    if isinstance(node, dict):
        node_type = node.get("type")
        if node_type == "object":
            props = node.get("properties")
            if isinstance(props, dict) and props:
                # OpenAI requires: required must include every key in properties
                required = set(node.get("required") or [])
                required.update(props.keys())
                node["required"] = sorted(required)

        for key in ("properties", "$defs", "definitions", "patternProperties"):
            value = node.get(key)
            if isinstance(value, dict):
                for child in value.values():
                    enforce_required_includes_all_properties(child)

        for key in ("items", "additionalItems", "contains", "if", "then", "else", "not"):
            if key in node:
                enforce_required_includes_all_properties(node[key])

        for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
            value = node.get(key)
            if isinstance(value, list):
                for child in value:
                    enforce_required_includes_all_properties(child)

    elif isinstance(node, list):
        for child in node:
            enforce_required_includes_all_properties(child)


def enforce_no_additional_properties(node: object) -> None:
    """Recursively set `additionalProperties` false on all object schema nodes."""
    if isinstance(node, dict):
        node_type = node.get("type")
        if node_type == "object":
            node["additionalProperties"] = False

        for key in ("properties", "$defs", "definitions", "patternProperties"):
            value = node.get(key)
            if isinstance(value, dict):
                for child in value.values():
                    enforce_no_additional_properties(child)

        for key in ("items", "additionalItems", "contains", "if", "then", "else", "not"):
            if key in node:
                enforce_no_additional_properties(node[key])

        for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
            value = node.get(key)
            if isinstance(value, list):
                for child in value:
                    enforce_no_additional_properties(child)

    elif isinstance(node, list):
        for child in node:
            enforce_no_additional_properties(child)
