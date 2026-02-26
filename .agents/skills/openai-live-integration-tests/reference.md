# OpenAI Live Integration Tests – Reference

## Planned Model Calls (from CodeSpec)

| Source | Count | Example |
|--------|-------|---------|
| Relevance guardrail | 1 | `runtime_guardrails_plan.relevance_model_call` |
| Safety guardrail | 1 | `runtime_guardrails_plan.safety_model_call` |
| Main call per headline | 1 per item | `api_usage_by_headline_item[*].selected_api` |

**Total live tests** = 2 (guardrails) + number of headline items.

## LiveSmokeTestTier Schema (CodeSpec)

```python
class LiveSmokeTestTier(StrictSchemaModel):
    opt_in: Literal[True]  # Must be true
    run_condition: str     # OPENAI_API_KEY + RUN_LIVE_OPENAI_TESTS=1
    skip_behavior: str     # Skipped when not opted in; no failure
    cost_and_safety_constraints: list[str]
    what_it_verifies: list[str]  # Must include per-call coverage
    commands_or_how_to_run: list[str]
```

## what_it_verifies (Per-Call Coverage)

`what_it_verifies` must explicitly list each planned call and its live test:

```json
{
  "what_it_verifies": [
    "Relevance guardrail: real request succeeds, parses RelevanceVerdict.",
    "Safety guardrail: real request succeeds, parses SafetyVerdict.",
    "Main call (headline X): real request succeeds, parses expected schema, UI updates."
  ]
}
```

One entry per planned model call.

## cost_and_safety_constraints

```json
{
  "cost_and_safety_constraints": [
    "One live test per planned model call; no redundant coverage.",
    "Use default models and minimal token prompts.",
    "Assert on status, parse result, and key UI/state updates."
  ]
}
```

## Pytest Gating Example

```python
import os
import pytest

def requires_live_openai():
    if not os.getenv("OPENAI_API_KEY") or os.getenv("RUN_LIVE_OPENAI_TESTS") != "1":
        pytest.skip("Live OpenAI tests require OPENAI_API_KEY and RUN_LIVE_OPENAI_TESTS=1")

@pytest.mark.live_openai_smoke
def test_relevance_guardrail_live():
    requires_live_openai()
    # ... real relevance call, assert parse success

@pytest.mark.live_openai_smoke
def test_safety_guardrail_live():
    requires_live_openai()
    # ... real safety call, assert parse success

@pytest.mark.live_openai_smoke
def test_main_call_headline_x_live():
    requires_live_openai()
    # ... real main call, assert parse + UI update
```
