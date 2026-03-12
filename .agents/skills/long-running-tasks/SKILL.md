---
name: long-running-tasks
description: "Run long-running or multi-stage tasks with durable markdown checkpoints, bounded execution loops, resumable state, and explicit cleanup. Use when a task spans many commands, files, tests, or services; may outlive one uninterrupted pass; risks getting stuck or losing context; or needs milestone reporting, markdown worklogs, watchdog checks, and safe resume behavior."
---

# Long-Running Tasks

Run extended work as a controlled sequence, not a single opaque push. Make progress legible, resumable, and bounded so interruptions, retries, and cleanup are part of the workflow instead of surprises.

## Start With A Contract

Before substantial work:

1. Define what counts as done.
2. Define the visible milestones.
3. Define the stop conditions:
   - success
   - blocked
   - waiting on external input
   - exceeded retry budget
4. Decide which markdown files will hold tracking state.

If the task has no clear finish line or no clear stop condition, fix that first.

## Track In Markdown Files

Record long-running work in markdown files, not only in transient tool output. Create a hidden directory for these files, named for the task.

Use at least one durable markdown file for the task, such as:

- `TASK.md` for the overall contract and milestone list
- `WORKLOG.md` for chronological progress notes
- `CHECKPOINTS.md` for resume-oriented state snapshots

The exact filenames can vary, but the tracking medium must be markdown and must live with the task’s working context.

## Use Milestones, Not One Giant Loop

Break the work into milestones with concrete artifacts, such as:

- changed files
- passing tests
- generated reports
- migrated data
- validated deployment state

After each milestone:

1. Record what changed.
2. Record what remains.
3. Record the next intended action.
4. Verify the milestone before moving on.

## Keep Durable State

For work that may be interrupted, maintain a lightweight markdown worklog or checkpoint file. It must answer:

- what milestone is complete
- what is currently in progress
- what command or verification step comes next
- what blockers or anomalies were observed
- what cleanup is still pending

Prefer restart-safe operations and idempotent checkpoints so reruns do not corrupt state.

When practical, separate the markdown records by role:

- contract and milestone plan
- chronological execution log
- latest resume checkpoint

## Use Bounded Execution Loops

For any repeated loop, use this shape:

1. Attempt
2. Observe
3. Verify
4. Reassess
5. Either continue or stop

Never allow open-ended retry loops. Set a retry budget or escalation threshold up front.

## Detect Stalls Early

Treat these as stall signals:

- no artifact changed after repeated attempts
- the same error repeats without new information
- background work has no fresh output for too long
- verification fails in the same way across retries

When stalled:

1. snapshot current state into markdown
2. record the blocker clearly
3. either change strategy or stop

## Separate Execution From Cleanup

Long-running tasks need an explicit closeout phase.

Before declaring completion:

1. stop temporary processes
2. remove temporary artifacts that should not remain
3. verify final outputs
4. capture any residual risks or unfinished edges

Do not rely on the happy path to perform cleanup implicitly.

## Resume Deliberately

On resume:

1. read the latest markdown checkpoint first
2. verify the world still matches the checkpoint
3. re-run the smallest safe verification needed
4. continue from the next incomplete milestone

Do not blindly restart from the top unless the task is intentionally stateless.

## Report Progress Narratively

For long tasks, status updates should always answer:

- what was just completed
- what is running now
- what will happen next
- whether the task is on track, blocked, or degraded

Prefer milestone language over raw command spam.

## Minimum Markdown Contents

Any markdown tracking file set for a long-running task should make these easy to find:

- task goal
- milestone list with status
- latest completed step
- active step
- next step
- blockers
- verification status
- cleanup status

## Read The Reference

Open [references/long-running-patterns.md](references/long-running-patterns.md) when you need:

- checkpoint design heuristics
- bounded-loop rules
- stall detection patterns
- cleanup and resume guidance derived from the harness-engineering page
