---
name: openai-env-config
description: Configures OpenAI API credentials from environment with fail-fast validation. Use when building or modifying demos that call OpenAI APIs, when setting up local development, or when the user mentions OPENAI_API_KEY, .env, or environment configuration for OpenAI.
---

# OpenAI Environment-Based Key Loading

Provides a consistent, low-friction way to configure OpenAI credentials locally. Ensures fail-fast behavior with clear errors when the key is missing.

## When to Apply

- Any demo that calls OpenAI APIs
- Setting up local development for OpenAI-dependent projects
- User asks about OPENAI_API_KEY, .env setup, or credential configuration

## Required Outputs

The implementation must produce:

1. **Read OPENAI_API_KEY from environment** – via framework's standard mechanism
2. **`.env.example`** – documents required variables (OPENAI_API_KEY and any optional ones)
3. **README section** – env file setup, where to place it, and how to run
4. **Fail-fast behavior** – clear UI/API error when key is missing (not a generic 500)

## Implementation Checklist

- [ ] Load env vars via framework's standard mechanism (e.g., `dotenv` in Node, `python-dotenv` or `pydantic-settings` in Python). Do not add auth/billing/other concerns.
- [ ] Provide a **single configuration module** used by all OpenAI client code
- [ ] Validate presence of key at **startup** or **before first call**
- [ ] Return a structured error (e.g., 503 or 400) with a clear message like "OPENAI_API_KEY is not configured" – not an unhandled exception

## Quick Reference

| Framework | Env loader | Config pattern |
|-----------|------------|----------------|
| Python (FastAPI/Flask) | `pydantic-settings` or `python-dotenv` | Single `Settings` class or `config` module |
| Node/Express | `dotenv` | Single module exporting `process.env.OPENAI_API_KEY` after validation |
| Next.js | Built-in `.env.local` | `process.env.OPENAI_API_KEY` (validate in API route or server component) |

## .env.example Template

```bash
# OpenAI (required for demos that call OpenAI APIs)
OPENAI_API_KEY=
```

Add optional vars (e.g., model, output dir) as needed. Never commit `.env`; add it to `.gitignore`.

## README Section Template

```markdown
## Environment Setup

1. Copy the example env file:
   ```bash
   cp .env.example .env
   ```
2. Set your OpenAI API key in `.env`:
   ```bash
   OPENAI_API_KEY=<your-key>
   ```
3. Run the app:
   ```bash
   [your run command]
   ```

Place `.env` in the project root (or the directory from which the app is started).
```

## Tests (Required)

| Test | Purpose |
|------|---------|
| Config loader returns key when set | Assert `get_openai_api_key()` or equivalent returns the value when `OPENAI_API_KEY` is in env |
| Missing key triggers explicit error | Assert that when key is absent/empty, the loader raises a clear, catchable error (e.g., `ValueError`, `RuntimeError`, or custom `OpenAIConfigError`) with a message mentioning `OPENAI_API_KEY` |

Use env patching (e.g., `monkeypatch`, `patch.dict(os.environ)`) to control env state in tests. Do not rely on real `.env` files in tests.

## Additional Resources

- For framework-specific code examples, see [reference.md](reference.md)
