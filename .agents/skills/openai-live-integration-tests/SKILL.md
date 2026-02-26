---
name: openai-live-integration-tests
description: Defines two-tier OpenAI testing with mocked-by-default and opt-in live integration tests. Use when implementing or specifying OpenAI model call testing. Requires one live integration test per planned model call. Gated by OPENAI_API_KEY and opt-in flag.
---

# OpenAI Live Integration Tests

Defines how to test OpenAI model calls with a two-tier strategy: mocked tests run by default; live integration tests are opt-in and validate real connectivity.

## When to Apply

- Implementing or specifying tests for OpenAI model calls
- CodeSpec testing strategy or openai_test_tiers
- Guardrails, main model calls, or any runtime OpenAI usage

## Two-Tier Model

| Tier | Runs by default | Purpose |
|------|-----------------|---------|
| **Mocked** | Yes | Request formation, schema parsing, guardrail short-circuit, tool-call display. Uses fixtures/snapshots. |
| **Live** | No (opt-in) | Real API calls proving connectivity, parse success, and UI/state updates. |

## Required: One Live Test Per Planned Model Call

**Every planned OpenAI model call must have its own live integration test.**

Planned calls typically include:
- **Relevance guardrail** – one live test
- **Safety guardrail** – one live test
- **Main model call(s)** – one live test per headline item (from `api_usage_by_headline_item`)

Example: demo with 1 headline item and guardrails → 3 live tests (relevance, safety, main).

## Opt-In Gating

Live tests run only when:
- `OPENAI_API_KEY` is set
- Opt-in flag is set (e.g., `RUN_LIVE_OPENAI_TESTS=1`)

When gating conditions are unmet:
- Tests are **skipped** (not failed)
- Default suite must not fail due to missing credentials

## Implementation Checklist

- [ ] Enumerate all planned model calls (guardrails + main per headline)
- [ ] Add one live integration test per call
- [ ] Gate live tests with `OPENAI_API_KEY` and opt-in flag
- [ ] Ensure skipped live tests do not fail the default suite
- [ ] Use low-cost constraints: minimal tokens, default models, deterministic assertions where feasible

## Cost and Safety Constraints

- Minimal calls (one per planned call; no redundant coverage)
- Default models; low token usage
- Deterministic assertions on status, parse result, and key UI/state updates where possible

## Run Command Example

```bash
OPENAI_API_KEY=... RUN_LIVE_OPENAI_TESTS=1 uv run pytest -q -c apps/api/pyproject.toml apps/api/tests -k live_openai_smoke
```

## Additional Resources

- For schema definitions and test payload examples, see [reference.md](reference.md)
