# Baseline Module

## When It Applies

Apply to every demo E2E unless the user is asking for something narrower than a runnable demo.

## Responsibilities

- Define the smallest honest demo scope and explicit non-goals.
- Produce the core flow, views, interactions, walkthrough, presets, guardrails summary, AI seam notes, and testing expectations.
- Apply the baseline demo decisions directly: server-side guardrails only, one relevance and one safety verdict, global selectable presets, and mocked integration coverage proving shipped presets can reach their intended demo flows.
- Keep generated-output labeling, synthetic-input labeling, async UX, OpenAI config, model defaults, and cost awareness in view from the start rather than bolting them on later.
- Ensure the demo is browser-compatible and appears and operates correctly in both light and dark themes when a UI exists.

## Required Outputs Or Checks

- headline demo items with success signals
- a user-facing core flow
- walkthrough behavior and step coverage
- preset coverage with apply/run/reset semantics
- guardrails and AI seam summary
- generated-output indicator plan and seeded-label plan
- OpenAI env/config/defaults plan when the demo uses OpenAI
- cost-estimation note when model choice affects the plan
- mocked-by-default test expectations
- opt-in live test expectations when OpenAI calls are present

## Local Reference

- [../reference.md](../reference.md)
- `../../openai-live-integration-tests/SKILL.md`

## Local Authority That Stays Here

Keep these topics in `demo-e2e`:

- foundational baseline demo decisions about guardrails and preset posture
- generated-output indicator behavior, accessibility, and test coverage
- seeded or synthetic input labeling and reset behavior
- async loading, streaming, timeout, and retry behavior
- OpenAI env loading, fail-fast behavior, model defaults, override rules, and pricing posture
- walkthrough contract and state-machine expectations
- cross-cutting scope discipline
- cross-section traceability expectations
