# API (`apps/api`)

FastAPI + SQLModel backend for the fullstack template. Use this app as the API when bootstrapping or extending the template.

## What’s included

- **Health** – `GET /health`
- **Auth** – JWT (access + refresh), login/register, protected routes
- **Users** – CRUD, password hash, linked to auth
- **SSE** – Server-Sent Events endpoint for realtime updates
- **Uploads** – Presigned URL generation (S3; GCS/Azure adapters available)
- **Email** – Jinja2 + MJML templates (welcome, password reset), configurable transport
- **Database** – PostgreSQL via SQLModel, Alembic migrations
- **Quality** – Pytest (unit + integration), Ruff, pre-commit

## Development

### Setup

Use the repo’s virtual environment and install the API in editable mode with dev deps:

```bash
# From repository root
source .venv/bin/activate
uv pip install -e "apps/api[dev]"
```

If the venv doesn’t exist yet, create it from the root: `uv venv .venv` then activate and install (or run `./scripts/bootstrap`).

### Run locally (no Docker)

```bash
# From repository root
cp config/env.example .env
# Set DATABASE_URL or POSTGRES_* for your Postgres instance

cd apps/api
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Config reads `.env` from the current working directory. Without Postgres locally, use `pnpm dev:db` from the root to start the stack with the `db` profile.

### Tests

```bash
# From apps/api (with venv activated from root)
pytest

# With coverage
pytest --cov=app --cov-report=html

# Filter by marker
pytest -m unit
pytest -m "not slow"

# Single file
pytest tests/test_health.py
```

### Lint and format

```bash
ruff check app/ tests/
ruff format app/ tests/
ruff check --fix app/ tests/
```

Pre-commit is configured at the repo root; run `pre-commit install` from the root to run Ruff before each commit.

## Project layout

- `app/` – FastAPI app, routers (auth, users, sse, uploads), models, schemas, storage adapters, email
- `alembic/` – Migrations
- `tests/` – Pytest tests
- `scripts/migrate.py` – Migration runner for deployment
