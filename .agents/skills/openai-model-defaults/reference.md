# OpenAI Model Defaults – Implementation Reference

## Python (pydantic-settings)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAIConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPENAI_", extra="ignore")

    model: str = "gpt-5.2"
    reasoning_effort: str = "low"
    realtime_model: str = "gpt-realtime"


config = OpenAIConfig()
```

Usage:

```python
from openai import OpenAI

client = OpenAI()
response = client.responses.create(
    model=config.model,
    reasoning=config.reasoning_effort,
    input="...",
)
```

## Node / TypeScript

```typescript
const config = {
  model: process.env.OPENAI_MODEL ?? "gpt-5.2",
  reasoningEffort: process.env.OPENAI_REASONING_EFFORT ?? "low",
  realtimeModel: process.env.OPENAI_REALTIME_MODEL ?? "gpt-realtime",
};
```

Or with a config module:

```typescript
// config/openai.ts
export const openaiConfig = {
  model: process.env.OPENAI_MODEL ?? "gpt-5.2",
  reasoningEffort: (process.env.OPENAI_REASONING_EFFORT ?? "low") as "low" | "medium" | "high",
  realtimeModel: process.env.OPENAI_REALTIME_MODEL ?? "gpt-realtime",
};
```

## Unit Tests

**Default config resolves to specified defaults:**

```python
def test_openai_config_defaults():
    from app.config import OpenAIConfig
    # Ensure no env override
    config = OpenAIConfig(_env_file=None)
    assert config.model == "gpt-5.2"
    assert config.reasoning_effort == "low"
    assert config.realtime_model == "gpt-realtime"
```

```python
def test_openai_config_defaults_with_fresh_env(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_REASONING_EFFORT", raising=False)
    monkeypatch.delenv("OPENAI_REALTIME_MODEL", raising=False)
    from app.config import OpenAIConfig
    config = OpenAIConfig()
    assert config.model == "gpt-5.2"
    assert config.reasoning_effort == "low"
    assert config.realtime_model == "gpt-realtime"
```

**Override path works:**

```python
def test_openai_config_override(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "high")
    from app.config import OpenAIConfig
    config = OpenAIConfig()
    assert config.model == "gpt-5-mini"
    assert config.reasoning_effort == "high"
```

## .env.example

```bash
# OpenAI model defaults (optional overrides)
# OPENAI_MODEL=gpt-5.2
# OPENAI_REASONING_EFFORT=low
# OPENAI_REALTIME_MODEL=gpt-realtime
```
