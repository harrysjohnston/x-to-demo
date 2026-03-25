# Long-Running Execution Practices

## When It Applies

Apply to every demo E2E task as execution guidance.

Use the full durable tracking workflow when the work spans multiple milestones, repeated verification loops, or interruption-prone implementation steps.

Full durable tracking means keeping explicit markdown artifacts for the task contract, ongoing worklog or checkpoints, and closeout notes.

## Extra Responsibilities

- Separate the execution contract from the demo product spec.
- When full tracking is required, track progress in durable markdown files.
- When full tracking is required, use milestone-based execution and bounded retry loops.
- When full tracking is required, record blockers, cleanup, and resume state explicitly.

## When Full Tracking Is Required

- task contract with done criteria and milestones
- worklog and latest checkpoint
- per-milestone verification notes
- explicit closeout or cleanup notes before completion

## Reuse These Skills

- `../../long-running-tasks/SKILL.md` as the authoritative workflow

## Notes

- Do not mix execution bookkeeping into the demo spec itself.
- Use this guidance for the work process, not as a product feature requirement.
- This is always-on execution guidance, not a primary profile or demo module.
