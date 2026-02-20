---
name: openai-model-defaults
description: Keeps OpenAI model defaults consistent across demos. Use always unless a demo-specific requirement overrides. Covers Responses API, Agents SDK, and Realtime API defaults plus per-demo override patterns.
---

# Default OpenAI Model Configuration

Keeps model defaults consistent across demos. Apply **always** unless a demo has a specific requirement that overrides.

## When to Apply

- Setting up or modifying any demo that uses OpenAI APIs
- Adding new OpenAI integration (Responses, Agents, Realtime)
- Default: apply. Override only when demo explicitly needs different model or reasoning effort

## Required Outputs

1. **Standard defaults** – use these unless overridden:
   - **Responses API / Agents SDK**: `gpt-5.2` with `reasoning_effort: low`
   - **Realtime API**: `gpt-realtime`

2. **Single override point** – one place to change per-demo (config constant or env var) without refactoring client code

## Implementation Checklist

- [ ] Define defaults in one config module or env schema
- [ ] Expose override via env var (e.g., `OPENAI_MODEL`, `OPENAI_REALTIME_MODEL`) or config constant
- [ ] All OpenAI client code reads from this config; no hardcoded model strings in call sites
- [ ] For Responses/Agents: include `reasoning_effort` default (`low`) in config

## Config Pattern

```text
config/
  model: gpt-5.2 (or env override)
  reasoning_effort: low (or env override)
  realtime_model: gpt-realtime (or env override)

All OpenAI calls → config
```

## Override Paths

| API | Default | Override (env) | Override (constant) |
|-----|---------|----------------|---------------------|
| Responses / Agents | gpt-5.2, reasoning_effort=low | OPENAI_MODEL, OPENAI_REASONING_EFFORT | config.openai_model, config.reasoning_effort |
| Realtime | gpt-realtime | OPENAI_REALTIME_MODEL | config.openai_realtime_model |

Prefer env vars for deployment flexibility; constants are fine for single-demo config files.

## Tests (Required)

| Test | Purpose |
|------|---------|
| **Default config resolves to specified defaults** | With no override set, assert model = gpt-5.2, reasoning_effort = low, realtime_model = gpt-realtime |
| **Override path works** | Set env var or config constant; assert client receives overridden value |

Use env patching or config injection to test both paths. Do not rely on real env in tests.

## Additional Resources

- For implementation examples by framework, see [reference.md](reference.md)
