# Invariants

These guarantees apply broadly across demo E2E work. Keep them short here and use [reference.md](reference.md) for implementation patterns and examples.

## Scope Discipline

- Keep the demo scoped to the smallest credible proof, usually one to three headline demo items.
- Do not add new product scope while moving from concept to implementation.
- Carry exclusions forward explicitly so plumbing does not re-enter later by accident.

## Stable Traceability

- Use stable, human-readable identifiers where they improve review and test traceability.
- Preserve identifier continuity across headline items, walkthrough steps, presets, controls, and tests when those concepts exist.

## Presets And Seeded Inputs

- Presets are global, user-selectable demo controls, not hidden per-component fixtures.
- The preset selector and its apply/run/reset controls belong in the main input area for the primary flow.
- Presets are apply-only; execution requires an explicit run or submit action.
- Presets must cover every intended happy-path demo flow.
- Presets must never auto-run on load, navigation, or preset selection.
- Shipped presets require mocked-by-default integration coverage before they are treated as done.
- Live preset validation is optional and opt-in unless the demo explicitly requires more.
- Presets and other seeded inputs remain synthetic and reviewable, not hidden runtime state.

## Walkthrough Behavior

- UI demos should include an in-app walkthrough unless the demo explicitly justifies a different onboarding path.
- The walkthrough auto-starts, can be retriggered, can be canceled, and behaves like a bounded state machine rather than presenter prose.
- Walkthrough steps should align to real UI states and success checks.

## Guardrails

- Runtime guardrails are server-side; authoritative guardrail logic never runs in the client.
- Guardrails follow deterministic validation, then exactly one relevance pass, then exactly one safety pass.
- Relevance and safety verdicts use strict structured outputs; do not infer verdicts from free-form text.
- Rejects must short-circuit before the main AI call or tool action.
- Verdict vocabulary stays consistent: `unsupported`, `blocked`, `allowed`.
- Guardrail logs keep only minimal metadata such as request id, timings, verdicts, and parse outcomes.

## AI Seam Validation

- Validate requests before sending them.
- Parse and validate structured responses before turning them into app state.
- Failures at the AI seam must be visible, retryable, and testable.
- No silent fallback or silent data corruption at the seam.

## Labeling Separation

- Generated outputs and synthetic inputs use different labeling systems and must not share the same badge meaning.
- AI/tool outputs use one reusable generated-content indicator with accessible name `Generated content`.
- Seeded or synthetic inputs, datasets, and assets use one chosen base term: `Example`, `Demo`, `Synthetic`, or `Sample`.
- Seeded surfaces expose deterministic reset or reseed behavior using an allowed reset label.

## Async UX

- Async actions follow an explicit state model such as `idle`, `loading`, `streaming`, `success`, `error`, and `timeout`.
- Async actions must show immediate in-flight feedback and working copy.
- Conflicting controls disable during the request and re-enable after completion.
- Timeout and error states must be explicit and retryable.

## Testing Posture

- Mocked tests are the default path.
- Live OpenAI tests are opt-in and skip when credentials or flags are missing.
- Every planned OpenAI runtime call gets its own live integration test when live coverage exists.
- Tests must prove guardrail rejects, preset behavior, walkthrough behavior, async states, and AI seam failures where applicable.
- Tests also prove generated-output labeling, seeded-label visibility, seeded reset behavior, and OpenAI config/default override behavior where those concerns exist.

## OpenAI Baseline

- If the demo uses OpenAI, load `OPENAI_API_KEY` through one shared configuration path and fail fast with a clear, catchable error when it is missing.
- If the demo uses OpenAI, keep model defaults centralized unless the demo explicitly needs an override.
- Keep exactly one override point for model configuration; do not hardcode models in call sites.
- When estimating cost, use a current authoritative pricing source and treat pricing as USD per 1M tokens.

## Browser And Theme Defaults

- Browser-compatible UI is the default posture for demos with a UI.
- Light and dark themes should remain usable and testable unless the demo explicitly has no theme concept.

## Privacy-Safe Debugging

- Do not log raw sensitive input, prompts, model outputs, secrets, or binary payloads.
- Keep debug logging limited to minimal metadata needed to localize failures.
