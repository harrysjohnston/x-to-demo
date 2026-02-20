# x-to-demo

`x-to-demo` turns raw Input X into structured specifications through a three-phase pipeline.

## What is retained

- Local web app (`apps/web`) for running pipeline jobs and reviewing artifacts.
- Local API (`apps/api`) that runs the x-to-demo pipeline and saves artifacts.
- Pipeline schemas, canonical JSON/XML rendering, and resumable run artifacts.
- Web/API tests, linting, and pre-commit checks.

## What was removed

- Auth and users
- Database and migrations
- Upload/storage services (S3/MinIO)
- Email pipeline
- Deployment/infra template assets

## Quick start

1. Create env file:

```bash
cp config/env.example .env
```

2. Set your OpenAI key in `.env`:

```bash
OPENAI_API_KEY=<your-key>
```

3. Start local stack:

```bash
pnpm dev
```

4. Open:

- Web: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`

## API surface

- `GET /health`
- `POST /api/v1/x-to-demo/runs`
- `GET /api/v1/x-to-demo/runs/{run_id}`
- `GET /api/v1/x-to-demo/runs/{run_id}/artifacts/{phase_key}`
- `PUT /api/v1/x-to-demo/runs/{run_id}/artifacts/{phase_key}`
- `POST /api/v1/x-to-demo/runs/{run_id}/resume`
- `GET /api/v1/x-to-demo/runs/{run_id}/artifacts/{phase_key}/download`
- `GET /api/v1/x-to-demo/runs/{run_id}/download`

All endpoints are local-only and unauthenticated.

## Artifacts

By default, artifacts are written under:

`artifacts/x-to-demo/<run-id>/`

Configure with `X_TO_DEMO_OUTPUT_DIR`.

## Local checks

```bash
pnpm lint
pnpm typecheck
pnpm test
```

Run pre-commit hooks over all files:

```bash
uv run --project apps/api --extra dev python -m pre_commit run --all-files
```
