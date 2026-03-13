---
name: demo-e2e
description: "Create demos end-to-end using a thin orchestrator, reusable invariants, conditional modules, and explicit delegation to other relevant skills."
---

# Demo E2E

Use this skill to scope, design, specify, or implement a demo end-to-end.

## When To Apply

- The user wants a demo scoped, designed, implemented, or specified end-to-end
- The work needs demo-specific guardrails, presets, walkthrough, AI behavior, and testing to stay aligned
- You need one orchestration layer that composes other relevant skills instead of duplicating them

## Expected Outputs

- A scoped demo plan or implementation-ready spec in markdown
- Baseline demo artifacts described in [workflow.md](workflow.md) and [outputs.md](outputs.md)
- Conditional module outputs only when the demo actually needs them

Default to clear markdown outputs unless a consuming workflow requires a different format.

## Always-On Reading

1. [workflow.md](workflow.md)
2. [outputs.md](outputs.md)
3. [invariants.md](invariants.md)
4. [modules/baseline.md](modules/baseline.md)
5. [reference.md](reference.md) when you need implementation patterns for guardrails, presets, labeling, async UI, or OpenAI setup

## Conditional Modules

- [modules/tools.md](modules/tools.md): only when a headline demo item truly needs tool use or iterative planning
- [modules/multimodal.md](modules/multimodal.md): only when audio or image input/output is part of the demo
- [modules/assets.md](modules/assets.md): only when the demo needs project-owned synthetic assets or seeded datasets beyond trivial inline text
- [modules/long-running.md](modules/long-running.md): only when the work itself is interruption-prone or milestone-driven

## Reuse Existing Skills

Use [references/existing-skills.md](references/existing-skills.md) as the concern-to-skill map. Prefer those skills as the canonical homes for topic-specific implementation guidance.

Use [references/local-conventions.md](references/local-conventions.md) only when you need to adapt the generic procedure to local project conventions.

## Execution Flow

1. Lock scope to the smallest honest demo boundary, usually one to three headline demo items.
2. Choose the active profile and modules before detailing UI or API behavior.
3. Carry forward stable identifiers where they improve traceability across headline items, views, walkthrough steps, presets, controls, and tests.
4. Reuse existing skills for guardrails, presets, labeling, async UX, model config, credentials, and testing instead of restating them.
5. Produce markdown outputs that define the demo contract, implementation notes, and proof plan.
6. Adapt the resulting demo contract to local project conventions only after the user-facing behavior is clear.
