# Rule Reduction Loop Task

## Goal
Implement the end-of-run reduction loop for rule refinement with an editor-critic pattern, reduction pass tracking, artifact persistence, and tests.

## Done Criteria
- Reduction models are added and wired into the run result.
- Reduction prompts and service logic are implemented.
- Reduction artifacts, metrics, and manifest output are persisted.
- Tests cover the new reduction behavior.

## Milestones
- [x] Add reduction models and exports.
- [x] Add reduction prompt builders and artifact helpers.
- [x] Implement reduction loop in the service.
- [x] Extend persistence and tests.

## Stop Conditions
- Success: all milestones complete and targeted tests pass.
- Blocked: a required design choice or existing contract prevents safe implementation.
- Waiting: external clarification is required.
- Retry budget: stop after repeated failing verification without new information.
