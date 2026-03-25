# Outputs

Default to markdown outputs that are useful to build, review, and test the demo. Use another format only when the demo workflow requires it.

## Minimum Output Shape

Produce one concise markdown doc or section set covering the relevant items below.

This minimum output shape is the demo contract for the work: the behavior-first spec the implementation should realize.

## Overview

- demo name or working title
- one-sentence purpose
- primary profile
- additional demo modules, if any
- explicit scope boundary

Primary profile should name the closest operating profile: `baseline`, `tools`, `multimodal`, or `assets`.

## Headline Demo Items

- one to three headline items
- stable ids when they help traceability
- user-visible proof for each item

Each headline item should be one top-level user-visible capability or scenario the demo is intended to prove.

User-visible proof should state what an observer can see in the demo that proves the item works.

## Core Flow

- primary user journey from initial state to successful outcome
- entry point, execution point, and success signals
- declared out-of-scope or non-goals

Entry point should state where the user starts. Execution point should state the control or event that triggers guardrails and the main flow.

Success signals should be observable outcomes that show the flow reached its intended result.

## Views And Interactions

- key views or surfaces
- primary controls and what each does
- important enable/disable rules
- generated-output indicator surfaces
- seeded/synthetic labeling surfaces
- any first-run or default state expectations
- loading, streaming, timeout, and recovery states

## Walkthrough

- auto-start behavior
- retrigger and cancel behavior
- ordered step inventory
- what each step highlights or verifies

## Presets And Synthetic Inputs

- shipped presets or seeded inputs
- which flow each preset covers
- apply/run/reset behavior
- any seeded datasets or seeded file examples

Shipped presets are the presets intended to be available in the delivered demo.

## Guardrails And AI Behavior

- deterministic validation summary
- relevance and safety behavior
- canonical reject outcomes and user messaging posture
- main AI call or tool loop summary
- AI seam request/response validation notes

## Implementation Notes

- major server/client boundaries
- key state machines
- reusable UI indicators and labeling patterns
- shared OpenAI config loader and model-default override point
- pricing or cost-estimation note when model choice matters
- which additional demo modules are active and which external skills the work depends on
- any local integration constraints

## Testing Expectations

- mocked-by-default coverage expectations
- opt-in live coverage expectations
- walkthrough, async UX, reject paths, and AI seam failure checks
- generated-output label coverage
- seeded-label and reset coverage
- OpenAI config/default and override coverage when OpenAI calls exist
- concrete commands when they are known and relevant

## Open Questions / TODOs

- unresolved local implementation facts
- choices that need user confirmation
- intentionally deferred work within scope

## Additional Module Sections

Add these only when the corresponding additional demo modules are active:

- tooling plan
- multimodal capture and validation plan
- required synthetic assets inventory

## Execution Tracking

Add this only when full long-running tracking is required for the work:

- task contract with done criteria and milestones
- worklog or latest checkpoint summary
- per-milestone verification notes
- closeout or cleanup notes when relevant
