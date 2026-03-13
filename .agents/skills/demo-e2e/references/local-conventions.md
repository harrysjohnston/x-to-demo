# Local Conventions

Use this file only when you need to adapt the generic `demo-e2e` procedure to a specific project.

## What Belongs Here

Local conventions may cover:

- where demo outputs should be stored
- how demo presets or synthetic assets are organized
- how environment variables and setup docs are documented
- which commands run tests, linting, or screenshots
- whether the project expects markdown, JSON, tickets, specs, or some other output wrapper

## How To Use Local Conventions

- Keep the demo contract generic first.
- Apply local naming, file-layout, and command conventions only after the user-facing behavior is defined.
- Treat local paths, wrappers, and artifact shapes as delivery details, not as behavior-level requirements.

## When Conventions Are Missing

- Choose one clear convention instead of several competing ones.
- Document the choice near the implementation or spec output.
- Leave a TODO when a local convention is important but cannot be confirmed safely.
