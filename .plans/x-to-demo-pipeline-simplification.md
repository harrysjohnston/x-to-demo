# X-to-Demo — Pipeline Simplification Refactor (Drop Stakeholder Simulation)

## 1) Intent (why this refactor exists)

The current pipeline is harder to reason about than it needs to be:

- It assumes **Input X is a transcript**, when X can be any raw material.
- It uses **stakeholder simulation** (personas + multi-round convergence) which increases token cost, latency, and output variance.
- It produces long narrative artifacts that are difficult to validate or drive automation from.

This refactor aims to make the pipeline **smaller, clearer, and more testable** while preserving the core value: converting messy input into an executable demo handoff.

## 2) Non-goals (explicitly out of scope)

- Reintroducing stakeholder simulation (personas, dialogic convergence, multi-round debate).
- Designing production architecture (services, databases, scaling, security posture) beyond what a demo needs.
- Building “perfect” ingestion for all file types (PDF parsing, image OCR, etc.) — treat as future work.

## 3) Constraints & invariants (must always be true)

- **Input X may be any type**; the pipeline must not rely on transcript structure.
- The pipeline must preserve uncertainty: it can propose interpretations, but must label them.
- The feature spec must remain **behaviour-first** (inputs/outputs, pre/postconditions, error states, acceptance criteria).
- The demo spec must remain intentionally small: **5–7 steps**, scripted/mocked by default.
- If implementation and spec conflict, **spec wins** (spec-driven development posture).

Draft references:

- SDD feature spec checklist: [`draft-feature-spec-principles.md`](./draft-feature-spec-principles.md)
- Demo-spec generation prompt: [`draft-feature-to-demo-spec-prompt.md`](./draft-feature-to-demo-spec-prompt.md)

## 4) Proposed vNext pipeline (3 phases; merge Phase 1 + 2)

Move to a simpler, three-phase pipeline by merging the former Phase 1 “digest/problem frame”
into the FeatureSpec generation. This reduces calls and removes duplication while preserving
the same core artifacts (FeatureSpec → DemoSpec → CodeSpec).

### Phase 1 — “Input → SDD Feature Spec” (merged)

**Input:** raw `x_input` + optional context
**Output:** `FeatureSpec` (behavioural; markdown + embedded JSON)

Key behaviours (digest + spec in one artifact):

- Identify/guess `x_source_type` (e.g., transcript, PRD, notes, ticket, email, unknown).
- Extract the primary problem and who is affected (roles, not simulated stakeholders).
- Capture assumptions, constraints, risks, and open questions.
- State **intent before implementation**: outcome, objective, problem.
- Define **external behaviour**: inputs, outputs, preconditions, postconditions, error states.
- Provide **acceptance criteria** as Given/When/Then.
- Declare **constraints & invariants** (business rules, privacy/safety, performance bounds for demo).
- Define **success metrics** and “definition of done”.

Hard rules:

- No stakeholder personas or convergence rounds.
- No UI design details; only describe observable behaviour and minimal UX implications.
- Use the checklist in [`draft-feature-spec-principles.md`](./draft-feature-spec-principles.md) as the definition of “SDD-ready”.

Failure modes to handle:

- Input is contradictory or too vague → explicitly list what’s missing and what can’t be assumed.

### Phase 2 — “Feature Spec → Demo Spec”

**Input:** Feature spec
**Output:** `DemoSpec` (minimal demo plan; markdown + embedded JSON)

Key behaviours:

- Use the “Feature spec → demo spec” principles:
  - happy path
  - mocked data
  - moment-of-value driven
  - explicitly in-scope vs out-of-scope
- Produce a 5–7 step “core flow” that best demonstrates the feature.
- Generate the `DemoSpec` using [`draft-feature-to-demo-spec-prompt.md`](./draft-feature-to-demo-spec-prompt.md) as the baseline prompt/template.

### Phase 3 — “Demo Spec → Code Spec”

**Input:** Demo spec
**Output:** `CodeSpec` (implementation-ready prompt; markdown + embedded JSON)

Key behaviours:

- Bias toward a runnable demo with mocked dependencies.
- Define explicit “AI seam” contracts (schemas) even when mocked.
- Provide acceptance tests that are derivable from the spec (Given/When/Then).

Hard rules:

- No stakeholder simulation.
- No expansion beyond demo scope.

## 4.5) Optional next simplification: collapse phases (after vNext proves stable)

Once the 3-phase “no simulation + structured JSON” pipeline is stable, simplify further by reducing calls:

- **2-phase option**
  1) SDD Feature Spec (includes digest + constraints)
  2) Demo Spec + Code Spec (combined artifact; code spec becomes an appendix)

Decision criterion:

- If Phase 1 digest/problem framing is consistently duplicative → shrink it to a minimal summary inside the FeatureSpec.
- If Phase 3 CodeSpec is mostly templated boilerplate → merge it into Phase 2 DemoSpec as an appendix.

## 5) Output format standardisation (structure over prose)

All phases should follow a consistent wrapper:

1. `# <Phase Name>: <Feature Name (if known)>`
2. `## Summary` (short; 5–10 bullets max)
3. `## Spec (JSON)` in a fenced `json` block (the machine contract)
4. `## Details (Markdown)` (only what’s needed to clarify behaviour)
5. `## Open Questions` (only if applicable)
6. `## Version` (`v0.x`, status, timestamp)

This makes outputs:

- easier to validate mechanically
- more stable for downstream steps
- cheaper and faster to generate

## 6) Implementation plan (repo changes)

### 6.1 Prompts (API)

- Update `apps/api/app/services/x_to_demo_pipeline.py`:
  - Remove all instructions requiring “simulate 3–5 stakeholders”, “AI Visionary”, and “3 convergence rounds”.
  - Remove output sections `## Stakeholder Personas` and `## Dialogic Convergence` from all phases.
  - Rename transcript language → generic “Input X”.

### 6.2 Naming + copy (Web + API schemas)

- Web UI: replace “transcript” copy/labels with “Input X”.
- API schema docstrings/descriptions: “Raw input X (any type; often text extracted from documents, notes, transcripts, etc.)”.
- Consider keeping internal variable names stable initially (to reduce diff), but remove transcript semantics in user-visible places.

### 6.3 Compatibility strategy (phase keys)

Pick one:

1) **Low-risk:** keep existing phase keys and artifact filenames; change only titles and content.
2) **Clean:** rename phase keys away from “transcript” (requires updating web UI, tests, and any persisted references).

Recommendation: do (1) first, then (2) in a follow-up if desired.

### 6.4 Validation + tests

- Add lightweight output validators per phase:
  - required headings present
  - JSON block parses
  - JSON contains required top-level keys
- Add regression tests ensuring outputs do **not** include:
  - `Stakeholder Personas`
  - `Dialogic Convergence`
  - “simulate 3-5 … stakeholders”

## 7) Success metrics for this refactor

- Mean tokens per run decreases (target: **-30%** vs baseline on representative inputs).
- Output variance decreases (target: required JSON keys present **100%**).
- “Transcript” terminology is removed from user-facing paths (web + docs).
- Developers can generate tests from Phase 2/3 acceptance criteria without guessing.

## 8) Future extensions (explicitly deferred)

- Optional stakeholder simulation as a feature flag / advanced mode.
- Native multi-modal input support (attachments, OCR, extraction pipelines).
- Spec compilation: generate typed TS/Pydantic schemas from `FeatureSpec` / `DemoSpec`.
