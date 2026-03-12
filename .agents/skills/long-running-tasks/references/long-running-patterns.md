# Long-Running Task Patterns

Source page:

- `https://openai.com/index/harness-engineering`

This reference distills the page into a reusable operating pattern for long-running agent work.

## Core View

Treat long-running tasks as systems work, not just prompt-following. The job is to keep the task moving, visible, and restartable even when it spans many commands, verification steps, or environment changes.

## Durable Progress

Long-running work should leave behind a durable trail in markdown files:

- latest completed milestone
- current objective
- next planned action
- last successful verification
- last observed blocker

If a task can be interrupted without this state, it is too fragile.

Recommended markdown layout:

- `TASK.md`: task contract, milestones, done criteria
- `WORKLOG.md`: chronological notes and decisions
- `CHECKPOINTS.md`: compact resume snapshots

One file is acceptable for smaller tasks, but the records should still be markdown and should still separate plan, progress, and resume state clearly through headings.

## Milestone Narrative

A good long-running task exposes narrative milestones instead of only internal activity.

Examples:

- scaffold complete
- dependency installation complete
- first failing test reproduced
- fix candidate applied
- verification passed
- cleanup complete

This makes progress understandable to a human and resumable by another agent pass.

## Bounded Loops

The page’s underlying lesson is to avoid indefinite work cycles.

Good loop:

1. try a bounded action
2. inspect the result
3. decide whether to continue, pivot, or stop

Bad loop:

- keep retrying because more effort might help

Every loop needs one of:

- retry cap
- timeout
- explicit pivot condition
- escalation condition

## Watchdogs And Stall Detection

Long-running systems fail quietly unless they are watched.

Add checks for:

- elapsed time since last meaningful output
- repeated identical failure signatures
- unchanged artifacts across retries
- background process still alive but not progressing

When a watchdog trips, do not simply wait longer. Capture state, explain the stall, and decide whether to pivot or stop.

Write the watchdog finding into markdown immediately so the next resume does not rediscover the same stall from scratch.

## Restart Safety

Prefer steps that are safe to replay:

- idempotent setup
- checkpointed migrations
- append-only logs where possible
- explicit verification before mutation

Avoid workflows where a partial previous run makes the next run ambiguous.

## Cleanup As A First-Class Phase

Cleanup is not an afterthought. For long-running work, the closeout phase should include:

- stopping temporary servers or workers
- removing temporary files that should not persist
- preserving logs or artifacts that matter
- recording remaining risks and manual follow-ups

If cleanup is skipped, the task is not truly complete.

## Resume Pattern

A safe resume sequence is:

1. read the latest markdown checkpoint
2. verify environment still matches checkpoint assumptions
3. rerun the smallest relevant verification
4. continue from the next incomplete milestone

Resume should be deliberate, not optimistic.

## Good Status Updates

Status updates for long-running work should be short but information-dense.

They should identify:

- the last completed milestone
- the active step
- the next step
- the reason for any pause or pivot

This keeps the work inspectable without drowning the operator in logs.

## When To Use This Pattern

Use this skill when the task includes one or more of:

- many file edits across multiple phases
- long test or evaluation cycles
- background services or watchers
- migrations or repair scripts
- repeated verification loops
- any task likely to be interrupted and resumed later

## Suggested Markdown Sections

Useful headings for a single-file or multi-file tracking setup:

- `# Goal`
- `# Done Criteria`
- `# Milestones`
- `# Current State`
- `# Worklog`
- `# Blockers`
- `# Next Step`
- `# Verification`
- `# Cleanup`
