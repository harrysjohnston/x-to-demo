# Demo Build Rules
## How to Use These Rules (CANONICAL)
### Audience + Prerequisites (CANONICAL): For spec authors, implementers, and reviewers; assumes the active phase schema and repo-owned references exist—if they are unavailable, do not guess or invent details; record explicit questions/TODOs and keep the artifact in draft until resolved.
### Key Concepts (POINTER): Use **Glossary** and **Artifact Primer** for definitions; do not introduce new requirements here.

### Applicability / Demo Profiles (Actionable Mapping; Skip Rules by Profile)
Pick the closest profile early (Phase 1) and treat only its Required modules as active unless later phases explicitly opt in to optional modules.
- **Baseline (text-only):** **Required** = presets (apply/run), server-side guardrails, AI seam validation, walkthrough, generated-output + seeded/synthetic labeling, async UX, browser-compatible UI + theme verification, required test tiers. **Optional** = Playwright automation; Long-Running Tasks Workflow. **Not applicable** = tools, multimodal, assets.
- **Tools:** **Required** = Baseline + Tools Mode constraints (repo-owned synthetic tool data only), UI-visible tool call/results, and tool mocking strategy/tests. **Optional** = assets, multimodal, Playwright, long-running.
- **Multimodal (audio/image):** **Required** = Baseline + capture/permission UX state machines, modality allowlists + deterministic validation, feasibility fallbacks, and modality-specific tests. **Optional** = tools, assets, Playwright, long-running.
- **Assets:** **Required** = Baseline + repo-owned synthetic assets with UI labeling + automated validation, plus an asset generation plan when needed. **Optional** = tools, multimodal, Playwright, long-running.
- **Long-running build work:** Optional add-on for any profile when the work is interruption-prone or milestone-driven (see Operational Appendix — Long-Running Tasks Workflow).
### Minimal Baseline Path (CANONICAL; Executable Happy Path)
#### Phase 1 — Define the Boundary (FeatureSpec)
- **Output:** Phase 1 artifact that locks scope to 1–3 headline capabilities with observable acceptance criteria, assumptions/constraints, excluded plumbing, a portable guardrails summary, and a tools-needed vs no-tools decision. **Gate:** acceptance criteria are observable/testable and the tooling posture is locked.
#### Phase 2 — Define the Demo Contract (DemoSpec)
- **Output:** Phase 2 artifact that defines the UX contract (views + interaction contracts), shipped presets (apply/run), an in-app walkthrough state machine with step success criteria, guardrails UX semantics using canonical verdict terms, generated vs seeded/synthetic labeling, and traceability to required tests. **Gate:** every headline item is reachable via shipped presets and covered by walkthrough + tests with consistent verdict vocabulary.
#### Phase 3 — Implement + Prove (CodeSpec/Build)
- **Output:** Phase 3 plan/build that implements the Phase 2 contract with server-side guardrails, AI seam validation, and a concrete, executable test strategy. **Gate:** required mocked-by-default test tiers pass (including presets, guardrails rejects with zero main-model calls, walkthrough, async UX, interaction matrix, theme verification, and AI-seam failure visibility), with live tests only when explicitly opted in.
### Per-Role Deliverables (by phase)
- **Spec author:** publish the active phase artifact with clear, externally observable behavior and traceability anchors (see Purpose & Output Contract; Phase Linkage, Grounding, and Metadata).
- **Implementer:** deliver the demo plus tests that prove presets, guardrails outcomes, walkthrough behavior, async UX/error states, and AI seam failure handling.
- **Reviewer:** confirm scope discipline, cross-section consistency, canonical verdict vocabulary, and that tests cover every claimed behavior.
### Document Structure (3 Parts) + Navigation (CANONICAL)
- **Structure:** Part 1 = phase procedures; Part 2 = cross-cutting invariants; Part 3 = optional modules/operational appendices. Use **Canonical Anchors (Quick Index)** to find the single canonical home for any requirement; use checklists/glossary/examples only as aids.

## Purpose & Output Contract (CANONICAL)

These rules define the standard procedure to produce exactly one active-phase artifact (Phase 1 feature spec, Phase 2 demo spec, or Phase 3 build plan) that is behavior-first, testable, and traceable.

**Output contract**
- Output exactly **one** schema-valid JSON object for the active phase (no wrappers/markdown/prose; no extra fields).
- Stay within scope: **1–3** headline capabilities/demo items with stable identifiers; do not add extra features beyond schema + provided inputs.
- Specify externally observable behavior: inputs, outputs, UI states, errors, and guardrails UX.
- Provide testable acceptance criteria and maintain cross-section traceability (views ↔ interactions ↔ presets ↔ guardrails ↔ walkthrough ↔ tests).
- Record excluded plumbing, invariants, success metrics, and (when applicable) a tooling-need assessment.

## How to Interpret Rules: Rule Types, Precedence, and Verdict Terms (CANONICAL)

**Rule types (strength and intent)**
- **CANONICAL:** Normative requirements that can be verified. Each CANONICAL rule should include at least one explicit anchor cue: an artifact anchor (what the phase artifact must state), a UX contract anchor (what a user can observe), and/or a test anchor (what automated tests must prove).
- **POINTER:** Non-normative navigation to the canonical anchor; do not restate requirements.
- **REFERENCE:** Informational notes, indexes, and examples; no new normative requirements.

**Conflict resolution / precedence (use this whenever rules appear to disagree)**
1. The active phase artifact JSON schema + explicit user input
2. Cross-phase consistency constraints (stable feature/capability identifiers; tooling posture consistency)
3. Safety/guardrails requirements
4. This build-rules document

If a deviation is necessary, document it in spec notes and/or code comments.

**Guardrails verdict terminology (canonical vocabulary):** Use only these verdict terms and normalize any upstream rejection terminology to them consistently across server responses, UI rendering, specs, and tests.
- **unsupported:** Deterministic validation failure or (when treated as capability mismatch) relevance out-of-scope; hard short-circuit with zero main-model calls.
- **blocked:** Safety fail (disallowed/unsafe content or policy violation); zero main-model calls.
- **allowed:** Only when relevance (in-scope) and safety both pass; main model may be called.

## Canonical Anchors (Quick Index; POINTER; Primary Navigation)

- **Start here:** How to Use These Rules; How to Interpret Rules (precedence + verdict terms).
- **Phase 1 authoring:** Phase 1 Core Requirements; Phase 1 Acceptance Criteria Style; Phase 1 Assumptions and Constraints Declaration; Phase 1 Output Format; Scope Boundary + Excluded Plumbing; Feature Name Resolution.
- **Phase 2 authoring:** Phase Linkage, Grounding, and Metadata; UI/UX + Interaction Contracts; Minimalist Views; Presets, Synthetic Data, and Assets; Walkthrough; Runtime Inputs, Deterministic Validation, and Guardrails; Phase 2 Demo Narrative + Core Flow; Phase 2 Scope Lists; AI/Non-AI Delineation; Preset Traceability Mapping.
- **Phase 3 authoring:** Phase 3 Carry-Forward Obligations; Phase 3 CodeSpec: Implementation Plan Inventory; Phase 3 Stack Selection Must Be Concrete; Phase 3 Testing Strategy; Phase 3 Acceptance Tests; Phase 3 AI Dependency Mocking Strategy; Phase 3 Request Validation Failure UX Contract.
- **Cross-cutting invariants (always-on unless explicitly overridden):** Guardrails Pipeline; Deterministic Validation & Guardrails; AI Seam Validation; No Silent Failures at the AI Seam; Presets (Semantics/Coverage/Shipping Gate); Async UX + Error Handling; Generated Output Labeling; Synthetic/Seeded Input Labeling; Labeling Systems Clarification; Browser-Compatible UI Default (Global); Dark/Light Theme Verification; Testing Standard; Testing Tiers & Where They Are Specified.
- **OpenAI operations + live testing:** OpenAI Model Defaults; OpenAI Credentials; CodeSpec OpenAI Testing; Live Test Run Commands; Pricing / Cost Estimates; API Selection.
- **Optional modules (apply only when the triggering condition is true):** Tools Mode + Synthetic Data Constraint; Tooling Plan: Mocking Strategy; Multimodal Requirements; Images & Vision Workflows; Audio Workflows; Synthetic Assets; Asset Generation Plan; Assets: Conditionality + Naming Discipline.
- **Operational appendices (optional):** Operational Appendix — Playwright CLI; Operational Appendix — Long-Running Tasks Workflow.
- **Editing/canonicalization:** Maintenance, Canonicalization, and Indexes; Editing Guidance and De-Dup Checklist.
- **Reference aids (optional):** Build/Review Checklist; Artifact Primer; Glossary; Compact End-to-End Examples; Traceability Walkthrough.
- **Labeling + privacy/logging:** Accessibility, Labeling, Logging, and Privacy; Debug/Privacy Logging Policy.

## Build/Review Checklist (Reference; Authoritative Checklist, No New Requirements)

1. **Checklist (reference):** confirm scope (1–3 items) and carried exclusions; grounding/identifier stability; UX contract + async/theme behavior; presets + walkthrough reachability; server-side guardrails + AI seam behavior; labeling/privacy; and required tests per the canonical modules.

**No Line Number References (CANONICAL):** Do not reference line numbers in rules; use section names or topic anchors instead (e.g. "see Scope Boundary + Excluded Plumbing", "see UI/UX + Interaction Contracts").

## Phase 1 (FeatureSpecArtifact) Core Requirements (CANONICAL)

- Define exactly 1–3 headline capabilities with stable identifiers that are AI-first: for each capability, state the specific user value, what the AI generates or optimizes (the concrete artifact, decision, or improvement), why AI/innovation is required (why deterministic logic or a manual flow is insufficient), a modality-grounded input/output contract description, and an in-demo proof statement describing what an observer will see that demonstrates it works.
- Record intent framing, assumptions/constraints, excluded plumbing, invariants, success metrics, and a tools posture (tools needed vs no-tools) that is scope-locking across phases; include a portable guardrails summary consistent with **Guardrails Pipeline** and canonical verdict terms, including the user-visible outcomes/messages for unsupported (invalid), unsupported (out-of-scope), blocked (safety), and allowed cases.
- Keep the artifact behavior-first and input-entailed: explicitly enumerate the feature’s key inputs, outputs, user-visible states, and user-visible error states, and describe only what a user can observe and what is strictly implied by the chosen headline capabilities. Acceptance criteria must be strictly derived from the provided Phase 1 input and the chosen 1–3 headline capabilities; do not add “reasonable-sounding” requirements, integrations, metrics, or edge-case behaviors that are not entailed by the input. If the raw input is underspecified, narrow scope and write acceptance criteria as verifiable outcomes without adding new product commitments.

## Phase Linkage, Grounding, and Metadata (CANONICAL)

### Phase-2 Grounding (CANONICAL)

Treat the Phase 2 artifact as the sole product-requirements source of truth and the sole structured input to Phase 3: do not invent new requirements or acceptance criteria; only restate, decompose, and map Phase 1 intent into UX contracts, presets, walkthrough coverage, guardrails behavior, and tests, preserving stable identifiers for traceability.

### Consistency Trace (CANONICAL)

Include a consistency trace summarizing which Phase 1 capability identifiers are in scope, how identifiers remain stable across phases, and confirmation the walkthrough covers the same set with no extras.

### Spec Metadata Hygiene (CANONICAL)

Keep generation metadata separate from product behavior and include enough information for review: schema/version, status, source provenance (what inputs were used), and version history with unambiguous UTC timestamps; update the version history whenever meaningfully changing the artifact.

## Scope Boundary + Excluded Plumbing (CANONICAL)

### Scope Boundary (CANONICAL)

Enforce the declared scope boundary by implementing only what is necessary to demonstrate the headline demo items; treat everything else as excluded plumbing unless explicitly required by the input or active schema.

### Out-of-Scope / Excluded Plumbing (CANONICAL)

Exclude non-essential plumbing unless explicitly required by schema or input and carry Phase 1 excluded plumbing forward consistently into Phase 2. By default, treat items such as authentication/authorization, billing/payments, user management, audit logging, production observability/analytics, feature flags/config management, rate limiting, background job queues/workers, multi-tenancy, admin consoles, enterprise integrations, and deployment/CI/CD as out of scope unless the demo’s headline capability cannot be shown without them.

## UI/UX + Interaction Contracts (CANONICAL)

### No Inert UI (CANONICAL)

Every interactive element must have defined behavior and automated test coverage; no inert buttons or controls.

### Interaction Contracts (CANONICAL)

For each minimalist view, define interaction contracts and keep naming consistent between views and contracts; enumerate every user-facing control with a stable, human-readable identifier, its observable behavior/state changes, enable/disable rules with a user-visible explanation, and loading/in-flight semantics; keep preset controls consistent across preset-enabled surfaces and traceable to walkthrough targeting and tests.

### Device Target + Theme Support (CANONICAL)

Keep device framing decisions demo-honest: enable a smartphone-style frame only when the experience is explicitly mobile-like and the frame materially improves understanding; otherwise keep the frame disabled. Theme support and verification are canonical in **Dark/Light Theme Verification** (do not restate theme rules elsewhere).

## Walkthrough (CANONICAL; In-App Tour State Machine, Not a Script)

### Walkthrough Definition (CANONICAL)
**When to apply:** any demo with a user-facing UI (Baseline and above) must include the in-app walkthrough unless Phase 1/2 explicitly justify an exception and tests cover the alternative onboarding.
Interpret "walkthrough" as an in-app interactive UI tour that auto-starts, can be retriggered, can be cancelled, and is implemented as a bounded state machine rather than a presenter script.

### Walkthrough State Machine Model (CANONICAL)

Define the walkthrough as an explicit bounded state machine with states, transitions, guards, and invalid-transition handling for auto-start, navigation, cancel, finish, retrigger, and bounds safety; treat highlight-target resolution failures as retryable errors.

### Walkthrough Test Suite (CANONICAL)

Add deterministic tests covering auto-start, next/back, cancel, finish, retrigger, bounds safety, highlight-target resolution, per-step present/visible/enabled checks, and at least one end-to-end liveness run that steps from the first walkthrough step through to finish without getting stuck under expected UI conditions.

## Presets, Synthetic Data, and Assets (CANONICAL Overview)

### Presets (Semantics) (CANONICAL)

**When to apply:** whenever the demo has any reproducible runnable flow, ship presets so reviewers can reach each flow deterministically. Presets must follow apply/run semantics: apply populates UI state only (no side effects); run/submit is an explicit user action that triggers server-side guardrails then the main flow. Never auto-run on launch, navigation, view changes, or preset selection. Choose and auto-apply a default preset on startup (populate-only) and define reset behavior consistent with seeded/synthetic labeling.

### Presets (Build Integration Tests) (CANONICAL)

Mocked-by-default integration-test presets during build (default CI posture): iterate each shipped preset; apply (populate-only) -> run (guardrails then main flow); assert guardrails allow happy-path presets; assert each preset reaches main-flow execution and produces the preset's expected output and/or expected UI state (as defined in the preset spec). Include at least one rejected-case test asserting zero main-model calls when guardrails reject (see Deterministic Validation & Guardrails). If opt-in live preset smoke testing is added, it should run only a minimal representative preset (not all presets) to validate end-to-end wiring without creating a cost-heavy suite.

### Preset Coverage (CANONICAL)

Ensure every planned demo flow is reachable via at least one shipped preset. Collectively, presets must exercise all headline demo items and all main or guardrail-allow happy paths.

### Preset Shipping Gate (CANONICAL)

Do not ship or merge a demo with presets unless all presets pass the required mocked-by-default integration-test tier. Live-tier preset tests, if added, remain optional and opt-in or skip-gated.

### Synthetic Assets (CANONICAL)

If any example text, image, or audio assets are required, generate them via appropriate OpenAI APIs or scripts, store them in-repo, label them synthetic in the UI, and validate them via automated tests. Do not source ad-hoc assets from the public internet or third-party sites. If no assets are needed, required assets must be empty.

## Runtime Inputs, Deterministic Validation, and Guardrails (CANONICAL Overview)

### Guardrails Pipeline (CANONICAL)

Enforce guardrails server-side for all inputs (including presets): deterministic validation → relevance → safety; any reject must hard short-circuit before any model/tool call or other downstream side effect beyond rendering the rejection. After deterministic validation, run exactly one relevance check and exactly one safety check using strict, parseable structured outputs (no extra guardrail-like model calls). Use **unsupported/blocked/allowed** consistently, and on any reject return an actionable user message and display it near the input with retry/edit (and cancel where applicable).

## OpenAI + Tooling Integration (CANONICAL Overview)

### AI Seam Validation (CANONICAL; see Glossary: AI seam)

Treat the AI seam as schema-driven: preflight-validate every OpenAI request before sending (at minimum: confirm a concrete model choice is present; required request components for the intended call are present and non-empty; structured-output expectations are internally consistent and compatible with strict parsing; and the request is within deterministic size/format limits). Parse and validate every structured response, include a reviewable post-processing/normalization step for turning the model output into app-ready state, and fail fast with clear UI-visible, retryable errors on validation, parsing, or normalization failures.

### CodeSpec OpenAI Testing (CANONICAL)

Use a two-tier strategy: mocked-by-default tests run in CI; an opt-in live smoke tier runs only when credentials are configured and an explicit opt-in flag is set. **Mocked tier purpose:** validate OpenAI-call wiring without network use by asserting request formation at the AI seam, strict structured-response parsing/validation, guardrails short-circuit behavior, and (when tools are part of the demo) that tool calls/results are rendered in the intended UI-visible tool log, preferably using deterministic fixtures/snapshots. **Live tier contract:** must be opt-in and skip-not-fail when opt-in/credentials are absent; constrain cost and safety (low-cost, clearly safe inputs, bounded outputs, minimal-token prompts, default model configuration unless a reviewable reason exists to diverge); state what it verifies (connectivity, parsing/validation when applicable, plus at least one observable UI/state update proving the app consumed the result) and how to run. Live coverage requirement: enumerate every planned runtime OpenAI call the demo can make, then provide exactly one live integration test per enumerated call with an explicit one-to-one mapping; do not add redundant live tests unless explicitly justified as essential.

## Generated Output Labeling (CANONICAL; Single System)

Use exactly one reusable Generated badge/indicator to mark every AI- or tool-generated surface consistently. **When to apply:** whenever adding or modifying any UI that renders generated content, add/update the indicator placement and extend automated label tests in the same change so new generated surfaces cannot ship unlabeled. **Coverage:** label all generated contexts, including assistant/chat messages, summaries/suggestions, code blocks, cards/panels, tables/rows, tool results/logs, and non-text media; **generated images must be labeled on the image output itself (not only surrounding containers/captions)**, and generated audio clips must be labeled when rendered. **Icon + text:** pick one icon convention and do not mix meanings across screens; show “Generated” text when space allows, allow icon-only in tight layouts (optionally via tooltip/caption). **Placement:** keep placement discoverable and consistent per surface type (start/header/overlay corner), not below the fold. **Mixed provenance:** attach the indicator to the smallest clearly bounded generated region and do not label user-only regions as generated. **Accessibility:** use the standard accessible name “Generated content” and meet contrast requirements in both themes. **Testing:** add automated UI tests that enumerate every generated-output surface and assert the indicator is present using stable, accessibility-oriented queries; a stable test hook on the reusable badge is allowed only when needed to disambiguate icon-only or repeated indicators.

## Multimodal Requirements (CANONICAL Overview)

### Multimodal Change Control (CANONICAL)

When a demo supports any voice, audio, or image input in any capacity (primary or secondary path; single-modality or multimodal; including speech-to-text, text-to-speech, or vision features), the demo must comply with the multimodal rules in this section. When adding or modifying voice, audio, or image input, update DemoSpec and implementation together: capture controls, per-modality state machines, deterministic validation or allowlists, permission and error UX, and tests. If hardware or permission is unavailable, follow **Input Hardware Feasibility** and document any necessary deviations in spec notes or tests.

### Audio (CANONICAL)

Primary audio input must be push-to-record microphone capture with explicit user control (choose one interaction mode: press-and-hold or tap-to-toggle); never auto-record or capture in the background. Model capture UX as a simple state machine (idle, recording, processing, error) with clear transitions and cancel/error recovery back to idle. Disable conflicting controls while recording, require playback plus an explicit submit vs discard decision before any submit, and show a meaningful mic-level visualizer while listening. Permission denial must show the standard microphone-denial copy with a retry action. Tests must cover the chosen capture semantics, transitions, disabling, playback-before-submit/discard, visualizer behavior, and feasibility fallbacks.

### Image (CANONICAL)

Primary image input must be user-initiated device camera capture; upload may be secondary but not the only path. Never auto-capture on load. Model capture UX as a simple state machine (idle, capturing, processing, error) and require a preview/inspect step before submit for both camera-captured and uploaded images. Permission denial must show a clear error and retry action. Tests must cover capture, upload (if supported), preview-before-submit for both origins, and a no-auto-capture-on-load assertion.

### Modality Format + Allowlist (CANONICAL)

Define one per-modality MIME and extension allowlist aligned to the chosen OpenAI endpoint and its current documented constraints; this single allowlist must govern all input origins for the modality (record/capture output and upload). When implementing or modifying multimodal inputs, consult the current authoritative OpenAI documentation to determine supported formats and limits, using MCP lookups when available to prevent drift across API versions; do not guess or invent capability claims.
Enforce early rejection consistently across origins: for uploads, the UI must accept only allowlisted types and provide immediate, consistent rejection messaging; block unsupported types and oversize payloads before upload/transfer when feasible, and always reject server-side before any OpenAI call. If the recorder/capture output is not endpoint-accepted, prefer deterministic normalization/conversion into an allowlisted format before sending when feasible and reviewable; otherwise return an unsupported verdict with consistent "Unsupported file type" messaging. Reject messaging and user recovery guidance must be origin-independent (record vs capture vs upload): client preflight rejections and server deterministic-validation rejections must be consistent in meaning and style.

## Synthetic/Seeded Input Labeling (CANONICAL; Separate from Generated)

If the demo uses any seeded/synthetic inputs or assets (including presets, programmatic seeding, prefilled fields, datasets/lists/tables, or seeded file uploads), seeded/synthetic input labeling is mandatory and must be consistent across all seeded surfaces. Enumerate every seeded surface that must be labeled. Choose exactly one base terminology (Example|Demo|Synthetic|Sample) and use it consistently (composed phrases allowed if they preserve the base term). **Placement:** label each prefilled input adjacent/inline (or via a clear placeholder), allow a form-level banner for multiple fields, label seeded datasets/lists/tables on or above the dataset (optionally per row/card), and label seeded file uploads near the file name/upload area. **Mixed provenance:** if seeded and user-added content can coexist, make provenance unambiguous (row/card level or clearly separated sections) and test this case. **Accessibility:** labels/badges/banners must have clear accessible names that include the chosen terminology and use appropriate roles where a banner conveys status/context. Provide a deterministic reset/reseed control near the labeled content (or relevant toolbar) whose behavior is explicitly defined and stable: it must clear user edits and restore the exact initial seeded state (typically the baseline preset-applied state) without desynchronizing labels; its label must be exactly one of the allowed options in **Standard Copy Appendix**. **Testing:** add deterministic UI tests that (1) seeded labels are visible and accurate whenever seeded content is present (including after applying/switching presets) and (2) after edits, reset/reseed restores the exact documented initial seeded state and its labeling.

## Presets (Repo Ownership + Canonical Source; CANONICAL Repo Convention)

Store presets in repo-owned, reviewable files with stable identifiers and deterministic formatting so diffs are easy to scan. Maintain one canonical preset collection per demo/feature and ensure both the UI and tests read from the same source of truth. If the repository defines standard locations or naming conventions for presets, follow them; otherwise, choose and document one clear default location strategy (either UI-owned presets stored with the front-end, or a shared presets location consumed by both server and client) and keep it consistent to avoid drift.

## Async UX + Error Handling (CANONICAL)

Any async request (guardrails/main/tool/backend) must follow an explicit status state machine (idle/loading/streaming/success/error/timeout) with immediate animated in-flight feedback and clear “working” copy; choose spinner/skeleton/progress/streaming patterns appropriately; disable the initiating and conflicting controls during in-flight; enforce explicit timeouts; clear in-flight UI on both success and failure; and present distinct, retryable error/timeout states with actionable recovery.

**In-flight UI tests (mocked-by-default):** For every async-triggering action, test (1) loading/streaming affordance + “working” copy appears immediately and is accessible, (2) loading clears on success and on error/timeout and the UI transitions to the correct state, and (3) initiating (and declared conflicting) controls disable during the request and re-enable after completion; also assert visible recovery controls, a consistent error-message policy (use safe API message when appropriate else concise generic), distinct network vs timeout messaging, streaming-progress evidence when applicable, and that interaction contracts explicitly describe the loading/disable/timeout/streaming/error + recovery behavior.

## Phase 1 Output Format (CANONICAL; Avoid Schema Restatement)

Persist a deterministic Phase 1 run-input record sufficient to reproduce the Phase 1 artifact: capture the exact raw input request text, any material additional context, any user-provided naming hint, and the resolved stable feature name used in the artifact (record raw inputs before name resolution and the resolved name after).
Given the same run-input record, reruns must resolve the same feature name and preserve the same scope and acceptance intent; record any deterministic conflict-resolution rationale needed for reproducibility. Treat the run-input record as a shareable review artifact (not a debug log): keep it non-sensitive by construction or explicitly redact sensitive information while preserving the intent needed for reproducibility.

## API Selection (CANONICAL; Downstream Only)

Only Phase 2 and Phase 3 artifacts should select among OpenAI APIs. When selection is needed, justify the choice among Responses, Images, Realtime, and Agents SDK (see **Glossary**) and provide per-headline-item API mappings. Default to Responses unless voice or low-latency streaming requires Realtime, image generation/editing is the primary outcome and is best served by Images, or iterative tool orchestration requires Agents SDK.

- If any headline demo item includes **voice** (live microphone conversation or streaming voice UX), include the Realtime API in the API plan and map those voice items to Realtime. Use file/batch audio workflows only for non-voice audio use cases (for example, upload/record-a-clip transcription/translation or non-realtime text-to-speech) when the DemoSpec does not claim a voice conversation experience.
- If any headline demo item requires iterative planning or tool-use loops, include the Agents SDK in the API plan and map only those headline items to Agents SDK; otherwise do not add Agents SDK.
- Maintain a prompt pack: for each guardrail check and each headline item, identify the prompt, its purpose, required inputs, and the structured output contract; enforce strict parsing and validation at the AI seam.
- The relevance guardrail prompt must include an explicit in-scope allowlist derived from presets and intended happy-path flows. Relevance should reject only clearly out-of-scope inputs and must treat all shipped presets as in-scope by default.

- Map each headline capability to its prompts or main model call(s), walkthrough step(s), and deterministic tests so traceability is complete and non-redundant.

## Debug/Privacy Logging Policy (CANONICAL)

Logs must never persist sensitive content (user inputs, audio/image bytes, API keys, raw model outputs containing sensitive data). Allow only redacted/hashed identifiers and high-level event metadata needed for debugging; align guardrails/tooling logging with this policy. If the project persists Phase 1 run inputs for reproducibility, treat that as a controlled review artifact governed by the Phase 1 run-input rules (non-sensitive by construction or explicitly redacted), not as general-purpose logging.

## Testing Standard (CANONICAL, Scope-Limited)

Testing must be concrete with explicit commands; run continuously during build; any test failure blocks completion. Acceptance scope is strictly the 1–3 headline demo items; exclude plumbing criteria. Required coverage is defined by the canonical topic rules (e.g., presets/tests/gates, **Preset Shipping Gate**; guardrails outcomes + zero-main-call on reject; walkthrough tests; interaction matrix; async UX tests; **AI Seam Validation**; synthetic assets validation if any).

## CodeSpec Requirements (CANONICAL)

In the CodeSpec OpenAI plan, define a primary model and an ordered list of fallback models per call type (guardrails + each main call), specify when fallbacks are allowed (e.g., transient errors/overload) without changing required structured-output expectations, and record the decision rationale in a consistent way that is auditable across these dimensions: primary interaction mode (single-turn vs multi-turn vs streaming), latency category (instant vs noticeable vs long-running), and statefulness category (stateless request/response vs session-like state carried across turns).

In the CodeSpec API selection section, map each headline demo item to exactly one selected API surface (Responses, Images, Realtime, or Agents SDK) with rationale and an explicit “what would break if swapped” note; additionally include a single, explicit summary of the set of API surfaces used by the demo overall and why that set is sufficient. Include an explicit, reviewer-auditable confirmation that the chosen API set satisfies the DemoSpec’s interaction requirements (including any voice and tool-loop needs) and that no additional API surfaces are used at runtime beyond those declared.

## Deterministic Validation & Guardrails (CANONICAL Detail)

**Deterministic Validation (before any model call):** Validate per-modality MIME/type allowlist + extension sanity; max payload sizes; modality parsing/decoding checks (including container readability for audio/image); for audio, enforce duration limits and any endpoint-relevant technical constraints that can be validated deterministically (for example, channels and sample rate when required by the chosen workflow); for text-like inputs, enforce valid UTF-8 decoding and any required parseability (for example, when the demo accepts JSON-like payloads, require that they are readable and parseable as JSON); and include an explicit unsupported-modality/format short-circuit path.

If deterministic validation fails, return an unsupported verdict with a user-visible message and perform zero relevance, safety, and main-model calls (hard short-circuit).

Guardrail model responses must be strict, parseable JSON that conforms exactly to the authoritative guardrail verdict schemas used by the project (no extra keys) and must consistently carry: (1) a machine-checkable decision signal for that guardrail, (2) a non-user-facing reason suitable for audit/debug review, and (3) a user-facing message intended for UI display. If parsing or validation fails, treat it as a hard failure with a UI-visible, retryable error and do not infer verdicts from free-form text.

Each guardrail model prompt must use explicit system/developer/user layers and must include all required context for a deterministic decision: the demo scope/context, an explicit supported-modality declaration and how to interpret provided input summaries, the normalized runtime input summary/metadata plus any optional safe extracted content, and an explicit decision policy for that guardrail (what counts as in-scope and demo-appropriate vs out-of-scope/inappropriate for relevance; what constitutes unsafe/disallowed for safety). End with an instruction to output JSON only matching the provided schema (no prose/markdown and no additional keys).

Guardrails logging policy: never persist raw prompts/responses or sensitive user content; log only request/run id, deterministic validation outcomes, relevance/safety decision labels, per-step timing/latency, and structured-output parse success/failure.

Mocked-by-default tests must cover allowed, unsupported, and blocked outcomes; assert (1) rejected paths return user-visible reject messages, (2) rejected paths trigger zero main-model calls, and (3) deterministic validation failures hard short-circuit and skip all guardrail model calls.

## OpenAI Model Defaults (CANONICAL)

Apply these OpenAI model-default rules to any demo that uses OpenAI APIs unless a demo-specific requirement explicitly overrides them. **When to apply:** treat this section as an always-on checklist whenever (a) setting up a new demo that calls OpenAI, (b) adding a new OpenAI call path (guardrails, main generation/extraction, agent/tool-loop, or realtime), or (c) refactoring configuration/clients in a way that could reintroduce hardcoded model choices.

**Default Model Configuration (CANONICAL, Centralized):** Use gpt-5.2 with low reasoning effort for Responses API + Agents SDK calls and gpt-realtime for Realtime calls; centralize these defaults in one shared configuration location with exactly one per-demo override point, and ensure every OpenAI call path (guardrails checks, main generation/extraction, and any agent/tool-loop calls) reads model defaults from that shared configuration (no hardcoded model/reasoning choices at call sites).

Expose overrides via documented environment variables (preferred for deployment flexibility) or a single demo-owned config constant mechanism. Do not add secondary override mechanisms (such as per-request overrides, scattered feature-level model picks, or multiple config modules) that would undermine the single override point. Ensure the repo-owned example environment file makes every supported override reviewer-visible so reviewers can see what is configurable without reading code.

**Model Default Tests (CANONICAL):** Add deterministic tests asserting (1) defaults resolve to the documented default models and reasoning setting when no overrides are set, and (2) the specific override mechanism the demo actually implements works end-to-end using env patching/config injection; tests must not rely on the ambient environment. Do not claim support for an override path unless that exact path is exercised by tests. Additionally, provide a single, reviewer-auditable summary of the effective model configuration (model choices and reasoning setting when applicable) that can be checked in review and asserted in tests, so all OpenAI call paths are demonstrably reading from the same centralized defaults.

## OpenAI Credentials (CANONICAL, Env-First + Single Loader)

Load the OpenAI API key via the framework’s standard env-loading mechanism into one shared config module/class used by all OpenAI client code; avoid bespoke per-feature loaders. Normalize the configured key before validation (for example, trim whitespace) and validate it is present and non-empty at startup or before the first OpenAI API call. On missing/empty keys, fail fast with a clear, catchable error and (when applicable) a structured HTTP/UI error response whose message names the required API-key environment variable and how to fix it; do not return a generic 500, and keep the error policy and response shape consistent. **Documentation deliverables (required):** provide a repo-owned example environment file and a README “Environment Setup” section stating where the env file is discovered from, how to copy and set the key, and at least one run command; never commit real secrets (env files must be gitignored). **Tests (required, env-patched):** add deterministic tests that (1) when a key is configured, the loader returns the exact configured value, and (2) when missing/empty, the loader throws/returns a catchable error that names the required variable and yields the documented UX/HTTP failure behavior; tests must not rely on an ambient env file.

## Pricing / Cost Estimates (CANONICAL)

When selecting models or estimating run cost, use the repo-owned pricing reference document as the single price authority (teams may adapt the filename/location, but keep one canonical source). Treat prices as USD per 1M tokens and structure estimates as a clear breakdown of input, cached input (when supported and explicitly used), and output; treat reasoning tokens as output and state uncertainty when reasoning-token usage is not directly observable. Default estimation stance when token counts are unknown: provide a conservative range and, unless the spec can justify otherwise, assume output tokens are materially higher than input (often several times higher) so estimates are reviewer-comparable rather than hand-wavy. Report realtime and audio pricing as distinct line items per call type and ensure each call path is mapped to the correct pricing tier (text vs realtime vs audio vs image) so mixed-modality demos do not misprice costs. Assume no caching in estimates unless the implementation explicitly uses cached input; if caching is expected, explicitly state what repeated context is intended to be cached and what is not, so reviewers can audit the assumption. Keep any mirrored pricing references in sync to avoid drift.

## Live Test Run Commands (CANONICAL)
Maintain a single repo-owned place that lists copy-pastable commands to run the default mocked-by-default test tier(s) and the opt-in live tier, including required environment variables/flags and any safety/cost constraints; keep this documentation consistent with the Phase 3 testing strategy.
## Edge Cases, Feasibility, and Waivers (CANONICAL)

### Input Hardware Feasibility (CANONICAL)

If a rule assumes hardware that may be absent (e.g., camera or microphone), the demo must (1) detect lack of availability or permission deterministically, (2) present a clear, retryable UX, and (3) fall back to an allowed secondary path when feasible without changing the declared primary interaction mode. Any fallback that would violate a primary-path rule must be explicitly documented in spec notes and covered by tests. Primary capture rules (**Audio**, **Image**) defer to this feasibility rule when hardware or permission is unavailable.

### Runtime Input Summarization (CANONICAL)

For relevance and safety guardrail calls, provide the model only a safe runtime input summary consisting of metadata (modality, MIME/type, size, duration/dimensions where applicable) plus optionally extracted content that is safe, truncated, and/or derived (e.g., first N characters of text, filename, hashed ids, image or audio format/container info). Do not include raw binary payloads or excessive verbatim content beyond what is necessary for the verdict.

## Maintenance, Canonicalization, and Indexes (CANONICAL)

**Canonicalization / De-Dup Policy (CANONICAL):** Keep exactly one canonical, testable rule per topic; before adding new rules, search **Canonical Anchors (Quick Index; Primary Navigation)** for an existing home and add only a POINTER (or blank redundancy) when one exists; when blanking text, never remove the only statement of a requirement; any new CANONICAL rule must include an artifact, UX, and/or test anchor cue.

**Index Consistency (CANONICAL):** When adding, removing, or migrating canonical anchors, update **Canonical Anchors (Quick Index; Primary Navigation)** to match; indexes must not conflict with canonical rule text and must defer to precedence (see **How to Interpret Rules: Rule Types, Precedence, and Verdict Terms**).

## Editing Guidance and De-Dup Checklist (CANONICAL)

## Minimalist Views (CANONICAL)

For each minimalist view, list intentionally included visible elements and intentionally hidden/omitted elements, and ensure every visible interactive element is covered by interaction contracts.

## Synthetic Input Compatibility Fields (CANONICAL)

Avoid deprecated compatibility mechanisms that imply auto-run or duplicate preset expectations; use shipped presets (and their expected outcomes) as the single source of truth for deterministic demo behavior and tests.

## Labeling Systems Clarification (CANONICAL)

**Labeling Non-Conflict (CANONICAL):** Keep the two labeling systems distinct and non-overlapping: (1) generated-output indicator applies only to AI/tool outputs; (2) seeded/synthetic input labeling terminology and reset/reseed controls apply only to prefilled/demo data. Do not use the same badge text/icon to mean both concepts; add UI tests that both systems appear where applicable and do not incorrectly appear elsewhere.

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

## Audio Workflows: Endpoint Choice, STT, and TTS (CANONICAL)

### Audio Endpoint Choice (CANONICAL)

When the demo includes audio, choose the audio workflow explicitly and keep all UX, validation, and tests consistent with that choice:
- **File/batch audio workflow:** Use when the user provides an audio clip (upload or recorded clip) and the system returns transcription/translation or generated speech as a single request/response (optionally with a progress indicator).
- **Realtime workflow:** Use only when the experience requires live microphone streaming with very low latency, automatic turn detection, partial deltas, or continuous session-based interaction; document which of these realtime-only requirements are needed.

### Speech-to-Text (STT) Behavior (CANONICAL)

For any STT capability, make explicit, reviewable choices for (a) the model strategy, (b) the response shape/contract, and (c) the user-visible rendering, and test them accordingly:
- **Transcription vs translation:** State whether output preserves the source language or is translated into English; treat these as distinct behaviors with distinct acceptance tests.
- **Response shape (contract):** Choose the intended transcript contract as a first-class decision (for example: plain text only, structured JSON, verbose JSON with timestamps/segments, or diarized/speaker-attributed structure). Define what the user sees (transcript text, timestamps/segments, speaker labels) and what is treated as optional metadata vs required output. Ensure parsing/validation and UI rendering are aligned to this chosen contract and are covered by tests.
- **Model selection + feature-tied fallback:** Prefer a modern transcription model as the default. Only fall back to an alternative model/workflow when a required, user-visible feature depends on it (for example: a specific timestamp granularity, diarization, or a realtime partial-delta experience) and document the feature-based rationale. Avoid legacy approaches unless explicitly justified by a needed capability, and ensure tests cover both the default path and any declared fallback behavior.
- **Realtime transcription (if used):** When using Realtime for transcription, define how partial transcript updates are displayed, when they finalize into the stable transcript, and how automatic turn detection (or its alternative) affects observable UI state transitions. Tests must cover the partial-to-final transition and at least one representative turn boundary behavior.
- **Epistemic caution:** Treat transcripts as model output, not ground truth; avoid demo logic that assumes transcripts are always correct. Tests should validate handling and UX, not claim perfect transcription accuracy.
### Text-to-Speech (TTS) Behavior (CANONICAL)

For any TTS capability, make explicit, reviewable choices for the model and user-visible audio contract, and test them accordingly:
- **Model selection rationale + feature-tied fallback:** Select a TTS model based on the demo’s observable latency and quality needs (for example: “instant preview” vs “higher quality final audio”). If a fallback model is declared, it must be justified by a required user-visible capability (or reliability constraint) and must not silently change the promised audio behavior; document when fallback is allowed and ensure it is test-covered under mocking.
- **Explicit voice choice:** Choose and document a specific voice (do not rely on implicit defaults) and ensure it is stable across runs unless the user explicitly changes it.
- **Output format choice:** Choose an output format aligned to playback and storage constraints and keep it consistent with the player and download behavior in the demo.
- **Instruction support:** Use style or instruction-like controls only when supported by the chosen model/endpoint; otherwise omit them rather than simulating support.
- **Streaming playback (if used):** Only stream generated audio when progressive playback materially improves the experience; define buffering/ready states and test them.
### Audio-Specific Testing Additions (CANONICAL)

In addition to the general testing standard, add mocked-by-default tests for audio variants that the demo claims to support, including (as applicable):
- transcription vs translation behaviors (distinct assertions),
- diarization/timestamps/detail-level rendering and response parsing/validation,
- incremental transcript updates and finalization (if streaming deltas are used),
- audio format normalization/conversion paths (capture output → endpoint-accepted format), including early reject UX for unsupported types and oversize payloads.

Live opt-in tests (when enabled) must include coverage for each distinct planned OpenAI audio call type used by the demo (guardrails plus each STT/TTS call), consistent with the per-call live-test rule.

## Demo-Specific Specs vs Reusable Defaults (CANONICAL)

- State only demo-specific, user-observable flows, inputs/outputs, UX states, guardrails outcomes, presets, and acceptance criteria; reference canonical anchors for shared defaults instead of pasting boilerplate, and avoid re-specifying underlying default logic unless a demo-specific choice affects observable behavior.

## Phase 2 (DemoSpecArtifact) Central AI Value + “AI Moment” (CANONICAL)
For every headline demo item, the DemoSpec must make the AI/technical innovation the central user value: explicitly identify the moment where AI behavior delivers the core outcome, keep non-AI steps minimal and clearly supporting, and ensure the walkthrough and success signals foreground this AI moment rather than peripheral UI or plumbing.

## Phase 2 Authoring: Runtime Input + Guardrails Summary Must Be Human-Auditable (CANONICAL)
In addition to defining the guardrails pipeline behavior, the DemoSpec must include a coherent, human-auditable summary of runtime inputs and guardrails: supported input modalities and how users provide them, the end-to-end decision pipeline in plain language, the user-visible outcomes for unsupported/blocked/allowed cases, and cancel/retry semantics. Reviewers must be able to understand the full reject/allow behavior without inferring it from scattered details.

## Phase 2 Demo Narrative + Core Flow (CANONICAL)

In addition to the in-app walkthrough state machine, the DemoSpec must include a **human-readable demo narrative** that Phase 3 can implement without inference: (1) a concise demo overview a reviewer can read quickly (what the user accomplishes, what the AI produces/optimizes, and the observable outcome), (2) an explicit statement that the demo is an in-app product showcase (not a presenter script), (3) an ordered list of core flow steps with observable success signals, and (4) concise example UI copy where helpful (titles, empty states, button microcopy, error/help text). This narrative must stay consistent with the walkthrough, presets, and acceptance criteria, and must not introduce new requirements beyond Phase 1 scope.

## Phase 2 Scope Lists (CANONICAL; Reviewable In/Out)

Phase 2 must present a concrete, reviewable scope statement as two lists: what the demo explicitly includes and what it explicitly excludes. Use these lists to keep reviews and implementation disciplined, and ensure Phase 3 carries exclusions forward as non-goals and omits implementation work outside the intended demo boundary.

## Phase 2 Non-Optional Demo Invariants (CANONICAL)
**When to apply:** for all Baseline demos unless the active phase input explicitly overrides an invariant.
Default invariants (must be true and testable): (a) walkthrough auto-starts on first launch and is retriggerable (see Walkthrough); (b) the demo accepts runtime inputs, not presets-only (see Runtime Input Guardrails Applicability); (c) presets go through the same server-side deterministic validation + guardrails pipeline as user-entered inputs (see Presets (Semantics); Guardrails Pipeline); (d) the intended demo surface is a minimalist, browser-compatible UI unless explicitly overridden (see Browser-Compatible UI Default (Global)); and (e) dark/light theme support is enabled and verified (see Dark/Light Theme Verification). Any deviation must be explicitly justified and covered by tests.

## Tools Mode + Synthetic Data Constraint (CANONICAL)

When tools are used, Phase 2 must make an explicit binary decision: either the demo uses no tools, or it uses tools backed only by synthetic, repo-owned, deterministic data. Default posture: do not introduce tools unless they are absolutely necessary to demonstrate the in-scope headline capabilities; if the capability can be shown without tools, choose no-tools and keep the demo simpler. Tool calls and results must be UI-visible (including a user-readable tool call log or equivalent surface), reproducible under mocking, and must not depend on ad-hoc external services or live third-party data. If the demo uses no tools, state that clearly to prevent accidental tool creep in Phase 3.

## Phase 3 CodeSpec: Implementation Plan Inventory (CANONICAL)

Phase 3 must produce a reviewable implementation plan inventory that realizes the DemoSpec without adding product scope and keeps the AI value central; it must cover: platform posture, default mocking posture, major components, key state + state transitions (including async/error), minimalist layout/visibility constraints (including generated and seeded/synthetic labeling placement), walkthrough implementation + robust highlight targeting and target-missing fallback, presets/synthetic data/required-assets approach, and explicit non-goals derived from excluded plumbing and Phase 2 out-of-scope lists.

## Phase 3 Carry-Forward Obligations (CANONICAL; Phase 2 → Phase 3 Checklist)

Treat Phase 3 as a structured projection of Phase 2 decisions. Phase 3 must explicitly carry forward: (1) the in-scope/out-of-scope scope lists into non-goals; (2) interaction requirements into API coverage confirmations (voice/tool-loop needs); (3) interaction contracts into an interaction test matrix and control-level loading/enablement behavior; (4) walkthrough steps into walkthrough implementation notes and walkthrough tests; (5) presets and required assets into deterministic fixtures, validation, and tests; (6) guardrails UX semantics into server-side enforcement and rejected-path tests; and (7) when tools are used, the Phase 2 tooling decision into an implementation-ready tooling plan (including UI-visible tool call/result surfaces and mocking strategy). Any mismatch must be documented as a deliberate deviation.

## Phase 3 Request Validation Failure UX Contract (CANONICAL)

Phase 3 must define an explicit, testable UI error-state contract for request preflight failures at the AI seam: what the user sees, how they recover (retry/edit), and how the system guarantees that no external request is sent when preflight validation fails. This contract must be exercised by mocked-by-default tests.

## Asset Generation Plan: Content Guardrails + Operational Detail (CANONICAL)

When Phase 3 includes an asset generation plan, it must include both operational detail (how assets are generated, stored, named, and referenced by the app) and content guardrails suitable for demos: avoid real person likeness, avoid copyrighted brand assets, and avoid personal data. Asset generation must remain deterministic and repo-owned, and the demo must not generate assets live on startup.

## Tooling Plan: Mocking Strategy (CANONICAL)

When tools are present, Phase 3 must specify how tool calls are mocked in default tests, what deterministic fixtures are used, and how the UI-visible tool log remains consistent under mocking. When tools are absent, Phase 3 must state that explicitly and confirm no tool mocking is needed.

## Phase 3 Testing Strategy: Module-by-Module Plan + Verification Steps (CANONICAL)

Phase 3 must present the test strategy as a module-by-module coverage plan with concrete verification steps and copy-pastable commands; it must state the default mocked-by-default posture vs any opt-in live tier, including how each AI/tool call (and any intentional delay/timeout/error simulation) is mocked, what each tier verifies, and how to run each tier without reading code. Include coverage for: guardrails short-circuit (including zero main-model calls on reject), AI seam request/response validation and parsing failures, async state transitions and loading/timeout UX, walkthrough state machine and highlight targeting, presets integration behavior, and tooling behavior (or a no-tools confirmation). The plan must be auditable and map back to headline demo items.

## Phase 3 Acceptance Tests: Given/When/Then Format (CANONICAL)

Phase 3 acceptance tests must be written in a clear Given/When/Then structure so reviewers can trace each claim to observable behavior and to automated tests. Keep them scoped to the 1–3 headline demo items and the defined rejected-path behaviors; do not expand into excluded plumbing.

## Operational Appendix — Long-Running Tasks Workflow (CANONICAL)

Use this workflow when the demo work is likely to be extended and interruption-prone (for example: multi-step refactors, multi-surface UX changes, multi-tier test additions, or work that requires repeated build/run cycles). The goal is to make progress **bounded, resumable, and verifiable** rather than an opaque single push.

### Entering long-running mode (CANONICAL)

Switch into long-running mode when any of the following is true:
- The work spans multiple milestones that cannot be completed in one continuous session.
- The work requires coordinated changes across spec, implementation, and tests with non-trivial sequencing.
- The work depends on external inputs (credentials, endpoint constraints, new decisions) that may block progress.
- Verification requires multiple distinct checks (for example: presets integration, walkthrough coverage, guardrails outcomes, async UX assertions).

### Pre-work execution contract (CANONICAL)

Before making substantive changes, establish a short execution contract that is separate from the product spec content. If the finish line or stop conditions are not clear, resolve that ambiguity first and only then proceed with implementation work.
- **Definition of done:** A clear finish line stated in observable outcomes and required verifications.
- **Milestones:** A small ordered list of concrete milestones, each with an explicit verification step and a restart-safe, idempotent checkpoint design so the milestone can be re-run without corrupting state or creating irreversible drift.
- **Stop conditions:** A simple taxonomy for how work can end at any checkpoint (completed, blocked, waiting on external input, or stopped due to exceeded retry budget).
- **Durable tracking decision:** Identify the tracking artifacts that will serve as the canonical execution record for this long-running task, prefer markdown files with clear purpose separation (for example, contract vs worklog vs checkpoints), and do not treat transient tool output or chat history as the primary record.

### Durable tracking artifacts (CANONICAL)

Maintain a durable, in-repo execution record for long-running work using markdown files stored together in a hidden, task-specific directory that is colocated with the task’s working context when practical (so the record is context-adjacent, not detached in a generic centralized area). This record must be sufficient for another implementer (or a future session) to resume without re-discovery.

At minimum, the tracking record must make it easy to find:
- task goal and current status
- milestone list with per-milestone status
- the latest completed milestone and what was verified
- the active milestone and the next intended action
- known blockers and what input is needed to unblock
- verification status (what was last run, what passed/failed, and what remains)
- cleanup/closeout status (what temporary items exist and whether they are removed).

### Milestone-driven execution + verification cadence (CANONICAL)

Execute work as a controlled sequence of milestones. After each milestone:
- record what changed and why it is consistent with the spec and scope boundary, and when appropriate capture a concrete milestone artifact beyond code/tests (for example, a generated report, a migration summary, or a validated environment state) so progress is reviewable even across interruptions,
- record what remains and the next intended step,
- **verify the milestone** using the smallest appropriate verification (targeted tests or checks that directly prove the milestone’s claim),
- do not proceed to the next milestone until verification is recorded as passing or the task is explicitly marked blocked with a next-step plan.

### Bounded attempt loops + retry budgets (CANONICAL)

Avoid open-ended repeat cycles. For any failing verification or stuck implementation step, follow a bounded loop: **attempt → observe → verify → reassess → continue or stop**.

Define and follow a retry budget per issue type (for example: repeated failing test, repeated parsing/validation failure, repeated build/run failure). When the retry budget is exceeded, stop and record:
- what was tried,
- what evidence was observed,
- why the current approach is not converging,
- the proposed alternative strategy or the specific external input needed.

### Stall detection + required response (CANONICAL)

Treat the work as stalled if any of the following occurs:
- repeated identical verification failures without new evidence,
- no net progress in artifacts over multiple attempts,
- the same error pattern recurs after multiple edits,
- progress depends on unknowns that cannot be resolved from available inputs, or a long-running/background step produces no fresh output for an extended, predefined interval (treat this as a watchdog-style stall signal).

When stalled, you must snapshot the current state to the durable tracking record, explicitly mark the task as blocked or degraded, and either change strategy (with a stated hypothesis) or stop with a clear request for the missing decision/input.

### Resume procedure (checkpoint-first) (CANONICAL)

When resuming long-running work, do not restart from memory. First:
- read the latest checkpoint in the tracking record,
- confirm the working state matches the checkpoint (or record any drift),
- rerun the smallest safe verification that re-establishes confidence,
- continue from the next incomplete milestone rather than redoing completed work.

### Progress reporting format (CANONICAL)

Progress updates for long-running work must be milestone-oriented (not command spam) and always answer:
- what completed (with verification),
- what is currently in progress,
- what is next,
- status: on track, blocked, waiting on external input, or degraded (with why).

### Closeout / cleanup phase (CANONICAL)

Before declaring the task done, perform an explicit closeout phase:
- stop temporary processes and remove temporary artifacts used only for debugging or exploration; do not rely on the happy path to perform cleanup implicitly—cleanup must be an explicit, recorded step,
- ensure the final required verification suite passes (per the relevant testing gates),
- record any residual risks, known limitations, or intentionally unfinished edges that remain within the agreed scope boundary.

## Phase 3 Agent Skills Application (CANONICAL)

Phase 3 must explicitly apply the shared, cross-demo skills needed to deliver the standard demo guarantees (guardrails, presets, labeling, and testing). When the CodeSpec includes a skills list, it must include the baseline set that covers server-side runtime-input guardrails, synthetic input presets, canonical spec-format parity, generated-output labeling, and opt-in live OpenAI integration tests; include multimodal-related skills when voice, audio, or image modalities are part of the demo.

## Phase 1 Acceptance Criteria Style (CANONICAL)

Write each acceptance criterion in a Given/When/Then form: the preconditions, the triggering user action or event, and the observable expected outcomes (including user-visible success state and any relevant error/reject outcomes). Each criterion must bind one-to-one to exactly one declared headline capability identifier; do not introduce new capability labels in acceptance criteria, and do not allow acceptance criteria to drift to renamed or near-duplicate capability wording without updating the canonical capability identifier consistently across phases.

## Phase 1 Assumptions and Constraints Declaration (CANONICAL)

Phase 1 must explicitly declare the demo’s key assumptions and constraints that affect later feasibility and grounding (for example: a minimalist, browser-compatible UI as the default platform posture unless explicitly overridden; system dark/light theme support enabled by default; text-first vs multimodal inputs; device/frame posture; and whether tools are expected). State these as a clear, reviewable default posture set (the expected defaults) and list any explicit overrides with rationale. Phase 2 and Phase 3 must be grounded in this declared posture so later phases do not infer or silently change it.

## Images & Vision Workflows (CANONICAL)

### Image/Vision API Choice (CANONICAL)

- When the headline capability is primarily **image generation, editing, or variation** (a single prompt/operation whose main output is an image), prefer the **Images API** and keep the UX centered on producing and reviewing the image output.
- When the headline capability primarily requires **reasoning over images** (for example: comparing multiple images, mixing text + images, multi-step explanation, or returning structured fields), prefer the **Responses API** so the demo can express a clear output contract and structured outputs alongside natural language when needed.
- Do not introduce new image/vision demos using legacy chat-completions style integrations; use the current, supported API surfaces and ground choices in the authoritative OpenAI documentation for the chosen endpoint.

### Image Input Transport + Reuse (CANONICAL)

- The demo must make a deliberate, reviewable choice for how image inputs are provided to the server and onward to OpenAI (for example: hosted URL, inline encoded payload, or upload-and-reuse). The choice must be consistent with privacy constraints, payload size limits, and testability.
- If the demo supports more than one transport mode, define a deterministic preference order and document when each mode is used (including any reuse strategy) so reviewers can predict behavior and tests can exercise each supported path.

### Vision Detail Defaults + Escalation (CANONICAL)

- Default to the endpoint’s automatic detail behavior when available, and only escalate to higher-detail processing when the user goal requires it (for example: OCR, screenshots with dense text, tiny labels, handwriting, or low-contrast scans).
- Any escalation must be justified in the spec as a user-visible quality need and must acknowledge the cost/latency tradeoff; do not silently increase detail without an explicit product rationale.

### Multi-Image Reasoning (CANONICAL)

- When the user task requires **comparing or synthesizing information across multiple images**, prefer sending the relevant images together in a single model request rather than fanning out into multiple separate calls, unless the spec explicitly justifies multi-call behavior as necessary.

### Output Contracts for Vision Tasks (CANONICAL)

- Prefer **structured extraction** and clearly defined fields over free-form captions when the demo’s value depends on correctness, reviewability, or downstream use.
- The output contract must include explicit uncertainty handling: when the model cannot confidently determine a requested fact from the image(s), it must respond with a clear “unknown/uncertain” outcome rather than confident invention. Acceptance criteria and tests must reflect this behavior where applicable.

### Vision-Specific Deterministic Validation (CANONICAL)

- Deterministic validation for image inputs must include image-specific constraints beyond type/size: enforce any **image count limits**, reject unsupported transports or malformed payloads, and hard short-circuit before any OpenAI call on violation.
- When the UX includes uploads, implement a best-effort **client-side preflight** to prevent obviously unsupported files from being selected or transferred (type/extension/size) when feasible (for example, by constraining the chooser to allowlisted types and clearly rejecting mismatches immediately), while still enforcing the authoritative server-side validation as the final gate.

### Image Generation/Editing UX Controls (CANONICAL)

- Expose image-tuning controls only when they materially improve the demo’s user value or reviewer understanding. Keep defaults lean and avoid presenting advanced controls that the demo does not need to prove the headline capability.
- If tuning controls are exposed, they must be grounded in the chosen endpoint’s documented capabilities and must have deterministic defaults, clear user-facing descriptions, and test coverage proving that changing a control produces an observable, reviewable difference in behavior or output handling. Phase 2/3 must also make the supported image output-option set reviewable by explicitly stating which output options the demo supports and/or exposes (for example: size, quality, format, compression, background, and moderation level where applicable) and what defaults are used when those options are not user-exposed.

### Progressive Rendering / Partial Results (CANONICAL)

- Only implement progressive or partial image rendering when it improves user experience and is consistent with the chosen API’s response behavior. Otherwise, present a clear in-flight state and show the final image when ready. Tests must assert the intended behavior (progressive vs final-only) rather than assuming streaming exists.

### Prohibitions + Known Limitations (CANONICAL)

- Do not send CAPTCHAs to vision models. If CAPTCHA-like content appears in inputs, deterministically block the request with a clear user message and zero main-model calls.
- When a demo’s value proposition depends on visual precision, the spec must surface relevant known limitations in a user-visible way (for example: approximate counting, rotated text failures, confusion with graphs/styled lines, distortion from panoramic/fisheye images, and non-applicability to specialized medical imaging). Ensure acceptance criteria and tests cover at least one representative limitation-handling behavior when relevant to the headline capability.

### Documentation Grounding + Drift Control (CANONICAL)

- Treat image/vision endpoints, supported parameters, and constraints as potentially changeable. Before finalizing Phase 2/3 decisions, re-check the authoritative OpenAI documentation (and approved internal references when available) for the chosen endpoint’s current limits and supported features, and record any key assumptions needed for review.

### Image/Vision Testing Additions (CANONICAL)

- Extend mocked-by-default tests to cover image/vision specifics claimed by the demo: multi-image handling (when used), each supported transport mode (when more than one is supported), deterministic rejection for image count/size/type violations with zero main-model calls, and detail default vs escalation behavior when applicable.
- For image generation/editing demos, tests must assert the default output handling and any exposed tuning control behaviors, and must verify that progressive rendering is present only when the spec claims it.

## Walkthrough Step Content: AI Role + Step Verification (CANONICAL)

In addition to the walkthrough state machine mechanics, each walkthrough step must state (1) what the AI is doing at that step (or explicitly that the step is non-AI) and (2) step-level success criteria that are verifiable from the UI (for example: an enabled control becomes clickable, a guardrail message appears near the input, a generated output region updates with the generated indicator visible). Walkthrough tests must be traceable to these step success criteria, not only to navigation mechanics.

## Synthetic Demo Data Justification (CANONICAL)

When Phase 2 uses seeded or synthetic demo inputs (including presets and any repo-owned example datasets/assets), it must include a short justification of why this data was chosen: how it covers each headline demo item and why it is appropriate for demonstrating the intended behaviors. It must also include safety and realism notes confirming the data is non-PII, non-sensitive, and bounded, while still being realistic enough to validate the demo’s core claims.

## Preset Traceability Mapping (CANONICAL)

Phase 2 must include an explicit mapping that shows, for each shipped preset, which headline demo item(s) and which walkthrough step(s) it is intended to exercise (happy path and, where applicable, rejected paths). This mapping must be consistent with preset coverage claims and with the preset integration tests so reviewers can quickly confirm that every preset has a purpose and that every headline item is reachable via presets.

## AI/Non-AI Delineation: Where Innovation Lives (CANONICAL)

Phase 2 must include a reviewer-auditable delineation of which components of the demo are AI-driven and which are deterministic/non-AI, and it must explicitly state where the technical innovation lives (the key AI behaviors that make the demo valuable). This delineation must align with the AI moment(s), tool usage decisions (if any), guardrails behavior, and the planned test coverage.

## Guardrail User-Message Style (CANONICAL)

Guardrail user-facing messages must be consistent, actionable, and auditable across deterministic validation, relevance, and safety outcomes:
- **Tone and structure:** one short sentence stating what happened, one short sentence stating what to do next. Avoid scolding language or policy citations that do not help the user recover.
- **Unsupported (deterministic invalidity or out-of-scope):** explain the incompatibility or mismatch and provide a concrete next step (for example, “Try a shorter input,” “Use plain text,” “Choose an in-scope topic,” or “Use one of the examples”).
- **Blocked (safety):** state that the request can’t be helped with for safety reasons and provide a safe alternative direction when feasible (for example, “Ask for general safety information,” “Rephrase without sensitive details,” or “Choose a non-harmful goal”). Do not provide instructions that would advance the disallowed intent.
- **Consistency constraints:** messages for similar rejects must use consistent wording across presets and user-entered inputs; avoid having deterministic validation, relevance, and safety produce conflicting guidance for similar user mistakes.
- **UI contract:** messages must be displayed near the input area and must not be replaced by generic “blocked/refused” text; recovery controls (edit + retry; optional cancel where relevant) must be present and testable.

## No Silent Failures at the AI Seam (CANONICAL)

Any OpenAI- or tool-boundary failure (request validation, network/timeout, structured-output parsing/validation, or post-processing/normalization) must be surfaced as an explicit, user-visible error state with a clear recovery action (at minimum: edit inputs and retry). Do not swallow errors, fall back to empty/placeholder outputs, or present a “success” UI state when the underlying call or parsing/validation failed. Tests must cover at least one representative failure mode per call type to prove the error is visible and retryable.

## Standard Copy Appendix (Reference; Exact Mandated Strings + Allowed Options)

- **Guardrails verdict vocabulary:** unsupported / blocked / allowed (see How to Interpret Rules: Rule Types, Precedence, and Verdict Terms).
- **Generated-output indicator:** standard accessible name is “Generated content” (see Generated Output Labeling).
- **Seeded/synthetic terminology + reset/reseed labels:** choose one base term (Example|Demo|Synthetic|Sample); reset/reseed control label must be exactly one of: “Reset”, “Restore example”, “Reload sample”, or “Clear and reseed” (see Synthetic/Seeded Input Labeling).
- **Microphone permission denial (audio capture):** must display exactly: "Microphone access denied. Please allow microphone access and try again." (see Audio).
- **Copy consolidation rule:** when a module requires exact user-visible strings, define them here and have the module point here rather than duplicating them across sections.
## Repo Conventions (Appendix; Reference)

- This rules document is intended to be portable. If a repository defines canonical locations, filenames, or reference documents (for example: where presets live, where pricing references are stored, or where live-test commands are documented), treat those as repo conventions and keep them out of behavior-level requirements.
- Canonical behavior-level guarantees remain in the main modules (presets semantics, guardrails pipeline, walkthrough, AI seam validation, labeling, and testing). Repo conventions should only make those guarantees easier to implement and review, not change their meaning.

## Feature Name Resolution (CANONICAL)

Treat any user-provided feature-name suggestion as an advisory naming hint, not a binding requirement. Resolve one stable feature name that best reflects the Phase 1 intent and headline capabilities, and keep it stable across reruns and later phases. Only change the resolved feature name when the Phase 1 meaning has changed in a way that would mislead reviewers; when renaming is necessary, record the reason as part of the Phase 1 reproducibility and provenance notes so downstream phases can update consistently.

## Modality Defaults: Generic Files and Video (CANONICAL)

Unless Phase 1 explicitly opts in to a non-text modality beyond audio and images (for example, generic file upload or video), treat that modality as unsupported for the demo. If Phase 1 opts in, it must declare the user-provided acquisition method (capture vs upload), the high-level allowlist/size limits expectation, the deterministic validation short-circuit behavior, the guardrails and UI outcomes for unsupported inputs, and the required tests to prove the modality path and its rejection behavior. Do not imply support for a modality via ambiguous wording such as “files” or “mixed inputs” without making the opt-in and constraints explicit.

## Preset Selector Visibility + Single Primary Entry Point (CANONICAL)

Make the preset system discoverable without explanation: the preset selector and its apply/run/reset controls must be visible in the primary input area for the main demo flow so a reviewer can immediately reproduce any flow from the same place they enter inputs. If secondary preset access exists elsewhere (for example, on additional views), it must mirror the same global preset set and semantics rather than creating a competing preset system.

## Preset Inspectability + Human-Scannable Content (CANONICAL)

Presets must be reviewable at a glance in code review and stable under diffs:
- Use descriptive, human-scannable preset identifiers and display labels that communicate intent (for example, which headline item and whether it is a happy-path or reject-path preset).
- Keep each preset’s input values short and field-like, matching the UI’s input granularity; avoid embedding long paragraphs where a user would normally enter a short value.
- When expected outcomes are naturally structured (multiple values or records), represent them in a structured, reviewable form rather than a single long free-form string; reserve concise strings for simple, single-surface expectations.
- Keep per-preset notes brief; when there is nothing to add, use an explicit “none” convention rather than omitting the field or adding boilerplate.

## Preset Synthetic/Example Data Explicitness (CANONICAL)

Presets must be explicitly marked as using synthetic/example/demo data within the preset definitions themselves (not only via UI badges). This storage-level explicitness must be consistent with the UI’s chosen seeded/synthetic terminology so reviewers can verify provenance from both the UI and the repo-owned preset content.

## Runtime Input Guardrails Applicability (CANONICAL)

Apply the full server-side guardrails workflow to any runtime input that can influence execution (text entry, file upload, camera/microphone capture, pasted structured text, etc.) whenever a user can change inputs and trigger run/submit; treat all such inputs—including presets that populate the same surfaces—as untrusted and enforce deterministic validation, relevance, and safety before executing the feature.

## Operational Appendix — Playwright CLI: Operational Conventions for Reproducible Automation (CANONICAL)

These conventions apply when using Playwright CLI as a browser-automation aid for demos. The goal is to make automation runs **repeatable, reviewable, and safe**, without turning automation into a product dependency.

### Standard operator vocabulary (CANONICAL)

- Use a consistent, minimal operator vocabulary for documenting steps, capturing evidence, and recording operator recipes so another operator can reproduce without interpreting prose; at minimum cover: opening a browser session; navigating to a URL; interacting with the page (click, type, keyboard actions); resizing the viewport; taking snapshots; inspecting console/network; optionally routing/mocking network requests; and closing the session.

- Treat any automation step list as an **operator recipe**, not as a required demo behavior. The demo must remain correct without running the recipe.

### Snapshot defaults, naming, and artifact hygiene (CANONICAL)

- Assume snapshots may be produced **frequently** during automation (including after many commands). Plan evidence collection so it remains intentional and reviewable rather than an uncontrolled pile of files.
- Prefer tool-default snapshot naming for exploratory runs. Only choose a custom, human-meaningful snapshot filename when the artifact is explicitly part of the workflow output (for example, PR review evidence tied to a specific acceptance claim).
- Keep automation artifacts in tool-owned, local-only locations by default. Commit only the minimum evidence required for review, and only when it is non-sensitive, small enough to keep the repository healthy, and clearly tied to a specific claim (what it proves, for which flow step).
- When snapshots are used as review evidence, include a short caption in the review artifact describing: the scenario (preset/inputs), the step that was executed, and what the snapshot demonstrates (guardrails message, loading indicator, generated label, walkthrough highlight, etc.).

### Multi-session workflows and lifecycle management (CANONICAL)

- When running more than one browser session (for example, multiple browsers, parallel flows, or multi-tab scenarios), use **named sessions** so evidence and diagnostics can be attributed to the correct run.
- Before ending a work block, deterministically clean up: close sessions normally when possible; if sessions are stuck, terminate them. Do not leave orphaned browser processes.
- If session data persists between runs, explicitly clear it when switching scenarios so results remain reproducible and do not accidentally depend on prior state.

### Browser selection and reproducibility knobs (CANONICAL)

- When the demo claims browser compatibility beyond a single engine, run the same core operator recipe in each relevant browser engine as a verification step. Keep the recipe identical except for the browser selection.
- Prefer defaults that are easy for reviewers to reproduce. Only use special connection modes, profiles, or configuration overrides when they are necessary for an in-scope claim, and document the reason and the minimal steps needed to replicate.

### Storage state manipulation (cookies/local storage) constraints (CANONICAL)

- Storage-state inspection or mutation is allowed as a **debugging/verification aid** (for example, to reproduce an edge case or confirm reset behavior), but must not become a hidden dependency for the demo’s correctness.
- Never store or commit secrets, tokens, or personal data via browser storage artifacts. If storage state must be saved for reproducibility, it must contain **synthetic, non-sensitive data only**, be minimal, and be treated with the same privacy discipline as logs and diagnostics artifacts.
- If storage manipulation is used to demonstrate a claim (for example, that reset clears state), ensure the claim is also provable via deterministic app controls and required test tiers; automation may provide extra evidence but cannot be the sole proof.

### Network routing/mocking in automation (CANONICAL)

- Network routing/mocking is an approved method to make automation verification deterministic (simulate errors, timeouts, slow responses, and fixed backend responses).
- Do not use automation routing/mocking to paper over product gaps. If the demo contract requires a behavior, implement it and test it in the required test tiers; use automation mocking only to reproduce or demonstrate the behavior reliably during review/debugging.

### Local execution fallback and command documentation (CANONICAL)

- Automation must be runnable in a fresh environment. If a globally installed CLI is unavailable, use a project-local execution approach (for example, invoking via the package runner) so reviewers can run the same commands without machine-specific setup.
- Any documented automation commands must be copy-pastable and must not depend on undeclared local paths, private profiles, or undocumented environment tweaks.

### Standard “blessed” recipes for common verification tasks (CANONICAL)

- Maintain a small set of reusable automation recipes for: (1) quick-start navigation + baseline snapshot, (2) form fill + submit + async/loading evidence, (3) guardrails rejection evidence (unsupported/blocked) including the user-facing message near inputs, (4) walkthrough highlight-target verification (step-by-step with snapshots), and (5) request-mocking reproduction of a timeout/error and its recovery UX.
- Keep recipes minimal: they should validate the demo’s **observable behavior** without encoding incidental UI structure beyond stable, accessibility-oriented targeting.

### Data extraction during automation (CANONICAL)

- If automation is used for “data extraction” (for example, copying values from the UI/DOM for debugging), treat extracted data as **ephemeral** unless it is explicitly synthetic and approved for repo ownership.
- Never introduce extracted third-party content into shipped presets, fixtures, or committed artifacts unless it is clearly permitted, non-sensitive, and consistent with the repo-owned synthetic data policy. When in doubt, regenerate synthetic equivalents instead of capturing real content.
- Extraction must not create new product requirements (for example, do not add scraping-like capabilities to the demo unless explicitly in scope and covered by guardrails, UX, and tests).

## Phase 2 Required Assets: Purpose, Where-Used Mapping, and Constraints (CANONICAL)

When Phase 2 declares any required assets, each asset entry must be review-complete and human-auditable by including: (1) the asset’s purpose in the demo, (2) where it is used (which preset-driven flow(s) and which view/screen(s) reference it), (3) the key format and size/duration constraints that must hold for reliable operation, and (4) explicit confirmation of synthetic labeling consistent with the demo’s chosen seeded/synthetic terminology, including the exact user-visible synthetic label text shown for that asset.

If the demo requires no assets, Phase 2 must make that explicit by keeping the required-assets list empty and ensuring no presets, walkthrough steps, or views implicitly depend on unlisted files.

## Images & Vision: Centralized Workflow Modules (CANONICAL)

To avoid re-deriving image/vision request behavior per feature, implement image and vision calls through **centralized, reusable workflow modules** that are shared across the demo wherever the same operation occurs. Centralization must cover the repeatable decisions that drive correctness and maintainability, including: image input transport handling and any reuse strategy, default parameter sets and escalation rules for vision detail, deterministic validation/allowlist enforcement, and request/response normalization steps that turn model results into app-ready state. Specs and tests should treat these workflows as the single source of truth for consistent behavior across headline items, presets, and views.

## Image/vision Changes: Companion Module Coordination (CANONICAL)

When adding or modifying any image/vision flow (capture, upload, transport, vision reasoning, image generation, or image editing), ensure the demo remains compliant with the companion modules that jointly define expected behavior: multimodal requirements (capture state machines, permissions, and modality tests), modality format/allowlists and deterministic validation, AI seam validation and no-silent-failures error recovery, generated-output labeling (including generated images), model defaults and credentials setup, and the testing standards (mocked-by-default coverage plus opt-in live tests when used). Record any deliberate exceptions as explicit, reviewable decisions and ensure they are test-covered.

## Phase 3 Interaction Test Matrix: Control-ID Keying (CANONICAL)

Phase 3 must present (or generate from the Phase 2 contracts) an interaction test matrix that is keyed by the stable control identifiers from the interaction contracts. Each matrix entry must explicitly map: the control’s enabled behavior and expected observable outcome, the disabled state and its user-visible explanation, and the loading/in-flight expectations (including timeout and recovery when applicable). This mapping must also be consistent with walkthrough step success criteria when a walkthrough step targets the same control.

## Phase 3 Walkthrough Planning: Step Data + Highlight Strategy (CANONICAL)

In addition to implementing the walkthrough state machine, Phase 3 must document how walkthrough steps are represented and sequenced in the codebase (as reviewable step definitions rather than ad-hoc imperative scripts), and how the highlight mechanism locates and anchors targets robustly. The plan must explicitly avoid brittle assumptions (such as deep DOM structure or incidental layout) by preferring stable, user-observable identifiers and accessibility-oriented targeting, and must describe the fallback behavior when a highlight target cannot be resolved (retryable error, not a stuck tour).

## Phase 3 AI Dependency Mocking Strategy (CANONICAL)

Phase 3 must define a first-class mocking strategy for AI dependencies that supports both development and testing: how the demo runs deterministically without network calls by default, what fixtures/snapshots/contract stubs are used, and how mocked outputs remain reviewable and aligned to the demo’s output contracts. This strategy must cover guardrails calls and each main AI call path, and must ensure rejected-path behavior (including zero main-model calls on reject) is provable under mocking.

## Phase 3 Request Validation: Debug Logging Policy Statement (CANONICAL)

When describing request preflight validation at the AI seam, Phase 3 must include an explicit debug logging policy statement scoped to request validation: log only minimal, non-sensitive metadata needed to diagnose validation outcomes (for example, which validation check failed and coarse size/shape metadata), and explicitly forbid logging API keys, raw prompts, raw model responses, and raw user-provided payloads. This statement must align with the global privacy/logging policy while being present and auditable in the request-validation plan itself.

## Phase 3 Synthetic Data Loading + Deterministic Startup (CANONICAL)

When the demo uses presets or other seeded/synthetic inputs, Phase 3 must specify where the synthetic seed data lives in the repo and how it is loaded deterministically on startup. The plan must explicitly describe the startup behavior for selecting and applying the default preset (populate-only, no execution), and the reset-and-rerun implementation approach that restores the documented baseline state and enables deterministic re-execution of the same flow without manual reconstruction.

## Assets: Conditionality + Naming Discipline (CANONICAL)

Treat assets as strictly conditional: if the demo’s required-assets inventory is empty, the implementation must not include asset generation steps or runtime dependencies on untracked files; if assets are declared as required, they must be generated/committed and validated as part of the build. When assets are used, enforce a consistent naming convention that makes each asset’s stable identity and synthetic provenance obvious from its filename/path, so reviewers can audit ownership and where-used mappings without opening the file contents.

## Tooling Decision Lock Across Phases (CANONICAL)

Treat the Phase 1 tools-needed vs no-tools decision as scope-locking. Phase 2 and Phase 3 must implement and test the inherited tooling posture exactly as decided in Phase 1. Do not “quietly” add tools to make implementation easier, and do not remove tools that Phase 1 requires to demonstrate the headline capability. The only permitted change is an explicit, reviewer-auditable deviation that (1) explains why the original decision is no longer valid, (2) updates the Phase 1 decision record (not only Phase 2/3), and (3) propagates the updated posture consistently through presets, guardrails, walkthrough, and tests.

## Browser-Compatible UI Default (Global) (CANONICAL)

Unless the active phase input explicitly requires a non-browser surface, treat the demo as a browser-compatible, minimalist UI across phases. Do not author contracts that assume platform-specific affordances unless explicitly justified as necessary to demonstrate the in-scope headline capability and carried forward into implementation and tests.

## Dark/Light Theme Verification (CANONICAL)

Because dark/light theme support is a non-optional invariant, include deterministic verification that the core flow renders and remains usable in both themes. At minimum, verify the primary demo flow in light and dark themes with automated UI assertions or snapshots that cover: key controls and their enabled/disabled states, in-flight/loading indicators, guardrails reject messaging near inputs, and the generated and seeded/synthetic labeling surfaces when applicable. Treat theme regressions as test failures rather than relying on manual review.

## Phase 3 Stack Selection Must Be Concrete (CANONICAL)
Phase 3 must make stack selection concrete (no placeholders): identify the specific UI, server, and test tools used (or explicitly inherit repo defaults), justify any non-default choice, and ensure the stack supports the DemoSpec’s UX contract, mocking strategy, and reproducible test runs.
## Phase 3 Scope Discipline: No New Requirements or Acceptance Criteria (CANONICAL)
Phase 3 must not invent new product requirements, new acceptance criteria, or new user-visible commitments beyond what is grounded in Phase 2 and the active schema. Phase 3 may only restate and operationalize Phase 2 behaviors into implementation tasks and tests. If Phase 3 discovers an ambiguity or missing requirement that blocks implementation, it must be raised as a required Phase 2 clarification (or recorded as an explicit, reviewable deviation), rather than silently filling the gap with new commitments.

## Phase 3 Test Plan Language: Anti-Vagueness Standard (CANONICAL)
Avoid non-verifiable testing language. Replace phrases like “should work,” “ensure correct behavior,” or “test edge cases” with concrete, auditable statements that specify the trigger, the observable outcome, and the verification method (including what assertion proves the claim). Any test-plan item that cannot be verified from observable UI/state and deterministic assertions must be rewritten or removed.

## Phase 3 Guardrails Contracts Must Be Explicitly Named (CANONICAL)
Phase 3 must present the runtime guardrails plan with an explicit, reviewer-auditable declaration of the structured-output contracts used for relevance and safety decisions, and must confirm that the implementation strictly parses and validates against those named contracts (no free-form prose interpretation). This declaration must be consistent with the two-step guardrails pipeline and the canonical verdict terminology used by the demo.

## Audio Speech: Workflow Decision Record (CANONICAL)

When a demo includes STT, TTS, or realtime audio transcription, maintain one human-auditable audio workflow decision record grounded in authoritative OpenAI documentation (and any approved, repo-owned references when available): capture the endpoint/workflow choice, STT/TTS strategies and response shape/rendering, supported formats/limits across capture/upload and server validation, and any streaming/partial-update UX; record key assumptions to avoid repeated re-derivation, and update the record and associated tests together whenever audio behavior changes.

## Audio Speech: Realtime Transcription UX Contract (CANONICAL)

When Realtime is selected for transcription, the demo must define an explicit, testable user experience contract for realtime transcription that goes beyond generic “streaming” language:
- users must be able to tell when the system is actively listening vs processing vs finalized,
- partial transcript updates (if shown) must have a clear, observable distinction from finalized text (for example, styling or a “draft” marker),
- turn detection (automatic or user-driven) must map to clear UI state transitions and must not leave the demo in an ambiguous “half listening” state,
- failure modes (disconnect, timeout, permission loss) must surface as retryable, user-visible errors consistent with the async/error and AI-seam failure rules.

Tests must include at least one deterministic scenario that exercises partial updates (when claimed), finalization, and a representative turn boundary or user-driven stop event, plus a representative realtime failure and recovery path under mocking.

## Audio Speech: Change-Coordination Checklist (CANONICAL)

Any time audio behavior is added or modified (capture UX, allowlists/limits, STT, TTS, realtime transcription), explicitly confirm in the spec and tests that all affected cross-cutting modules remain consistent (multimodal capture/permissions/feasibility, allowlists + deterministic validation + reject messaging parity, async/loading + recovery, credentials + model defaults, AI seam validation + no-silent-failures, and per-call opt-in live tests when used).

## Phase 2 Headline Demo Items: Primary Interaction Mode + Derivation Consistency (CANONICAL)

For each headline demo item in Phase 2, explicitly declare its **primary interaction mode** (for example: text-first form submission, chat-style turn-taking, image capture/upload, push-to-record audio, realtime voice conversation, or tool/agent loop). Treat this declaration as the downstream driver for consistency: it must align with the demo’s stated interaction requirements, the selected API surfaces, the multimodal and tools modules (when applicable), and the required tests. If an item is multimodal or tool-assisted, state which modality or tool use is primary vs secondary so reviewers can predict the intended user experience.

## Phase 2 Interaction Requirements: Deterministic Derivation + Auditable Rationale (CANONICAL)

Phase 2 must present cross-item interaction requirements (for example: whether voice is required, whether a tool/agent loop is required, whether image input is required) as a **deterministic derivation from the set of headline demo items**, not as discretionary flags. For each such requirement, include a short rationale that points to the specific headline item(s) that necessitate it. Treat any mismatch between the derived requirements and the headline items as a spec error that must be resolved in Phase 2 (not deferred to Phase 3 implementation decisions).

## Phase 2 Walkthrough Step Inventory: Stable Step Identity + Target Linkage + Retrigger Mechanism (CANONICAL)

In addition to the walkthrough state machine mechanics and step success criteria, Phase 2 must make each walkthrough step reviewable as a stable inventory: give every step a stable, human-readable identifier, and define each step’s UI target in a way that is systematically linkable to the interaction contracts (so a reviewer can trace step target → corresponding control on a view → tests). When a step targets an icon-only or otherwise compact control, ensure the control’s user-observable label or icon meaning is described consistently so targeting and accessibility remain unambiguous.

Phase 2 must also describe the user-visible **retrigger mechanism** for the walkthrough (how a user starts it again after completion/cancel), including where the retrigger control lives in the UI and any enablement rules. This retrigger mechanism must be covered by walkthrough tests.

## Phase 2 Seed Dataset: Compact, Deterministic, and Justified (CANONICAL)

When the demo uses any seeded or synthetic demo data beyond single-field presets (for example: lists, tables, small collections, or reusable example records), Phase 2 must include a compact, embedded seed dataset representation that is deterministic and human-scannable. The seed dataset must be explicitly tied to the headline demo items it supports, consistent with seeded/synthetic labeling and reset/reseed behavior, and covered by deterministic tests proving it loads and resets predictably. Keep the dataset small and non-sensitive; do not rely on ad-hoc, long free-form example strings when structured example records would be clearer and more testable.

## Phase 2 Success Signals + Example Copy: Required Inventories (CANONICAL)

Phase 2 must include (1) an explicit, non-empty inventory of observable success signals aligned to each headline demo item and its core flow steps, and (2) a curated inventory of example UI copy snippets that are needed to implement the demo contract without inference (titles, empty states, button labels, helper/error text, and guardrail reject microcopy where applicable). Keep these inventories consistent with the walkthrough, interaction contracts, presets, and guardrails user-message rules; do not introduce new scope via copy.

## Phase 2 Tooling Decision Trace: Reviewer-Auditable Carry-Forward (CANONICAL)

When tools are in scope or explicitly out of scope, Phase 2 must include a dedicated, reviewer-auditable tooling decision trace that carries forward the Phase 1 tools-needed vs no-tools decision and states the Phase 2 consistency assertion (no contradiction). If a deviation is proposed, it must be treated as an explicit cross-phase change that updates the original decision and propagates consistently through presets, walkthrough, guardrails behavior, and tests.

## Pricing-Aware Model Choice and Cost/Quality Trade-offs (CANONICAL)

When a demo makes or changes any OpenAI model choice (defaults, overrides, fallbacks, or per-call variations), the spec must include a brief, reviewer-auditable cost/quality rationale grounded in the pricing reference. This applies equally to guardrails calls and main feature calls.

- **Tiering discipline:** It is acceptable (and often preferable) to choose different model cost/quality tiers for different call types (for example, lower-cost models for high-volume guardrails checks and higher-quality models for the main user-visible generation), as long as the choice is explicit, consistent with the required structured-output contracts, and covered by mocked-by-default tests.
- **Comparison requirement when alternatives exist:** If more than one candidate model is plausible (or if overriding a shared default), include a compact comparison that names the candidates, summarizes relative cost, and states why the chosen model best fits the demo’s latency/quality needs. Keep the comparison decision-focused; do not paste pricing tables into the spec.
- **Context-window impact acknowledgment:** When using reasoning-heavy settings or workflows, explicitly acknowledge that reasoning tokens consume context capacity and can increase truncation risk; describe any mitigation that is observable or testable (for example, shorter prompts, bounded outputs, or smaller inputs).
- **User pricing questions (procedure):** When a user asks about model pricing, token rates, caching rates, or cost/performance comparisons, respond by (1) consulting the repo-owned pricing authority, (2) clearly stating the relevant pricing tier(s) for the user’s call type(s), and (3) providing a simple comparison or estimate using the same breakdown and default-estimation stance as the Pricing / Cost Estimates rules.

## Demo Design Decisions: Guardrails + Presets Preservation Contract (CANONICAL)

These build rules define a small, stable set of cross-cutting demo design decisions that must not drift over time. Treat them as a preservation contract: when implementing, refactoring, or modifying guardrails behavior or the preset system, explicitly reaffirm that each decision remains true (or document a deliberate deviation and its rationale).

### When to Apply (CANONICAL)

Apply this preservation contract whenever any change affects: runtime input handling; deterministic validation; relevance or safety guardrails; verdict-to-UX messaging; the run/submit trigger; preset definitions or their UI; preset integration tests; or any refactor that could alter when model/tool calls happen.

### The Four Non-Negotiable Design Decisions (CANONICAL)
Core decisions to reaffirm: server-side guardrails authority; exactly one relevance check and one safety check with strict structured outputs; a single global preset system where apply populates only and run/submit executes (no auto-run); and preset coverage plus mocked-by-default preset integration tests as a merge/ship gate.

### Decision Record Requirement (CANONICAL)

When changes could affect these decisions or other cross-cutting demo guarantees (especially guardrails, presets, walkthrough, labeling, or testing), include a lightweight, reviewer-readable decision record (for example, in code comments or spec notes) that either (a) reaffirms the preservation contract remains true, or (b) declares a deliberate deviation with its scope, rationale, and the specific tests that prove the new behavior.

## Artifact Primer (Reference; Conceptual, Not Schema-Shaped)
- **Phase 1 feature spec (FeatureSpec):** *Purpose* = define the product boundary and what “done” means for the demo. *Typical contents* = 1–3 headline capabilities, user value, observable acceptance criteria, assumptions/constraints, explicit non-goals, tooling posture (tools vs no-tools), and a portable guardrails summary in plain language. *Review criteria* = scope discipline, testability of outcomes, locked tooling posture, and guardrails outcomes that can be implemented without reinterpretation.
- **Phase 2 demo spec (DemoSpec):** *Purpose* = define the demo’s user-facing contract (what the app does and how it behaves) and how the Phase 1 claims will be proven. *Typical contents* = views and interaction contracts, presets (apply/run) that reach every flow, walkthrough as an in-app tour, guardrails UX semantics, labeling rules for generated vs seeded content, and traceability to required tests. *Review criteria* = every claimed behavior is observable, reachable via presets, consistent across sections, and mapped to tests without gaps.
- **Phase 3 code spec / build plan (CodeSpec):** *Purpose* = implementation plan + proof plan that makes the demo directly buildable and verifiable. *Typical contents* = concrete stack choices, server/client boundary decisions, AI seam validation and failure UX, mocking strategy, and executable test commands (including opt-in live tests when used). *Review criteria* = no new product scope, faithful projection of Phase 2, and tests that actually prove the contract (including rejected paths and AI-seam failure visibility).
