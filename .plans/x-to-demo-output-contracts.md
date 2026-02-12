# X-to-Demo — Output Contracts (vNext)

Goal: make each phase output **machine-interpretable by construction** while remaining readable.

All phase artifacts remain markdown, but must include a single **authoritative JSON block** under `## Spec (JSON)`.

Related drafts:

- SDD-ready feature spec principles: [`draft-feature-spec-principles.md`](./draft-feature-spec-principles.md)
- Feature spec → demo spec prompt: [`draft-feature-to-demo-spec-prompt.md`](./draft-feature-to-demo-spec-prompt.md)

## Shared conventions

- Every JSON payload includes:
  - `schema_version` (string; e.g. `"0.1"`)
  - `feature_name` (string | null)
  - `status` (enum: `"draft" | "review" | "ready"`)
  - `source` (object; provenance + traceability)

Example `source`:

```json
{
  "x_source_type": "unknown",
  "inputs": ["x_input", "additional_context"],
  "notes": "X may be any type; treat as raw material."
}
```

Current pipeline note:

- Phases **1 & 2 are merged**: the pipeline now emits **3 phase artifacts**:
  1) `FeatureSpec`
  2) `DemoSpec`
  3) `CodeSpec`
- The former `IntentBrief` is no longer emitted as a standalone artifact. If you still want that
  structure, include it as optional fields inside `FeatureSpec` or reintroduce a dedicated phase.

## (Legacy) `IntentBrief` schema (JSON)

Required top-level keys:

- `primary_problem` (object)
- `secondary_problems` (array)
- `affected_roles` (array of strings)
- `assumptions` (array)
- `constraints` (array)
- `open_questions` (array)

Minimal example:

```json
{
  "schema_version": "0.1",
  "feature_name": null,
  "status": "draft",
  "source": { "x_source_type": "notes", "inputs": ["x_input"] },
  "primary_problem": {
    "statement": "Users cannot reliably turn messy inputs into a demo plan.",
    "why_it_matters": "Time wasted; inconsistent demos.",
    "who_is_struggling": ["PM", "Engineer"]
  },
  "secondary_problems": [],
  "affected_roles": ["PM", "Engineer", "Designer"],
  "assumptions": ["We can treat X as text for vNext."],
  "constraints": ["No stakeholder simulation."],
  "open_questions": ["What demo format is preferred (screens vs scripted chat)?"]
}
```

## Phase 1 — `FeatureSpec` schema (JSON)

Design note: `FeatureSpec` should satisfy the behavioural + testability principles in [`draft-feature-spec-principles.md`](./draft-feature-spec-principles.md).

Required top-level keys:

- `intent` (object: problem, objective, desired_outcome, target_persona)
- `external_behavior` (object: inputs, outputs, states, errors)
- `acceptance_criteria` (array of Given/When/Then objects)
- `invariants` (array)
- `success_metrics` (array)
- `versioning` (object: version, changelog)

Acceptance criteria object shape:

```json
{
  "given": "…",
  "when": "…",
  "then": ["…", "…"]
}
```

## Phase 2 — `DemoSpec` schema (JSON)

Design note: `DemoSpec` shape should align with the output format described in [`draft-feature-to-demo-spec-prompt.md`](./draft-feature-to-demo-spec-prompt.md).

Required top-level keys:

- `demo_overview` (string)
- `demo_scope` (object: in_scope, out_of_scope)
- `demo_format` (string)
- `core_flow_steps` (array of 5–7 step strings or objects)
- `success_signals` (array)
- `example_copy` (array; minimal interaction/screen copy)

## Phase 3 — `CodeSpec` schema (JSON)

Required top-level keys:

- `demo_overview` (string)
- `tech_stack` (object)
- `project_changes` (array; files/modules touched)
- `components` (array)
- `state_model` (object)
- `ai_seam` (object: schemas, contracts, mock_strategy)
- `acceptance_tests` (array of Given/When/Then objects)
- `non_goals` (array)

## Validation expectations

“Valid output” for each phase means:

1) Markdown contains `## Spec (JSON)` with exactly one JSON code block.
2) JSON parses.
3) JSON contains the required keys for that phase.
4) The markdown does **not** include stakeholder simulation sections.
