# Outputs

Default to markdown outputs that are useful to build, review, and test the demo. Use another format only when the demo workflow requires it.

## Minimum Output Shape

Produce one concise markdown doc or section set covering the relevant items below.

## Overview

- demo name or working title
- one-sentence purpose
- chosen profile and active modules
- explicit scope boundary

## Headline Demo Items

- one to three headline items
- stable ids when they help traceability
- user-visible proof for each item

## Core Flow

- primary user journey from initial state to successful outcome
- entry point, execution point, and success signals
- declared out-of-scope or non-goals

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
- required modules or remaining reusable skills
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

## Optional Module Sections

Add these only when relevant:

- tooling plan
- multimodal capture and validation plan
- required synthetic assets inventory
- long-running execution notes
