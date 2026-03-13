# Tools Module

## When It Applies

Apply only when a headline demo item truly needs tool use or iterative planning. If the capability can be demonstrated without tools, do not add them.

## Extra Responsibilities

- Make an explicit binary choice:
  - no tools
  - tools backed only by synthetic, project-owned, deterministic data
- Keep tool calls and tool results visible in the UI.
- Ensure default tests can reproduce tool behavior without live third-party dependencies.
- Prevent accidental tool creep after the initial decision.

## Extra Outputs Or Checks

- tooling decision and why tools are required
- tool inventory and the synthetic data source behind each tool
- tool-call and tool-result surfaces in the UI
- mocked testing strategy for tool calls, delays, failures, and displayed logs
- live-test mapping only for the OpenAI calls that remain part of the flow

## Reuse These Skills

- [../reference.md](../reference.md) for tool-result labeling and tool-triggered async states
- `../../openai-live-integration-tests/SKILL.md` for the live-call mapping
- `../../playwright-cli/SKILL.md` when browser automation is needed for verification

## Local Authority That Stays Here

No narrower skill currently owns the tools-mode policy itself, so keep these rules here:

- tools are conditional, not default
- tool data must be synthetic and project-owned
- tool behavior must be mockable and UI-visible
