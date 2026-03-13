# Workflow

Use this workflow to turn rough demo intent into a buildable, testable demo without inventing scope.

## 1. Start From The Smallest Honest Demo

- Resolve the user request into one to three headline demo items.
- Keep the demo AI-first: each headline item should prove a concrete AI value, not just generic app plumbing.
- State what is intentionally out of scope. Do not smuggle in auth, billing, analytics, CI/CD, admin surfaces, or other plumbing unless the demo cannot be shown without them.

If the request is underspecified, narrow the scope and record TODOs or open questions instead of guessing.

## 2. Choose The Demo Profile Early

Pick the closest operating profile up front:

- baseline: text-first demo with no tools, no multimodal input, no required synthetic assets beyond normal presets
- tools: at least one headline item truly needs tool use or iterative planning
- multimodal: audio or image input/output is part of the core demo
- assets: the demo needs project-owned synthetic text, image, audio, or seeded datasets as named assets
- long-running: the implementation work itself needs checkpoints and bounded retries

Only activate the extra modules that the chosen profile actually needs.

## 3. Derive The Core Flow

Think in three passes:

1. boundary: define the headline items, success signals, assumptions, and exclusions
2. contract: define the user-facing flow, views, interactions, walkthrough, presets, and guardrails behavior
3. proof: define implementation notes, AI seams, test coverage, and any local implementation constraints

Each pass should sharpen the same demo, not expand it.

## 4. Keep Decisions Carry-Forward Friendly

Use stable, human-readable identifiers when they materially help carry decisions forward. Common examples:

- headline item ids
- walkthrough step ids
- preset ids
- control ids

Do not create identifier churn between planning, implementation, and tests.

## 5. Define User-Visible Behavior Before Implementation Detail

Before choosing libraries or request shapes, define:

- what the user can input
- what the demo returns or updates
- what each view and control does
- how the walkthrough behaves
- how presets populate state and how execution starts
- what reject, loading, timeout, and recovery states look like

Implementation notes should realize this contract, not replace it.

## 6. Treat Guardrails And AI Seams As First-Class Design Work

For any runtime input that influences execution:

- define deterministic validation
- define server-side guardrails outcomes
- define the main AI call or tool loop only after guardrails pass
- define request/response validation and failure handling at the AI seam

Do not bury these decisions inside later implementation notes.

## 7. Prefer Reuse Over Re-Explanation

When a topic already has another relevant skill, reference it and carry forward only the demo-specific decision:

- which guardrail policy applies here
- which preset set covers which flow
- which labeling surfaces exist in this demo
- which async states matter for this interaction
- which OpenAI calls require mocked and live tests

Keep `demo-e2e` focused on orchestration and cross-cutting demo composition.

## 8. Record TODOs When A Local Fact Is Unclear

Leave a concise TODO or open question when a required fact cannot be confirmed, such as:

- exact preset storage location for a new surface
- exact asset location for a new feature
- whether the local project expects a specific output format
- whether a tool loop is truly required or only convenient

Prefer explicit uncertainty over fabricated local conventions.

## 9. Adapt To Local Conventions Only When Needed

This skill’s default output is markdown. If the current project needs a different output format, artifact shape, or delivery wrapper, treat that as an adaptation step after the demo contract is stable.
