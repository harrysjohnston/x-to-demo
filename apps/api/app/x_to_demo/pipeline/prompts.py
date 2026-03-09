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
    "If the demo needs example text/image/audio assets, they must be synthetic, generated via appropriate OpenAI APIs, stored in-repo, and explicitly labeled synthetic in the UI; do not source ad-hoc internet assets.",
    "Demo startup must not depend on live asset generation; required synthetic assets must already exist in-repo and be validated by tests.",
    "Synthetic demo inputs are global selectable presets that populate UI state only; presets must never auto-run the main flow on launch.",
    "Presets must be integration-tested during build by applying each preset, running guardrails, and verifying main-flow reachability in mocked-by-default tests.",
    "Guardrails must be designed to avoid false rejects on intentional pathways: every happy-path must have at least one preset, and all presets must be treated as in-scope by relevance guardrails.",
    "All runtime inputs, including preset-applied inputs, must pass server-side guardrails before any main AI call.",
    "Guardrails pipeline order is mandatory: deterministic type/format/size checks, relevance model call with structured output, then safety model call with structured output.",
    "Guardrail rejects must return a user-visible verdict message and cancel the flow before the main AI call.",
    "On any guardrail reject (unsupported/off-topic/unsafe), the UI must display the guardrail model's user_message (with brief reasoning and a next step) near the input area; never show a generic blocked message.",
    "Keep specs demo-specific (modalities, runtime flow, UX outcomes) and keep demo-agnostic implementation defaults in .agents/skills.",
    "Keep tooling decisions consistent across phases; do not introduce tools later if earlier phase output says no tools.",
    "Preserve stable headline capability identifiers across phases.",
    "No inert buttons: every interactive element must have defined behavior and automated test coverage.",
    "Validate every OpenAI request before sending (model name, required fields, strict schema constraints) and fail fast with a clear UI-visible error message; no silent failures.",
    "CodeSpec must include two-tier OpenAI tests: mocked tests run by default and low-cost live smoke tests are opt-in only when OPENAI_API_KEY (and optional explicit flag) is set; every planned model call (guardrails + main per headline) must have its own live integration test; skipped live tests must not fail the default suite.",
    "Output one valid JSON object that matches the schema exactly.",
    "Do not add fields, wrappers, markdown, or prose outside schema fields.",
    "Do not invent acceptance criteria or requirements beyond the provided schema and input.",
)

_PHASE3_API_DECISION_GUIDE: tuple[str, ...] = (
    "Responses API: choose for request/response interactions (text or multimodal), simple tool calls, structured outputs, and minimal orchestration.",
    "Realtime API: choose when the demo includes live audio (voice input/output), low-latency streaming UX, or turn-taking. For voice/audio input, the primary capture method must be push-to-record (press-and-hold or explicit start/stop button); do not use auto-recording, background capture, or file-upload-only as the primary path.",
    "Agents SDK: choose when multi-step tool loops, planning, stateful agent behavior, retries, background tasks, memory, or multi-tool orchestration are required.",
    "Must map each headline demo item to selected API(s) and justify each mapping.",
)

_PHASE_RULES: dict[str, tuple[str, ...]] = {
    "feature_spec": (
        "Select one to three headline AI capabilities and center the artifact around them.",
        "Define guardrails summary and a tooling need assessment with explicit yes/no reasoning.",
        "Guardrails summary must explicitly define unsupported input type short-circuit semantics, including user-visible messaging and flow cancellation.",
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
        "Interaction contracts must explicitly include global preset selector, apply preset, run/submit, and reset/clear controls.",
        "Confirm system theme support and conditional smartphone framing behavior.",
        "Define synthetic demo inputs as global presets with a default selected preset id, explicit apply behavior (populate only), and explicit run behavior (requires user action).",
        "DemoSpec must include runtime_input_and_guardrails with supported modalities, input capture summary, type/relevance/safety pipeline summary, reject outcomes, and explicit cancel-flow behavior. When supported_input_modalities includes voice or audio, input_capture_summary must describe push-to-record (press-and-hold or explicit start/stop) as the primary capture method.",
        "Runtime guardrails must apply identically to manual runtime inputs and preset-applied inputs.",
        "Every happy-path flow must be represented by at least one preset; collectively, presets must cover all planned flows and must be treated as in-scope by relevance guardrails.",
        "Runtime guardrail rejects must show the guardrail verdict user_message (brief reasoning + next step) in the input panel and keep user input editable for retry.",
        "SyntheticDemoInputs must include required_assets listing needed text/image/audio assets for seeded scenarios or example uploads, with purpose, where-used mapping, format/size constraints, and explicit synthetic labeling; when none are needed, required_assets must be an empty list.",
        "Preset data must be inspectable: short ordered_inputs per field, structured expected_outputs (EmbeddedDataObject when applicable), concise notes.",
        "Provide explicit consistency trace back to phase-1 capability identifiers.",
        "Carry forward tooling decision from phase 1 without contradiction.",
    ),
    "code_spec": (
        "Select at least one OpenAI API from responses, realtime, agents and justify the selection.",
        "Apply the API decision guide and provide per-headline API mappings with non-hand-wavy rationale.",
        "Specify prompt pack, schema-driven structured outputs, parsing/validation, and guardrail behavior.",
        "CodeSpec must include a server-side runtime guardrails plan with exactly two model calls in this order: relevance verdict first, safety verdict second.",
        "Relevance guardrail prompt must include an explicit in-scope allowlist derived from the demo's presets/happy-path flows; reject only clearly out-of-scope inputs to avoid blocking intentional pathways.",
        "Runtime guardrails plan must include deterministic type/format/size checks and structured-output contract strings for RelevanceVerdict and SafetyVerdict.",
        "Verdict handling must map unsupported vs blocked vs allowed outcomes with user-visible messaging and guaranteed cancel semantics before the main model call when rejected.",
        "On any guardrail reject, server must return the guardrail verdict user_message to the client and the UI must display it in the input panel.",
        "Describe walkthrough implementation mechanics (highlighting, step model, auto-start/retrigger).",
        "WalkthroughImplementation must include an explicit state machine model (states, transitions, guards) covering auto-start, next/back, cancel, finish, retrigger, invalid transitions, and step-index bounds safety.",
        "Implement deterministic synthetic preset loading with explicit apply-only behavior and separate run/reset controls.",
        "Map each headline capability to prompts, walkthrough steps, and tests using stable identifiers.",
        "Require a top-level tooling plan that stays consistent with prior phase tooling decisions.",
        "CodeSpec must include agent_skills_to_apply, including runtime-input-guardrails-server-side, synthetic-input-presets, canonical-spec-format-parity, generated-output-badge, and openai-live-integration-tests; when voice/audio or image input is used, include multimodal-inputs.",
        "CodeSpec must include asset_generation_plan mapping required asset modalities to OpenAI API/model choices, generation scripts/commands, repo storage and naming, app load/reference behavior, synthetic UI labeling, guardrails, and no_live_generation_on_startup=true.",
        "OpenAIIntegration must include request_validation with concrete preflight checks, fail-fast behavior, UI error state contract, and a debug logging policy that never persists sensitive content.",
        "TestingStrategy must include synthetic_assets_validation covering repo-path existence, file sanity checks (type/extension, non-zero size, size limits), and proof that seeded startup runs without live generation calls.",
        "TestingStrategy must include preset_inputs_integration_coverage proving presets are applied, pass guardrails, and reach main-flow execution in mocked-by-default tests; optional live smoke may run a minimal preset subset.",
        "TestingStrategy must include openai_test_tiers: mocked tests for request formation/parsing/guardrails/tool-call display (when applicable), plus opt-in live smoke tests. Every planned OpenAI model call (relevance guardrail, safety guardrail, main call per headline) must have its own live integration test.",
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
        "Define guardrails summary (unsupported type, off-topic, unsafe/disallowed, allowed, refused behavior).",
        "Specify unsupported-input short-circuit behavior with user-visible messaging and flow cancellation.",
        "Set stable capability identifiers that later phases will reuse.",
        "Assess tool necessity explicitly; tools are allowed only when necessary.",
    ),
    "demo_spec": (
        "Map headline capabilities into minimalist views and headline demo items.",
        "Specify interactive walkthrough (auto-start on launch, retrigger path, cancellable controls).",
        "Define global synthetic presets with explicit selector/apply/run/reset UX; applying presets populates UI only and never auto-runs.",
        "Include runtime_input_and_guardrails with server-side type/relevance/safety stages, reject outcomes, and cancel-flow behavior. When voice or audio is a supported modality, input_capture_summary must state that push-to-record is the primary capture method.",
        "Ensure preset-applied inputs and manual runtime inputs pass through the same guardrails.",
        "Ensure every happy-path flow has at least one preset; presets collectively cover all planned flows and must pass guardrails.",
        "Ensure guardrail rejects display the guardrail verdict user_message (brief reasoning + next step) in the input panel.",
        "Include interaction_contracts for each minimalist view: enumerate every control with behavior + observable change + enable/disable + loading UI.",
        "Ensure interaction_contracts include preset selector, apply preset, run/submit, and reset/clear controls.",
        "Populate synthetic_demo_inputs.required_assets (or empty list) with asset_type, purpose, where-used mapping, format/size constraints, and explicit synthetic labeling.",
        "Ensure preset data is inspectable (short inputs, structured expected_outputs, concise notes).",
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
        "Include a server-side runtime guardrails plan with deterministic type checks plus exactly two model calls (relevance, then safety) using structured outputs.",
        "Define structured verdict contracts for relevance and safety guardrail calls, plus explicit reject handling and cancellation semantics.",
        "Ensure relevance guardrails are calibrated to allow all preset-defined happy-path flows; pass an explicit in-scope allowlist derived from presets/happy paths to the relevance model call.",
        "Define structured output schemas, parsing/validation, and post-processing at the AI seam.",
        "Include WalkthroughImplementation.state_machine_model with explicit states/transitions for auto-start, next/back, cancel, finish, retrigger, invalid transitions, and bounds safety.",
        "Specify synthetic preset implementation where default selection/apply populates UI only and run requires explicit action.",
        "Include asset_generation_plan (API/model per modality, generation scripts/commands, repo storage + naming, app load/reference, UI synthetic labels, guardrails, no_live_generation_on_startup=true).",
        "Include agent_skills_to_apply with runtime-input-guardrails-server-side, synthetic-input-presets, canonical-spec-format-parity, generated-output-badge, and openai-live-integration-tests; when voice/audio or image input is used, include multimodal-inputs.",
        "Provide per-headline implementation mapping that matches demo-spec capability identifiers.",
        "Keep tooling plan consistent with earlier phases and explain tool-call visibility in UI.",
        "Include OpenAIIntegration.request_validation (preflight checks, fail-fast UI errors, and safe debug logging with no sensitive persistence).",
        "Include TestingStrategy.openai_test_tiers (mocked default plus opt-in live smoke tests gated by OPENAI_API_KEY/flag; one live test per planned model call; skipped tests are safe and non-failing).",
        "Include testing_strategy.preset_inputs_integration_coverage covering all presets through guardrails and mocked main-flow reachability.",
        "Specify guardrails, walkthrough implementation approach, and UI constraints.",
        "Include TestingStrategy.walkthrough_test_suite_requirements covering deterministic walkthrough step-through and correct highlight targets with present/visible/enabled checks.",
        "Include TestingStrategy.interaction_test_matrix mapping every control_id_ref to enabled/disabled/loading expectations.",
        "Include testing_strategy.synthetic_assets_validation (existence + file sanity + startup independence).",
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
