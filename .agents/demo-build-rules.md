# Demo Build Rules
## How to Use These Rules (CANONICAL)

**Intended audiences**
- **Spec author (Phase 1/2/3 artifact author):** Use these rules to produce a single, schema-valid artifact that is behavior-first, testable, and traceable.
- **Implementer (demo builder):** Use these rules to translate the spec into a deterministic, test-covered demo with correct guardrails, presets, and UX.
- **Reviewer (PR/spec reviewer):** Use these rules to check scope discipline, traceability, and that tests prove the claimed behaviors.

**Phase-by-phase procedure (recommended reading order)**
1. **Interpretation + contract:** Read **Purpose & Output Contract** and **How to Interpret Rules: Rule Types, Precedence, and Verdict Terms** so you can correctly interpret rule strength, terminology, and conflict resolution.
2. **Navigate by topic:** Use **Canonical Anchors (Quick Index; Primary Navigation)** to find the single canonical home for any requirement.
3. **Phase 1 (FeatureSpec):** Lock scope to **1–3 headline capabilities**, define acceptance criteria, guardrails summary, and tooling need assessment.
4. **Phase 2 (DemoSpec):** Define the in-app UX (views + interaction contracts), presets, guardrails UX semantics, walkthrough state machine, and traceability to tests.
5. **Phase 3 (CodeSpec):** Select APIs/models as needed, implement **AI Seam Validation**, and satisfy the required test tiers.

**Minimal happy path (standard text-only demo)**
- **No tools, no external assets, text input/output only.**
- Ship at least **one preset per headline demo flow**, run guardrails server-side, show a generated-output indicator, provide an in-app walkthrough, and prove it all with mocked-by-default tests.

**Optional modules (only when needed)**
- **Tools:** Use only when Phase 1 says tools are needed; keep tool calls/results UI-visible and testable.
- **Assets:** Only if required; store synthetic assets in-repo; never generate assets live on startup.
- **Multimodal (voice/image):** Add only when required; follow modality state machines, allowlists, feasibility fallbacks, and tests.

**Navigation aids**
- Use **Canonical Anchors (Quick Index; Primary Navigation)** to find the single canonical rule for any topic.
- Use **Quick Build/Review Checklist** for fast review passes.
- See **Glossary** for internal terms and acronyms.

## Purpose & Output Contract (CANONICAL)

These rules define the standard procedure to produce **one phase artifact JSON** (Phase 1 FeatureSpecArtifact, Phase 2 DemoSpecArtifact, Phase 3 CodeSpecArtifact) that is **behavior-first, testable, and traceable**.

**Output contract**
- Output exactly **one** schema-valid JSON object for the active phase (no wrappers/markdown/prose; no extra fields).
- Stay within scope: **1–3** headline capabilities/demo items with stable identifiers; do not add extra features beyond schema + provided inputs.
- Specify externally observable behavior: inputs, outputs, UI states, errors, and guardrails UX.
- Provide testable acceptance criteria linked via capability_ref and ensure cross-section consistency (views ↔ interaction_contracts ↔ presets ↔ guardrails ↔ walkthrough ↔ tests).
- Record excluded plumbing, invariants, success_metrics, and (when applicable) a tooling need assessment.

For rule strength, conflict resolution, and canonical guardrails verdict terminology, use **How to Interpret Rules: Rule Types, Precedence, and Verdict Terms**.

## How to Interpret Rules: Rule Types, Precedence, and Verdict Terms (CANONICAL)

**Rule types (strength and intent)**
- **CANONICAL:** Normative, testable requirements (anchored to a schema field and/or a named test expectation).
- **POINTER:** Non-normative navigation to the canonical anchor; do not restate requirements.
- **REFERENCE:** Informational notes, indexes, and examples; no new normative requirements.

**Conflict resolution / precedence (use this whenever rules appear to disagree)**
1. The active phase artifact JSON schema + explicit user input
2. Cross-phase consistency constraints (feature_name, capability_ref, tooling consistency)
3. Safety/guardrails requirements
4. This build-rules document

If a deviation is necessary, document it in spec notes and/or code comments.

**Guardrails verdict terminology (canonical vocabulary)**
- **unsupported:** Deterministic validation failure (type/format/size/decode); hard short-circuit with zero model calls.
- **blocked:** Relevance fail (out-of-scope/off-topic) OR safety fail (disallowed/unsafe); zero main-model calls.
- **allowed:** Only when both relevance and safety pass; main model may be called.

Use **blocked** as the canonical reject verdict term in specs/tests/UX expectations; if UI copy uses the word **refused**, it must map to **blocked**.

## Primary Navigation (POINTER)

- Start with **How to Use These Rules (CANONICAL)** for the phase-by-phase procedure and the minimal text-only happy path.
- Interpret rule strength, resolve conflicts, and apply consistent guardrails terminology via **How to Interpret Rules: Rule Types, Precedence, and Verdict Terms (CANONICAL)**.
- For any topic, jump to the single canonical home via **Canonical Anchors (Quick Index; Primary Navigation)**.
- For fast review passes, use **Quick Build/Review Checklist (Reference; Primary Navigation, No New Requirements)**.
- For internal terms/acronyms, use **Glossary (Reference)**.
- For the end-to-end execution model, see **Traceability Walkthrough (Example; Reference)**.

## Canonical Anchors (Quick Index; Primary Navigation)

- **Interpretation + precedence + verdict terms:** How to Interpret Rules: Rule Types, Precedence, and Verdict Terms.
- **Phase 1 grounding + scope boundary:** Phase 1 (FeatureSpecArtifact) Core Requirements; Phase 1 Output Format.
- **Phase linkage + metadata + stable identifiers:** Phase Linkage, Grounding, and Metadata.
- **UI/UX + interaction contracts:** UI/UX + Interaction Contracts; DemoSpecArtifact Schema Guidance; Minimalist Views.
- **Walkthrough state machine + tests:** Walkthrough; Walkthrough State Machine Model; Walkthrough Test Suite.
- **Presets + synthetic inputs + asset ownership:** Presets, Synthetic Data, and Assets; Preset Coverage; Preset Shipping Gate; Synthetic Assets; Presets (Repo Ownership + Canonical Source; CANONICAL Repo Convention); Synthetic/Seeded Input Labeling; Synthetic Input Compatibility Fields.
- **Runtime inputs + validation + reject UX:** Runtime Inputs, Deterministic Validation, and Guardrails; Guardrails Pipeline; Deterministic Validation & Guardrails; Edge Cases, Feasibility, and Waivers.
- **OpenAI/tooling + live-test ops:** OpenAI + Tooling Integration; Tools + Tooling; AI Seam Validation; CodeSpec OpenAI Testing; API Selection; CodeSpec Requirements; OpenAI Model Defaults; OpenAI Credentials; Live Test Run Commands; Pricing / Cost Estimates.
- **Success + testing + traceability:** Success, Output Format, and Testing; Testing Standard; Traceability Walkthrough.
- **Labeling + privacy:** Accessibility, Labeling, Logging, and Privacy; Generated Output Labeling; Labeling Systems Clarification; Debug/Privacy Logging Policy.
- **Maintenance + editing:** Maintenance, Canonicalization, and Indexes; Editing Guidance and De-Dup Checklist.

## Quick Build/Review Checklist (Reference; Primary Navigation, No New Requirements)

1. **Scope:** 1–3 headline items + no extra features (Scope Boundary + Excluded Plumbing).
2. **Phase grounding + identifiers:** Phase 2 is grounded in Phase 1 with stable `feature_name`/`capability_ref` plus `consistency_trace`.
3. **UI/UX:** minimalist views + interaction contracts + device/theme + async UX.
4. **Presets:** apply/run semantics + repo ownership + coverage + shipping gate + integration tests.
5. **Guardrails:** deterministic validation then relevance then safety, server-side only, reject short-circuit before main call, verdict semantics + rejected-case tests.
6. **AI seam:** request/response validation + schema parsing failures are UI-visible and retryable.
7. **Tools/assets (if any):** tooling plan constraints + UI-visible tool logs + synthetic assets stored in repo/no live gen on startup + asset validation tests.
8. **OpenAI ops:** credentials loader + missing-key UX/tests + model defaults/overrides/tests + live tests opt-in + commands.
9. **Labeling/privacy:** generated indicator + seeded/synthetic labeling + reset/reseed + privacy logging.

**No Line Number References (CANONICAL):** Do not reference line numbers in rules; use section names or topic anchors instead (e.g. "see Scope Boundary + Excluded Plumbing", "see UI/UX + Interaction Contracts").

---

## Phase 1 (FeatureSpecArtifact) Core Requirements (CANONICAL)

Phase 1 defines the product boundary that every later phase must preserve.

- Define exactly 1-3 headline capabilities with stable identifiers, observable behavior, and acceptance criteria that a reviewer can test without guessing intent.
- Record `innovation_focus`, `acceptance_criteria`, `excluded_plumbing`, `invariants`, `success_metrics`, and `tooling_need_assessment` in Phase 1 so later phases stay grounded instead of inventing requirements.
- Keep the artifact behavior-first: describe what the user can observe, not implementation detail or speculative plumbing.
- Use **Phase Linkage, Grounding, and Metadata** plus **Scope Boundary + Excluded Plumbing** as the canonical homes for grounding, identifiers, scope, and carry-forward rules.

---

## Phase Linkage, Grounding, and Metadata (CANONICAL)

### Phase Linkage (CANONICAL)

Treat DemoSpecArtifact as the sole structured Phase 2 input into Phase 3, and produce CodeSpecArtifact as the sole structured Phase 3 output; keep linkage via stable `feature_name` and `capability_ref` identifiers.

### Phase-2 Grounding (CANONICAL)

Treat the Phase-2 input FeatureSpecArtifact as the sole product-requirements source of truth (`feature_name`, `intent`, `external_behavior`, `innovation_focus`, `acceptance_criteria`, `excluded_plumbing`, `invariants`, `success_metrics`). Ground the DemoSpecArtifact strictly in these fields; do not invent additional requirements.

### Consistency Trace (CANONICAL)

In `DemoSpecArtifact.consistency_trace`, include `phase1_headline_capability_refs`, a stable identifier rule that preserves capability identifiers across phases, and a walkthrough alignment summary confirming the walkthrough covers the same headline capability set with no extras.

### Spec Metadata Hygiene (CANONICAL)

Keep `spec_generation_metadata` separate from product behavior; it must include `schema_version`, `status` (`draft|review|ready`), `source` (`SourceInfo`), and `versioning` (`VersioningInfo` with `version`, `changelog`, and `updated_at_utc`). Update versioning whenever the spec meaningfully changes.

---

## Scope Boundary + Excluded Plumbing (CANONICAL)

### Scope Boundary + Preset Reachability (CANONICAL)

Treat the scope limit as 1-3 headline capabilities or demo items and require every planned demo flow to be reachable via shipped presets and verified by tests.

### Out-of-Scope / Excluded Plumbing (CANONICAL)

Exclude non-essential plumbing unless explicitly required by schema or input and carry Phase 1 `excluded_plumbing` forward consistently into Phase 2.

### Spec Hygiene & Ownership (POINTER)

Use the canonical de-dup and ownership rules in **Phase 1 (FeatureSpecArtifact) Core Requirements** and **Maintenance, Canonicalization, and Indexes**.

---

## UI/UX + Interaction Contracts (CANONICAL)

### No Inert UI (CANONICAL)

Every interactive element must have defined behavior and automated test coverage; no inert buttons or controls.

### Minimalist Views (POINTER)

Use **Minimalist Views** as the canonical home for visible vs hidden UI inventory.

### Interaction Contracts (CANONICAL)

Define `interaction_contracts` for every minimalist view and keep them schema-complete (see **DemoSpecArtifact Schema Guidance**). Ensure `interaction_contracts.screen_name` matches `minimalist_views[*].name`.

Interaction contracts must include a global preset selector visible in the primary input area, plus apply preset, run/submit, and reset/clear. The selector must have an explicit `control_id` and `label_or_icon_description`. Seeded/synthetic reset/reseed semantics and labeling are canonical in **Synthetic/Seeded Input Labeling**.

### Device Target + Theme Support (CANONICAL)

Keep system dark/light theme support and any `device_target` or `smartphone_frame` behavior consistent with `demo_experience`; do not restate the same constraints in multiple sections.

---

## Walkthrough (CANONICAL; In-App Tour State Machine, Not a Script)

### Walkthrough Definition (CANONICAL)

Interpret "walkthrough" as an in-app interactive UI tour that auto-starts, can be retriggered, can be cancelled, and is implemented as a bounded state machine rather than a presenter script.

### Walkthrough State Machine Model (CANONICAL)

In `DemoSpecArtifact.interactive_walkthrough`, include an explicit `walkthrough_state_machine` with states, transitions, guards, and invalid-transition handling for auto-start, next/back navigation, cancel-anytime, finish, retrigger, and step-index bounds safety. Treat highlight-target resolution failures as retryable errors rather than stuck states.

### Walkthrough Test Suite (CANONICAL)

Add deterministic tests covering auto-start, next/back, cancel, finish, retrigger, bounds safety, highlight-target resolution, and per-step present, visible, and enabled checks.

---

## Presets, Synthetic Data, and Assets (CANONICAL Overview)

### Presets (Semantics) (CANONICAL)

Presets are required for happy paths and must follow apply/run semantics: apply = populate UI state only (no side effects); run/submit = explicit user action that triggers guardrails then main flow. No auto-run on launch. On startup, auto-select and apply the default preset by populating inputs only.

### Presets (Build Integration Tests) (CANONICAL)

Mocked-by-default integration-test presets during build: iterate each preset; apply(populate-only) -> run(guardrails then main flow); assert guardrails allow happy-path presets; assert each preset reaches main-flow execution and produces the preset's expected output and/or expected UI state (as defined in the preset spec). Include at least one rejected-case test asserting zero main-model calls when guardrails reject (see Deterministic Validation & Guardrails).

### Preset Coverage (CANONICAL)

Ensure every planned demo flow is reachable via at least one shipped preset. Collectively, presets must exercise all headline demo items and all main or guardrail-allow happy paths.

### Preset Shipping Gate (CANONICAL)

Do not ship or merge a demo with presets unless all presets pass the required mocked-by-default integration-test tier. Live-tier preset tests, if added, remain optional and opt-in or skip-gated.

### Synthetic Assets (CANONICAL)

If any example text, image, or audio assets are required, generate them via appropriate OpenAI APIs or scripts, store them in-repo, label them synthetic in the UI, and validate them via automated tests. If no assets are needed, `required_assets` must be empty.

### Preset/Data Ownership (POINTER)

Use **Presets (Repo Ownership + Canonical Source; CANONICAL Repo Convention)** for repo layout and authoring conventions.

### Synthetic/Seeded Input Labeling (POINTER)

Use **Synthetic/Seeded Input Labeling** and **Synthetic Input Compatibility Fields** for labeling, reset/reseed, and compatibility behavior.

---

## Runtime Inputs, Deterministic Validation, and Guardrails (CANONICAL Overview)

### Guardrails Pipeline (CANONICAL)

All inputs (including presets) are decided server-side only. Enforce deterministic validation -> relevance -> safety with reject short-circuit before any main model call. Pipeline limits: deterministic validation makes 0 model calls on fail; then exactly two structured-output guardrail calls (relevance then safety) using strict JSON schemas (`additionalProperties=false`); no extra guardrail calls or free-form verdicts. UX: keep inputs editable; display the guardrail verdict `user_message` near the input; provide retry; `cancel_flow_behavior` must cancel before the main model call.

- **Voice/Audio Capture (POINTER):** If voice/audio is supported, follow **Audio**, **Guardrails Pipeline**, and **Input Hardware Feasibility**; do not restate capture semantics elsewhere.
- **Deterministic Validation + Guardrails Detail (POINTER):** Use **Deterministic Validation & Guardrails** for strict schemas, pre-model validation, logging, and rejected-path test expectations.
- **Input Hardware Feasibility (POINTER):** Use **Input Hardware Feasibility** in **Edge Cases, Feasibility, and Waivers** for hardware absence, retryable UX, and fallback rules.
- **Runtime Input Summarization (POINTER):** Use **Runtime Input Summarization** in **Edge Cases, Feasibility, and Waivers** for safe `runtime_input_summary` rules.

### Traceability + AI/Non-AI Delineation (POINTER)

Use **Phase Linkage, Grounding, and Metadata** for stable identifiers and `consistency_trace`, **Traceability Walkthrough (Example; Reference)** for the intended mapping chain, and `ai_pipeline_delineation` for the explicit AI/non-AI split.

---

## OpenAI + Tooling Integration (CANONICAL Overview)

### Tools + Tooling (POINTER; Single Source of Truth)

Define and justify tools only via `DemoSpec tooling_decision_trace` plus `tooling_plan_if_needed`, grounded in Phase 1 `tooling_need_assessment`. Tool calls and results must be UI-visible, testable, and governed by the same guardrails, async UX, error handling, and **AI Seam Validation**.

### AI Seam Validation (CANONICAL; see Glossary: AI seam)

Treat the AI seam as schema-driven: preflight-validate every OpenAI request before sending, parse and validate every structured response, and fail fast with clear UI-visible, retryable errors on validation or parse failures.

### API Selection (POINTER)

Use **API Selection** and **CodeSpec Requirements** for downstream API mapping, prompt packs, fallback models, and per-headline-item API rationale.

### CodeSpec OpenAI Testing (CANONICAL)

Use a two-tier strategy: mocked-by-default tests run in CI; `LiveSmokeTestTier` is opt-in only when `OPENAI_API_KEY` is set and `RUN_LIVE_OPENAI_TESTS=="1"`. `LiveSmokeTestTier` must set `opt_in=true` and include `run_condition`, `skip_behavior`, `cost_and_safety_constraints`, `what_it_verifies`, and `commands_or_how_to_run`. Provide exactly one live integration test per planned OpenAI model call (2 guardrails + each main model call per headline item); enumerate planned calls first and compute required live tests = 2 + (# headline items). Skipped live tests must not fail the default suite.

### OpenAI Operations (POINTER)

Use **OpenAI Model Defaults**, **OpenAI Credentials**, **Live Test Run Commands**, and **Pricing / Cost Estimates** as the canonical ops anchors.

### Required Assets Fields (POINTER)

If `synthetic_demo_inputs.required_assets` is non-empty, include stable asset ids, types, purposes, format and size constraints, and explicit in-app synthetic labeling requirements. Canonical anchors: **Synthetic Assets** and `asset_generation_plan`.

---

## Success, Output Format, and Testing (CANONICAL Overview)

- **Success Signals (POINTER):** Define observable success_signals aligned to each headline demo item; canonical anchor: success_signals and Phase-1 success_metrics where applicable.
- **Output Format (CANONICAL):** Output exactly one valid JSON object matching the required schema (no wrappers/markdown/prose; no extra fields). Do not invent requirements beyond schema + provided artifacts; ensure cross-section consistency (views ↔ interaction_contracts ↔ presets ↔ guardrails ↔ tests) and follow precedence (see How to Interpret Rules: Rule Types, Precedence, and Verdict Terms).
- **Testing Standard (POINTER):** Use **Testing Standard** for full required coverage, command discipline, and stack/tooling constraints.
- **Change Discipline (CANONICAL):** Treat these rules/skills as the source of truth for demo design decisions; record relevant deviations/decisions in spec notes and/or code comments when implementing or changing demos, guardrails, presets, or tests.

---

## Accessibility, Labeling, Logging, and Privacy (CANONICAL Overview)

- **Generated Output Labeling (POINTER):** Use **Generated Output Labeling** as the single canonical home for AI/tool-output indicators.
- **Synthetic/Seeded Input Labeling (POINTER):** Use **Synthetic/Seeded Input Labeling** as the single canonical home for seeded/demo-data labels and reset/reseed behavior.
- **Labeling Non-Conflict (POINTER):** Use **Labeling Systems Clarification** to keep output-labeling vs seeded-input-labeling distinct.
- **Debug/Privacy Logging Policy (POINTER):** Use **Debug/Privacy Logging Policy** and the guardrails logging policy as the canonical privacy anchors.

---

## DemoSpecArtifact Schema Guidance (POINTER; Avoid Schema Restatement)

Use the active DemoSpecArtifact schema as the sole authority for field names, allowed values, and nested shapes; do not restate the schema here.

When authoring DemoSpecArtifact, keep:

- `feature_name` and headline demo items aligned to **Phase Linkage, Grounding, and Metadata** plus **Scope Boundary + Excluded Plumbing**;
- `interaction_requirements`, `interaction_contracts`, and `demo_experience` aligned to **UI/UX + Interaction Contracts**;
- `interactive_walkthrough` aligned to **Walkthrough**;
- runtime-input and guardrails fields aligned to **Runtime Inputs, Deterministic Validation, and Guardrails** plus **Deterministic Validation & Guardrails**;
- `synthetic_demo_inputs`, presets, and any required assets aligned to **Presets, Synthetic Data, and Assets**, **Synthetic/Seeded Input Labeling**, and **Synthetic Input Compatibility Fields**;
- `tooling_decision_trace`, `tooling_plan_if_needed`, and downstream API signals aligned to **OpenAI + Tooling Integration** and **API Selection**;
- `consistency_trace`, `ai_pipeline_delineation`, and innovation framing aligned to **Phase Linkage, Grounding, and Metadata** plus **Traceability Walkthrough (Example; Reference)**.

Keep tooling plans consolidated and reviewable. Avoid duplicating tool definitions across the spec, UI, and tests, and keep one obvious canonical home for the tool plan.

## Generated Output Labeling (CANONICAL; Single System)

Visibly mark every AI- or tool-generated surface with one reusable Generated indicator component (badge/icon + optional "Generated" text) with consistent placement; ensure accessibility (aria-label/role + contrast in light/dark); add automated UI tests asserting every generated-output surface (including tool outputs) shows the indicator.
---

## Multimodal Requirements (CANONICAL Overview)

### Multimodal Change Control (CANONICAL)

When adding or modifying voice, audio, or image input, update DemoSpec and implementation together: capture controls, per-modality state machines, deterministic validation or allowlists, permission and error UX, and tests. If hardware or permission is unavailable, follow **Input Hardware Feasibility** and document any necessary deviations in spec notes or tests.

### Audio (CANONICAL)

Primary capture must be push-to-record and must not auto-record or capture in the background; file-upload-only must not be the primary path. UI must be keyboard and touch accessible and modeled as an explicit state machine with states `{idle, recording, processing, error}` and transitions `idle→recording→processing→idle` with error or cancel paths returning to idle. Disable conflicting controls while recording; provide playback before submit or discard; show a live mic-level visualizer with states `{active, muted, paused, no-permission}`. Permission denial must show exactly: "Microphone access denied. Please allow microphone access and try again." with a retry action. If microphone hardware or permission is unavailable, follow **Input Hardware Feasibility** and cover the fallback by tests. Tests must cover capture semantics, transitions, disabling, playback, and visualizer states.

### Image (CANONICAL)

Primary path must be device camera capture via `getUserMedia` video or equivalent; upload may be secondary but not sole. UI must be keyboard and touch accessible and modeled as an explicit state machine with states `{idle, capturing, processing, error}`; require an inspect or preview step before submit. Permission denial must transition to error with a clear message and retry action. If camera hardware or permission is unavailable, follow **Input Hardware Feasibility** and cover the fallback by tests. Tests must cover primary capture, secondary upload, and preview-before-submit.

### Modality Format + Allowlist (CANONICAL)

Define one per-modality MIME and extension allowlist aligned to the target OpenAI API. When implementing, look up the currently supported formats via MCP (see **Glossary**) and encode them as deterministic allowlists. Use the allowlist consistently for recording, capture, and upload; ensure recorded or captured outputs are already in-allowlist or are converted before sending. Enforce server-side deterministic validation that rejects non-allowlist types with consistent "Unsupported file type" messaging and an unsupported verdict.

---

## Synthetic/Seeded Input Labeling (CANONICAL; Separate from Generated)

If the demo uses any seeded/synthetic inputs/assets/prefilled fields/datasets (including via presets/seed_dataset or programmatically seeded content), label them with exactly one chosen terminology (Example|Demo|Synthetic|Sample) used consistently across the demo. Placement must be context-appropriate and visible: for each seeded/prefilled input field show an adjacent/inline badge/label (or placeholder like "(example)"); for multiple prefilled fields allow a section banner above the form; for seeded datasets/lists/tables show a banner/tag on or above the dataset (and optionally per row/card); for seeded file uploads show a badge near the file name or upload area. Provide a deterministic reset/reseed control placed near the labeled content (or in the relevant toolbar) that restores the exact initial seeded state (not merely "clear all"); its label must be exactly one of: "Reset", "Restore example", "Reload sample", or "Clear and reseed". Add deterministic UI tests that (1) when seeded content is present, the corresponding label/banner/tag using the chosen terminology is visible in the DOM and (2) after edits, reset/reseed restores the exact initial seeded values/state.

---

## Presets (Repo Ownership + Canonical Source; CANONICAL Repo Convention)

Store presets in repo-owned, reviewable, deterministically formatted files with stable `preset_id` values, stable labels, and deterministic field ordering; make preset data easy to scan and review in git diffs; maintain one canonical preset collection per feature referenced by both UI and tests. Recommended default locations: `apps/<surface>/src/presets/` for frontend-owned presets or `apps/api/app/<domain>/presets/` for server-shared presets. Keep `ordered_inputs` short per UI field and notes brief (use `"none"` when absent). Prefer structured `expected_outputs` or `expected_ui_state` using `EmbeddedDataObject` (see **Glossary**) when applicable; use a concise string only for simple single-line expectations.

---

## Async UX + Error Handling (CANONICAL)

Any async request (guardrail/main/tool/backend) must be driven by an explicit status state machine (idle/loading/streaming/success/error/timeout): show immediate loading + explicit "working" copy, support streaming indicators when applicable, disable conflicting controls in-flight, enforce explicit timeouts, and surface clear retryable error/timeout states. See In-flight UI tests.

**In-flight UI tests (mocked-by-default):** add deterministic tests using mocked and/or intentionally delayed responses that verify (1) loading UI + "working" copy appears immediately on request start (within one frame/before any mock delay), (2) controls are disabled during the request and re-enabled after completion, and (3) loading/streaming UI clears on both success and failure/timeout without relying on real network calls.

---

## Phase 1 Output Format (CANONICAL; Avoid Schema Restatement)

Phase 1 must output exactly one valid JSON FeatureSpecArtifact (no wrappers/markdown/prose) and it is the sole product-requirements source of truth for Phase 2 grounding (Phase-2 Grounding).

Define and persist a canonical run-input record (PipelineRunInput) to support resume semantics across Phase 1 runs; capture the raw input, any optional context/hints, and the resolved stable feature_name; populate required fields per the active schema.
*Schema field lists are intentionally omitted here to reduce duplication and drift risk; follow the active Phase 1 schema for required fields, allowed values, and nested object shapes.*
---

## API Selection (CANONICAL; Downstream Only)

Only Phase 2 and Phase 3 artifacts should select among OpenAI APIs. When selection is needed, justify the choice among Responses, Realtime, and Agents SDK (see **Glossary**) and provide per-headline-item API mappings. Default to Responses unless voice or low-latency streaming requires Realtime or iterative tool orchestration requires Agents SDK.

- If any headline demo item includes voice or audio input, or a voice or audio `interaction_mode`, include the Realtime API in the API plan and map those headline items to Realtime with explicit latency and streaming rationale.
- If any headline demo item requires iterative planning or tool-use loops, include the Agents SDK in the API plan and map only those headline items to Agents SDK; otherwise do not add Agents SDK.
- Specify a prompt pack for the demo. For each guardrail call and each headline item, include prompt identifiers, purpose, inputs, and required structured-output schemas; enforce schema-driven structured outputs with deterministic parsing and validation at the AI seam.
- The relevance guardrail prompt must include an explicit in-scope allowlist derived from presets and intended happy-path flows. Relevance should reject only clearly out-of-scope inputs and must treat all shipped presets as in-scope by default.
- Map guardrail outcomes to user-visible messaging and cancel semantics using the canonical verdict taxonomy in **How to Interpret Rules: Rule Types, Precedence, and Verdict Terms** and the behavior in **Guardrails Pipeline**, including returning or displaying the guardrail verdict `user_message` near the input area on any reject.
- Map each headline capability to its prompts or main model call(s), walkthrough step(s), and deterministic tests so traceability is complete and non-redundant.
- Include `agent_skills_to_apply` in the spec and ensure it includes `runtime-input-guardrails-server-side`, `synthetic-input-presets`, `canonical-spec-format-parity`, `generated-output-badge`, and `openai-live-integration-tests`; additionally include `multimodal-inputs` when any voice, audio, or image modality is supported.
- Include an `asset_generation_plan` when any example text, image, or audio assets are used; specify per-modality OpenAI API and model choices, generation scripts or commands, repo storage and naming conventions, app load and reference behavior, UI synthetic labeling, guardrails for asset use, and `no_live_generation_on_startup=true`.
- OpenAI integration must include `request_validation` with concrete preflight checks, fail-fast behavior, and a UI error-state contract exercised by mocked-by-default tests.

---

## Debug/Privacy Logging Policy (CANONICAL)

Logs must never persist sensitive content (user inputs, audio/image bytes, API keys, raw model outputs containing sensitive data). Allow only redacted/hashed identifiers and high-level event metadata needed for debugging; align guardrails/tooling logging with this policy.

---

## Testing Standard (CANONICAL, Scope-Limited)

Testing must be concrete with explicit commands; run continuously during build; any test failure blocks completion. Acceptance scope is strictly the 1–3 headline demo items; exclude plumbing criteria. Required coverage is defined by the canonical topic rules (e.g., presets/tests/gates, **Preset Shipping Gate**; guardrails outcomes + zero-main-call on reject; walkthrough tests; interaction matrix; async UX tests; **AI Seam Validation**; synthetic assets validation if any).

- Testing must include synthetic_assets_validation: verify repo-path existence, file sanity (type/extension, non-zero size, size limits), and proof that startup runs without any live asset generation calls.
- Testing must include preset_inputs_integration_coverage proving presets apply (populate-only), pass guardrails, and reach main-flow execution in mocked-by-default tests; optional live smoke tests may cover only a minimal preset subset.
- Testing must include a deterministic walkthrough test suite covering: auto-start, next/back, cancel, finish, retrigger, bounds safety, highlight-target resolution, and per-step present/visible/enabled checks (aligned to walkthrough state machine rules).
- Testing must include an interaction_test_matrix: for each DemoSpec control_id assert enabled => observable UI/state change; disabled => explicit disabled explanation; include loading behavior assertions when applicable; avoid vague testing language.

Provide stack guidance as compatibility constraints (e.g., browser support, testing tools, build tooling expectations) rather than mandating specific frameworks unless explicitly required by the schema/input.

---

## CodeSpec Requirements (CANONICAL)

CodeSpecArtifact must include its own spec_generation_metadata (kept separate from product behavior content) with schema_version, status (draft|review|ready), source (SourceInfo), and versioning (VersioningInfo) for traceability and change history.

In the CodeSpec OpenAI plan, define a primary model and an ordered list of fallback models per call type (guardrails + each main call), and specify when fallbacks are allowed (e.g., transient errors/overload) without changing required structured-output schemas.

In the CodeSpec API selection section, map each headline demo item to exactly one selected API surface from {responses, realtime, agents} with rationale and an explicit "what would break if swapped" note; explicitly confirm the selection satisfies interaction_requirements.requires_voice and interaction_requirements.requires_tool_loop from the DemoSpec.

---

## Deterministic Validation & Guardrails (CANONICAL Detail)

**Deterministic Validation (before any model call):** Validate per-modality MIME/type allowlist + extension sanity; max payload sizes; modality parsing/decoding checks; audio/image constraints as required; and include an explicit unsupported-modality/format short-circuit path.

If deterministic validation fails, return an unsupported verdict with a user-visible message and perform zero relevance, safety, and main-model calls (hard short-circuit).

Guardrail structured outputs must use these exact schemas (no extra keys): RelevanceVerdict {is_relevant:boolean, reason:string, user_message:string} with all fields required; SafetyVerdict {is_safe:boolean, reason:string, user_message:string} with all fields required; enforce additionalProperties=false and fail the request if parsing/validation fails.

Each guardrail model prompt must use explicit system/developer/user layers and end with an instruction to output JSON only matching the provided schema (no prose/markdown and no additional keys).

**Verdict Handling (POINTER):** Use the single canonical guardrails verdict taxonomy and blocked/refused mapping defined in **How to Interpret Rules: Rule Types, Precedence, and Verdict Terms**; enforce the same short-circuit and zero-main-model-call behavior via **Guardrails Pipeline**.

Guardrails logging policy: never persist raw prompts/responses or sensitive user content; log only request/run id, deterministic validation outcomes, relevance/safety decision labels, per-step timing/latency, and structured-output parse success/failure.

Mocked-by-default tests must cover allowed, unsupported, and blocked outcomes; assert (1) rejected paths return user-visible reject messages, (2) rejected paths trigger zero main-model calls, and (3) deterministic validation failures hard short-circuit and skip all guardrail model calls.

---

## OpenAI Model Defaults (CANONICAL)

Apply these OpenAI model-default rules to any demo that uses OpenAI APIs unless a demo-specific requirement explicitly overrides them.

**Default Model Configuration (CANONICAL, Centralized):** Use gpt-5.2 with reasoning_effort="low" for Responses API + Agents SDK calls and gpt-realtime for Realtime calls; centralize these defaults in one config module/env schema with a single per-demo override point, and ensure all OpenAI call sites read from that centralized config (no hardcoded model/reasoning at call sites).

Expose overrides via environment variables (preferred for deployment flexibility): OPENAI_MODEL and OPENAI_REASONING_EFFORT for Responses/Agents; OPENAI_REALTIME_MODEL for Realtime. Alternatively allow config constants (e.g., config.openai_model, config.reasoning_effort, config.openai_realtime_model) for single-demo config files.

**Model Default Tests (CANONICAL):** Add deterministic tests asserting (1) defaults resolve to model=gpt-5.2, reasoning_effort=low, realtime_model=gpt-realtime when no overrides are set, and (2) override paths work via env patching/config injection; tests must not rely on the ambient environment.

---

## OpenAI Credentials (CANONICAL, Env-First + Single Loader)

Load OPENAI_API_KEY via the framework's standard env-loading mechanism into one shared config module/class used by all OpenAI client code; validate present/non-empty at startup or before the first OpenAI API call and fail fast with a clear, catchable error and (when applicable) a structured HTTP/UI error response (e.g., 400/503) whose message explicitly mentions OPENAI_API_KEY is not configured and how to fix it (no generic 500/unhandled exception); provide .env.example + a README section explaining env-file setup (where to place it: project root/app start directory) and how to run the app; never commit .env (.gitignore); add deterministic tests for both present-key and missing/empty-key behaviors using env patching (no real .env reliance).

---

## Pricing / Cost Estimates (CANONICAL)

When selecting models or estimating cost/tokens, use reference.md (sourced from apps/api/openai_model_pricing.md) as the only authority; treat prices as USD per 1M tokens; when available compute input + cached input + output tokens; bill reasoning tokens as output and account for their context usage; apply cached-input discounts only when supported; treat realtime/audio pricing separately; keep reference.md and apps/api/openai_model_pricing.md in sync.

---

## Phase Linkage + Response Handling (POINTER)

Phase linkage is canonical in **Phase Linkage, Grounding, and Metadata**.

**AI Seam Response Handling (POINTER):** Treat response parsing, validation, normalization, and UI-visible retryable failures as part of the canonical AI seam contract; canonical anchors: request/response validation and strict schema parsing requirements.

**Post-Success UX (Reference):** Optionally show a success confirmation after completion without blocking continued demo use.

---

## Structure Note (CANONICAL)

Use the major thematic headings in this document as the primary navigation; when adding new rules, attach them to the most specific existing topic heading and prefer citing a single canonical anchor (see **Canonical Anchors (Quick Index; Primary Navigation)**) instead of duplicating requirements.

---

## Live Test Run Commands (CANONICAL)

Document at least one copy-pastable command to run live tests (e.g., RUN_LIVE_OPENAI_TESTS=1 OPENAI_API_KEY=... pytest -m live or pytest -k live_smoke), and ensure the default test command omits live tests and still passes when credentials/opt-in are absent.

---

## Edge Cases, Feasibility, and Waivers (CANONICAL)

### Input Hardware Feasibility (CANONICAL)

If a rule assumes hardware that may be absent (e.g., camera or microphone), the demo must (1) detect lack of availability or permission deterministically, (2) present a clear, retryable UX, and (3) fall back to an allowed secondary path when feasible without changing the intended `interaction_mode`. Any fallback that would violate a primary-path rule must be explicitly documented in spec notes and covered by tests. Primary capture rules (**Audio**, **Image**) defer to this feasibility rule when hardware or permission is unavailable.

### Guardrail Prompt Content (POINTER)

In downstream phases, keep guardrail prompts aligned to the in-scope allowlist, preset-in-scope rule, and verdict-to-UX mapping; do not introduce alternate decision policies.

### Runtime Input Summarization (CANONICAL)

For relevance and safety guardrail calls, provide the model only a safe `runtime_input_summary` consisting of metadata (modality, MIME/type, size, duration/dimensions where applicable) plus optionally extracted content that is safe, truncated, and/or derived (e.g., first N characters of text, filename, hashed ids, image or audio format/container info). Do not include raw binary payloads or excessive verbatim content beyond what is necessary for the verdict.

### Verdict Category Clarification (POINTER)

See **How to Interpret Rules: Rule Types, Precedence, and Verdict Terms** and **Deterministic Validation & Guardrails** for the single canonical verdict taxonomy and blocked/refused terminology mapping.

---

## Maintenance, Canonicalization, and Indexes (CANONICAL)

**Canonicalization / De-Dup Policy (CANONICAL):** Maintain exactly one canonical, schema-tied, testable rule per topic; convert all other overlapping content into short pointers to the canonical anchor (or blank them) to prevent drift. Prefer the most concrete requirement with a test/schema anchor; keep indexes as pointers only, not as new requirements.

**Index Consistency (CANONICAL):** When adding, removing, or migrating canonical anchors, update **Canonical Anchors (Quick Index; Primary Navigation)** to match; indexes must not conflict with canonical rule text and must defer to precedence (see **How to Interpret Rules: Rule Types, Precedence, and Verdict Terms**).

---

## Configuration, Env Overrides, and Run Commands (POINTER)

**Config/Env Pointers:** Prefer env-driven configuration and single-source loaders. Canonical anchors: OpenAI Model Defaults, OpenAI Credentials, CodeSpec OpenAI Testing, Live Test Run Commands.

---

## Editing Guidance and De-Dup Checklist (CANONICAL)

**Rule Type Definitions (POINTER):** See How to Interpret Rules: Rule Types, Precedence, and Verdict Terms for the canonical definitions of CANONICAL/POINTER/REFERENCE and the precedence rules.

**De-Dup Checklist (CANONICAL):** Before adding a new rule, (a) search **Canonical Anchors (Quick Index; Primary Navigation)** for an existing anchor, (b) if an anchor exists, add only a POINTER or blank the redundant content, (c) ensure every CANONICAL rule has at least one concrete schema field anchor and/or test anchor, and (d) update indexes and pointers if anchors change.

**Consolidation Safety (CANONICAL):** When blanking a redundant line, ensure its requirements are fully covered by an explicit canonical anchor elsewhere; never remove the only statement of a requirement.

**Skill Application (openai-env-config):** Apply these env/credential-setup rules for any demo/app that calls OpenAI APIs, for local development setup of OpenAI-dependent projects, and whenever users ask about OPENAI_API_KEY, .env setup, or OpenAI credential configuration; keep scope limited to environment-based credential configuration (do not introduce auth/billing/other plumbing beyond this).

---

## Minimalist Views (CANONICAL)

In demo_experience.minimalist_views, for each MinimalistView enumerate the intentionally included visible_elements plus intentionally hidden_or_omitted_elements (explicitly documenting what is left out for demo minimalism); ensure every visible interactive element is covered by interaction_contracts.

---

## Synthetic Input Compatibility Fields (CANONICAL)

Treat `synthetic_demo_inputs.default_first_run_inputs` and any synthetic-demo-inputs-level `expected_outputs` as deprecated compatibility fields; do not rely on them for behavior or tests and do not implement auto-run semantics. Prefer preset-level `ordered_inputs` plus `expected_outputs` or `expected_ui_state` as the single source of truth (see **Presets (Semantics)** and **Preset Coverage**).

---

## Determinism Reset-and-Rerun (POINTER)

Provide a reset-and-rerun path that restores the exact seeded/synthetic initial state and enables re-executing the same flow deterministically (via stable parameters and/or snapshot fixtures); canonical anchors: Synthetic/Seeded Input Labeling (reset/reseed control + tests), Presets (Semantics), Presets (Build Integration Tests).

---

## Labeling Systems Clarification (CANONICAL)

**Labeling Non-Conflict (CANONICAL):** Keep the two labeling systems distinct and non-overlapping: (1) generated-output indicator applies only to AI/tool outputs; (2) seeded/synthetic input labeling terminology and reset/reseed controls apply only to prefilled/demo data. Do not use the same badge text/icon to mean both concepts; add UI tests that both systems appear where applicable and do not incorrectly appear elsewhere.

---

## Glossary (Reference)

- **AI seam:** The boundary where the app forms an OpenAI request (or tool request) and later parses/validates a response into app state; requires strict request/response validation and retryable UI-visible failure modes.
- **Agents SDK:** OpenAI agent orchestration surface for iterative tool-use and planning loops.
- **Deterministic validation:** Non-model validation that runs before any model call (type/format/size/decode/allowlist checks) and can hard short-circuit with an unsupported verdict.
- **EmbeddedDataObject:** A structured expectation container used for reviewable, deterministic sample records (e.g., summary + sample_records) rather than long free-form strings.
- **Guardrails (relevance/safety):** The two structured-output model checks that run after deterministic validation and before any main model call.
- **MCP:** A mechanism used to look up authoritative, current integration facts (e.g., supported MIME types for a target API) to build deterministic allowlists.
- **Preset:** A shipped, deterministic input bundle used to reach demo flows; apply populates UI state only, run/submit triggers guardrails then the main flow.
- **Realtime API:** OpenAI low-latency streaming API surface typically used for voice/audio or ultra-low-latency interactions.
- **Responses API:** OpenAI general-purpose request/response API surface; default choice unless Realtime/Agents SDK is required.

---

## Traceability Walkthrough (Example; Reference)

**Goal:** Show the intended mapping chain without redefining schemas.

- **Headline capability (Phase 1):** “Generate a concise meeting follow-up email from notes.”
- **Headline demo item (Phase 2):** “Follow-up email generator” with a stable capability_ref pointing to the headline capability.
- **Preset(s):**
  - Preset “Happy path: short notes” → fills the notes input with safe seeded content.
  - Preset “Reject path: off-topic” → fills notes with clearly unrelated content to trigger blocked.
- **Guardrails outcomes:**
  - Happy-path preset → deterministic validation passes → relevance allows → safety allows → main model called.
  - Reject preset → deterministic validation passes → relevance blocks (or safety blocks) → zero main model calls.
- **Walkthrough steps:**
  - Step: “Select preset” → targets preset selector.
  - Step: “Run” → targets run/submit; explanation notes guardrails run first.
  - Step: “Review generated email” → targets output region and requires generated indicator visible.
- **Tests:**
  - Preset integration test iterates presets: apply (populate-only) → run → asserts expected UI/output.
  - Guardrails reject test asserts blocked outcome shows user_message near input and makes zero main-model calls.
  - Walkthrough test asserts auto-start, navigation, cancel/retrigger, and that step targets resolve and are visible/enabled.
