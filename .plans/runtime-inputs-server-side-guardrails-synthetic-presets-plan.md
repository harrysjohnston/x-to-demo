# x-to-demo: Runtime Inputs + Server-side Guardrails + Preset Synthetic Inputs

## Outcomes (non-negotiable)

1. **Runtime inputs come from the demo UI** (multimodal where relevant). Synthetic inputs do *not* drive runtime behavior.
2. **Server-side guardrails gate every runtime input** before any “main AI moment” call.

   * Deterministic **type/format/size** validation
   * **Relevance** check = **model call with structured output**
   * **Safety** check = **model call with structured output**
   * **Two model calls total** (relevance, then safety). Type checks remain deterministic.
   * If guardrails fail: return a verdict, show user-visible message, and **cancel the flow (no main model call).**
3. **Synthetic demo inputs become selectable presets (global)**.

   * Presets populate the UI but **do not auto-run** on app launch.
   * Presets must have already been used for **full integration testing during build**, proving they execute successfully.
4. **Spec vs Skill split**

   * **Demo-specific** decisions must appear in x-to-demo outputs (FeatureSpec/DemoSpec/CodeSpec).
   * **Demo-agnostic** best practices/defaults must live in `.agents/skills/*` and should *not* be re-stated verbosely per demo.
   * Some topics are both: specs choose *which* capability/modalities apply; skills encode *how* to implement them.

---

## Repo context (files we will modify)

### Schemas

* `apps/api/app/x_to_demo/schemas/feature_spec.py`
* `apps/api/app/x_to_demo/schemas/demo_spec.py`
* `apps/api/app/x_to_demo/schemas/code_spec.py`
* `apps/api/app/x_to_demo/schemas/common.py`

### Prompt rules

* `apps/api/app/x_to_demo/pipeline/prompts.py`
* (optional) `apps/api/app/x_to_demo/pipeline/models.py` (phase objectives copy)

### Renderers

* `apps/api/app/x_to_demo/renderers.py`

### Skills

* `.agents/skills/*`

---

## Task Group 0 — Design decisions (lock these in code)

**Deliverable:** short, explicit decisions recorded in code comments and/or new skill docs.

* Guardrails are **server-side only**.
* Guardrails include **two structured-output model calls**:

  1. Relevance verdict
  2. Safety verdict
* Synthetic inputs are **global presets** that are selectable in UI, not auto-run.
* Presets are required to have been validated via **integration tests** (mocked-by-default tier; live tier optional).

---

## Task Group 1 — Schema changes

> Important: the pipeline enforces strict structured outputs. New fields should have **defaults** where possible to avoid breaking artifact loading, and prompts must force the model to populate every required key.

### 1.1 FeatureSpec: add explicit “unsupported type” guardrail semantics

**File:** `apps/api/app/x_to_demo/schemas/feature_spec.py`

**Why:** Phase 1 must explicitly define the *input contract boundaries* that later phases implement.

**Edits**

1. Extend `GuardrailsSummary` with a new field:

* `unsupported_input_type_short_circuit: str`

**Meaning**

* How inputs that are the wrong modality/format (or otherwise unsupported) are rejected.
* Must explicitly mention: user-visible message + flow cancellation.

**Acceptance**

* FeatureSpec outputs always contain an explicit unsupported-type policy.

---

### 1.2 DemoSpec: replace auto-run “first run inputs” with global selectable presets

**File:** `apps/api/app/x_to_demo/schemas/demo_spec.py`

**Current issue:** DemoSpec currently implies “runnable on first launch” via `default_first_run_inputs`.

**Target behavior:** Presets exist, can be selected/applied, but do **not** auto-run.

**Edits (schema)**

A) Replace `FirstRunInputSet` with a preset model.

Create:

* `class PresetInputSet(StrictSchemaModel)`

  * `preset_id: str` (stable)
  * `label: str`
  * `ordered_inputs: list[str]` (deterministic)
  * `where_used_in_headline_flows: list[str]` (capability refs / walkthrough step ids)
  * `expected_outputs: TextOrEmbeddedData` (what should happen if user runs it)
  * `notes: str` (or “none”)

B) Update `SyntheticDemoInputs`:

* Keep `seed_dataset: TextOrEmbeddedData`
* Replace `default_first_run_inputs` with:

  * `input_presets: list[PresetInputSet]` (min_length=1)
  * `default_selected_preset_id: str` (pre-selected in UI)
  * `preset_application_behavior: str` (must state: populates UI only, no execution)
  * `preset_execution_behavior: str` (must state: requires explicit user action)
* Keep `why_this_data`, `safety_and_realism_notes`
* Keep `required_assets` unchanged

C) Add a dedicated runtime input + guardrails section (demo-specific)

Create:

* `class RuntimeInputAndGuardrails(StrictSchemaModel)`

  * `accepts_runtime_inputs: Literal[True]`
  * `supported_input_modalities: list[str]` (demo-specific; not generic)
  * `input_capture_summary: str` (what UI accepts, in what views)
  * `guardrails_pipeline_summary: list[str]` (must include: type, relevance, safety)
  * `relevance_check_summary: str` (model call; structured output)
  * `safety_check_summary: str` (model call; structured output)
  * `user_visible_outcomes_on_reject: list[str]` (messages + where shown)
  * `cancel_flow_behavior: str` (explicitly: no main model call; preserve UI state; allow edit/try again)
  * `presets_go_through_same_guardrails: Literal[True]`

Add to `DemoSpecArtifact`:

* `runtime_input_and_guardrails: RuntimeInputAndGuardrails`

D) Ensure interaction contracts include controls for presets and execution

No schema change needed (already enumerates controls), but update prompt rules (Task Group 2) to require:

* Preset selector control
* Apply preset control (populates)
* Run/Submit control (executes)
* Reset/Clear control

**Acceptance**

* DemoSpec no longer describes or implies automatic execution on launch.
* DemoSpec always includes runtime input + guardrails UX contract.
* Presets are global, explicitly selectable, and explicitly non-auto-running.

---

### 1.3 CodeSpec: require server-side guardrails with two structured-output model calls

**File:** `apps/api/app/x_to_demo/schemas/code_spec.py`

**Current state:** `AISeamGuardrails` is too generic (filters + refusal policy + short-circuit). It doesn’t encode the two-step guardrail pipeline and server-only requirement.

**Edits (schema)**

A) Introduce explicit verdict schemas for the two model calls

Add models:

* `class RelevanceVerdict(StrictSchemaModel)`

  * `is_relevant: bool`
  * `reason: str` (for logs)
  * `user_message: str` (for UI)

* `class SafetyVerdict(StrictSchemaModel)`

  * `is_safe: bool`
  * `reason: str`
  * `user_message: str`

B) Introduce a server-side guardrails plan

Add:

* `class RuntimeGuardrailsPlan(StrictSchemaModel)`

  * `server_side_only: Literal[True]`
  * `deterministic_type_checks: list[str]` (format/mime/size; “unsupported” verdict)
  * `relevance_model_call: str` (demo-specific: model id; defaults come from skill)
  * `relevance_prompt_contract: str` (demo-specific: what context is passed)
  * `relevance_output_schema: str` (describe `RelevanceVerdict`)
  * `safety_model_call: str`
  * `safety_prompt_contract: str`
  * `safety_output_schema: str` (describe `SafetyVerdict`)
  * `verdict_handling: str` (mapping: unsupported vs block vs allow)
  * `logging_policy: str` (must align with existing request_validation policy: no raw content persistence)

C) Hook the guardrails plan into the CodeSpec

Option 1 (recommended): extend `AISeamGuardrails`

* Add a new required field:

  * `runtime_guardrails_plan: RuntimeGuardrailsPlan`
* Keep existing `input_filters/refusal_policy/short_circuit_behavior`, but clarify:

  * `input_filters` = deterministic checks list (can overlap with plan)
  * `refusal_policy` = user-visible refusal style
  * `short_circuit_behavior` = state/UX behavior on reject

Option 2: add to `CodeSpecArtifact` top-level

* `runtime_guardrails: RuntimeGuardrailsPlan`

Pick Option 1 unless you want guardrails outside the AI seam.

D) Add a demo-specific “skills to apply” list

Add to `CodeSpecArtifact`:

* `agent_skills_to_apply: list[str]`

Rules:

* Must include:

  * `runtime-input-guardrails-server-side`
  * `synthetic-input-presets`
  * `canonical-spec-format-parity` (schema/edit hygiene)
  * `generated-output-badge` (UI generated outputs)
* May include other skills based on modalities (future voice skill, etc.)

E) Update synthetic data implementation semantics (no auto-run)

`SyntheticDataImplementation.auto_populate_first_run` currently implies “auto-populate + trigger.”

Change the *description* to:

* “How the default preset is selected and applied (populate UI only). Execution requires explicit run action.”

If you want less ambiguity, rename the field:

* `auto_apply_default_preset_on_load` (preferred)

Note: renaming requires renderer + prompt updates; keep only if you’re ready for a breaking change.

F) TestingStrategy: add preset integration coverage statement

Add field:

* `preset_inputs_integration_coverage: str`

Must state:

* Integration tests iterate every preset, apply, run guardrails, and confirm it reaches the “main flow” in mocked tier.
* Optional live tier uses one preset (or minimal subset) when opted-in.

**Acceptance**

* CodeSpec always encodes:

  * server-side-only guardrails
  * deterministic type checks
  * 2 model calls (relevance then safety) with structured output
  * explicit reject behavior + UI contract
  * preset integration test coverage
  * relevant `.agents/skills` selection list

---

### 1.4 Bump schema version

**File:** `apps/api/app/x_to_demo/schemas/common.py`

* Update `SpecGenerationMetadata.schema_version` default (e.g. `0.2` → `0.3`).

Acceptance:

* New artifacts are distinguishable.

---

## Task Group 2 — Prompt rule changes (phase outputs must follow the new behavior)

**File:** `apps/api/app/x_to_demo/pipeline/prompts.py`

### 2.1 Update `_GLOBAL_HARD_RULES`

**Remove/replace** the rule that forces “runnable on first launch with default first-run inputs.”

**Add rules**

* Synthetic inputs are **selectable presets**, not auto-run.
* Presets must be **integration-tested during build**.
* Runtime inputs must pass **server-side** guardrails.
* Guardrails include:

  * deterministic type checks
  * relevance model call (structured output)
  * safety model call (structured output)
  * cancellation semantics
* Spec-vs-skill separation:

  * Demo-specific decisions belong in specs
  * Demo-agnostic implementation details live in `.agents/skills`

### 2.2 Update `_PHASE_RULES` and `_PHASE_PRIORITY_CHECKLIST`

**FeatureSpec phase**

* Require explicit unsupported-type short-circuit semantics.

**DemoSpec phase**

* Must include `runtime_input_and_guardrails` with explicit cancellation behavior.
* Must define **global preset** selection/apply/run UI.
* Must ensure presets go through the same guardrails.

**CodeSpec phase**

* Must include server-side guardrails plan with exactly **two model calls**.
* Must output structured output schemas/contract strings for the two verdicts.
* Must include `agent_skills_to_apply` and select the correct skills.
* Must include preset integration test coverage.

### 2.3 (Optional) Update phase objectives copy

**File:** `apps/api/app/x_to_demo/pipeline/models.py`

Update the `objective` strings to reflect:

* demo_spec: includes runtime input flow + guardrails UX
* code_spec: includes server-side guardrails pipeline + preset testing

Acceptance:

* Prompting consistently yields the new spec fields without drift.

---

## Task Group 3 — Renderer updates (markdown parity)

**File:** `apps/api/app/x_to_demo/renderers.py`

> Follow `.agents/skills/canonical-spec-format-parity`.

### 3.1 DemoSpec markdown

Replace the current “Default First Run Inputs” section with:

* Presets list:

  * preset_id
  * label
  * where_used
  * ordered_inputs
  * expected_outputs
* Default selected preset id
* Preset apply vs run semantics

Add “Runtime Input + Guardrails” section:

* supported modalities
* guardrails pipeline summary
* reject outcomes + cancel semantics

### 3.2 CodeSpec markdown

Add/print:

* Guardrails plan details:

  * server-side-only
  * deterministic type checks
  * relevance call contract
  * safety call contract
  * verdict handling
* Preset integration coverage
* Agent skills to apply

Acceptance:

* Markdown includes every new schema field, with clear section headings.

---

## Task Group 4 — Add demo-agnostic agent skills

Create the following skills (YAML frontmatter + markdown, consistent with existing skills).

### 4.1 Skill: `runtime-input-guardrails-server-side`

**Path:** `.agents/skills/runtime-input-guardrails-server-side/SKILL.md`

**Content requirements**

* Canonical server-side architecture for guardrails
* Deterministic type validation guidance (mime/size, file decoding, audio duration)
* Two-step model-call guardrails:

  1. Relevance call → `RelevanceVerdict`
  2. Safety call → `SafetyVerdict`
* Structured output schema examples for both verdicts
* Prompt template skeletons (system/developer/user), including:

  * demo scope context
  * supported modalities
  * “output JSON only” instruction
* Verdict handling conventions:

  * unsupported → “not supported / not relevant” message
  * block → “cannot help with that” message
  * allow → proceed
* Logging constraints:

  * never persist raw prompts/responses or sensitive user content
  * log only request ids, decisions, timings, schema parse outcome
* Testing checklist:

  * mocked-by-default fixtures for allow/unsupported/block
  * ensure blocked paths trigger **zero** main model calls
  * optional live smoke test uses minimal inputs

### 4.2 Skill: `synthetic-input-presets`

**Path:** `.agents/skills/synthetic-input-presets/SKILL.md`

**Content requirements**

* UI conventions:

  * global preset selector
  * apply preset populates UI only
  * run triggers guardrails + main call
  * reset/clear behavior
* Storage conventions:

  * where preset definitions live (repo path conventions)
* Test conventions:

  * integration tests iterate all presets and assert they succeed through guardrails + mocked main flow
  * optional live tier runs 1 preset when opted-in

### 4.3 Update existing skills (optional)

* Consider adding a short note in `canonical-spec-format-parity` that markdown renderers must be updated whenever preset fields change.

Acceptance:

* Skills exist and are referenced by `CodeSpecArtifact.agent_skills_to_apply`.

---

## Task Group 5 — Tests and validation

### 5.1 Schema strictness validation

* Verify new schemas remain compatible with `openai_compatible_schema()` constraints:

  * objects require `additionalProperties: false`
  * required includes all properties
  * `$ref` nodes have no sibling keywords

### 5.2 Artifact load/compatibility (recommended)

* Ensure older artifacts load where feasible by giving defaults to new fields.
* If breaking changes are acceptable, document them in changelog and bump schema_version.

### 5.3 New regression tests

Minimum tests:

* DemoSpec markdown includes presets section and does **not** mention auto-run
* CodeSpec includes guardrails plan and two model calls
* Renderer doesn’t crash on new fields

### 5.4 Preset integration testing contract (spec-level)

* Ensure CodeSpec’s `testing_strategy.preset_inputs_integration_coverage` is explicit and implementable.

Acceptance:

* Tests pass; the generator produces stable outputs including the new required sections.

---

## Task Group 6 — Cleanup: align prompts with spec-vs-skill split

This can be phased after the runtime/preset changes are stable.

* Identify which `_GLOBAL_HARD_RULES` are demo-agnostic and migrate them into skills.
* Update prompt text to:

  * require `agent_skills_to_apply` selection
  * avoid re-stating demo-agnostic rules in spec prose

Suggested migrations (optional):

* OpenAI request validation
* Two-tier OpenAI test strategy
* No inert controls
* Walkthrough reliability patterns

Acceptance:

* Specs focus on demo-specific decisions; skills hold global conventions.

---

## Implementation checkpoints (PR gating)

* [ ] Schemas compile and validate
* [ ] Prompts updated and produce valid structured outputs for all phases
* [ ] Renderers updated to include new fields
* [ ] New skills added and referenced in CodeSpec outputs
* [ ] Integration test contract for presets present in CodeSpec
* [ ] Guardrails pipeline is explicitly server-side and uses 2 model calls

---

## Canonical guardrails flow (for shared understanding)

1. **Client** captures runtime input (text/upload), sends to API.
2. **Server** performs deterministic type/size/format validation.

   * If fail → verdict = unsupported → return message → stop.
3. **Server** calls model for relevance (structured output).

   * If not relevant → verdict = unsupported → return message → stop.
4. **Server** calls model for safety (structured output).

   * If unsafe → verdict = block → return message → stop.
5. **Server** performs main model call for demo feature.
6. **Client** renders result and marks generated outputs.

(Identical flow when input was populated from a preset.)
