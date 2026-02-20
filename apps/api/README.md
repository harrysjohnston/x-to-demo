# API (`apps/api`)

FastAPI service for local x-to-demo pipeline execution.

## Endpoints

- `GET /health`
- `POST /api/v1/x-to-demo/runs`
- `GET /api/v1/x-to-demo/runs/{run_id}`
- `GET /api/v1/x-to-demo/runs/{run_id}/artifacts/{phase_key}`
- `PUT /api/v1/x-to-demo/runs/{run_id}/artifacts/{phase_key}`
- `POST /api/v1/x-to-demo/runs/{run_id}/resume`
- `GET /api/v1/x-to-demo/runs/{run_id}/artifacts/{phase_key}/download`
- `GET /api/v1/x-to-demo/runs/{run_id}/download`

No auth/database/storage/email subsystems are included.

## Setup

```bash
uv sync --project apps/api --extra dev
```

## Run

```bash
uv run --project apps/api uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Test and lint

```bash
uv run --project apps/api --extra dev python -m ruff check apps/api/app apps/api/tests
uv run --project apps/api --extra dev python -m pytest -q -c apps/api/pyproject.toml apps/api/tests
```
