# X-to-Demo — Master Plan (Living)

## Intent

Make `x-to-demo` a small, reliable pipeline that converts **raw input X (any type)** into:

1. A behaviourally precise **SDD-ready feature spec**
2. A minimal **demo spec** that proves the “moment of value”
3. (Optional) An **implementation-ready code spec** for a runnable demo

## Current Focus

- Pipeline simplification: remove stakeholder simulation; reduce verbosity; increase structure.

## Plans (source of truth)

- Pipeline simplification plan: `/.plans/x-to-demo-pipeline-simplification.md`
- Output contracts (schemas + formats): `/.plans/x-to-demo-output-contracts.md`

## Draft references (working docs)

- SDD-ready feature spec principles: [`draft-feature-spec-principles.md`](./draft-feature-spec-principles.md)
- Feature spec → demo spec prompt: [`draft-feature-to-demo-spec-prompt.md`](./draft-feature-to-demo-spec-prompt.md)

## Scope Guardrails (global)

- **Input X is not “a transcript”.** It can be transcript text, PRD fragments, notes, tickets, emails, docs, etc.
- **No stakeholder simulation** (no personas, no multi-round convergence) until explicitly reintroduced later.
- Specs define intent + behaviour; avoid architecture/UI details unless required for demo realism.
- Prefer deterministic, machine-checkable formats over long narrative.

## Definition of Done (for this refactor)

- Pipeline produces the same number of artifacts as today (unless intentionally collapsed), but **none** contain stakeholder simulation sections.
- All user-facing copy says **Input X** (not “transcript”) unless referencing a specific example.
- Each phase output is structured enough to enable basic automated validation (headings + embedded JSON blocks).
