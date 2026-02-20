# OpenAI Env Config – Framework Reference

## Python (pydantic-settings)

**config.py:**

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key (required for pipeline)",
    )


settings = Settings()
```

**Validation helper (call at startup or before first use):**

```python
def require_openai_api_key() -> str:
    key = settings.openai_api_key
    if not key or not key.strip():
        raise ValueError("OPENAI_API_KEY is not configured. Set it in .env")
    return key
```

**FastAPI – fail-fast at startup:**

```python
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
def validate_openai_config():
    require_openai_api_key()
```

**FastAPI – lazy validation in dependency:**

```python
def get_openai_client():
    api_key = require_openai_api_key()
    return OpenAI(api_key=api_key)
```

**Return clear HTTP error (not 500):**

```python
# In exception handler or dependency
from fastapi import HTTPException

if not settings.openai_api_key:
    raise HTTPException(
        status_code=503,
        detail="OPENAI_API_KEY is not configured. Add it to .env and restart.",
    )
```

**Unit tests:**

```python
def test_config_returns_key_when_set(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
    from app.config import Settings
    s = Settings()
    assert s.openai_api_key == "sk-test-123"

def test_missing_key_raises_error(monkeypatch):
    from app.config import settings, require_openai_api_key
    monkeypatch.setattr(settings, "openai_api_key", None)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        require_openai_api_key()
```

---

## Python (python-dotenv only)

```python
from dotenv import load_dotenv
import os

load_dotenv()

def get_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise ValueError("OPENAI_API_KEY is not configured. Set it in .env")
    return key
```

---

## Node.js (dotenv)

**config.js or config.ts:**

```javascript
require("dotenv").config();

function getOpenAIApiKey() {
  const key = process.env.OPENAI_API_KEY?.trim();
  if (!key) {
    throw new Error("OPENAI_API_KEY is not configured. Set it in .env");
  }
  return key;
}

module.exports = { getOpenAIApiKey };
```

**Express – middleware or route guard:**

```javascript
app.use((req, res, next) => {
  try {
    getOpenAIApiKey();
    next();
  } catch (err) {
    res.status(503).json({
      error: { code: "config_error", message: err.message },
    });
  }
});
```

**Unit tests (Node):**

```javascript
test("returns key when set", () => {
  process.env.OPENAI_API_KEY = "sk-test-123";
  expect(getOpenAIApiKey()).toBe("sk-test-123");
});

test("throws when key missing", () => {
  delete process.env.OPENAI_API_KEY;
  expect(() => getOpenAIApiKey()).toThrow("OPENAI_API_KEY");
});
```

---

## Next.js

- Use `.env.local` in project root (Next.js loads it automatically).
- Validate in API route or server component before calling OpenAI:

```javascript
// app/api/chat/route.js
const key = process.env.OPENAI_API_KEY?.trim();
if (!key) {
  return Response.json(
    { error: { message: "OPENAI_API_KEY is not configured" } },
    { status: 503 }
  );
}
```
