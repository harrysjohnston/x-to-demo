# Long-Running Module

## When It Applies

Apply when the demo work spans multiple milestones, repeated verification loops, or interruption-prone implementation steps.

## Extra Responsibilities

- Separate the execution contract from the demo product spec.
- Track progress in durable markdown files.
- Use milestone-based execution and bounded retry loops.
- Record blockers, cleanup, and resume state explicitly.

## Extra Outputs Or Checks

- task contract with done criteria and milestones
- worklog and latest checkpoint
- per-milestone verification notes
- explicit closeout or cleanup notes before completion

## Reuse These Skills

- `../../long-running-tasks/SKILL.md` as the authoritative workflow

## Notes

- Do not mix execution bookkeeping into the demo spec itself.
- Use this module for the work process, not as a product feature requirement.
