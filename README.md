# x-to-demo

`x-to-demo` turns raw Input X into structured specifications through a three-phase pipeline (feature spec → demo spec → code spec).

**Prerequisites:** Docker (for `pnpm dev`), or Node/pnpm + Python/uv for running without Docker.

## Quick start

1. Create env file (or run `./scripts/bootstrap` for full setup):

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

Or run without Docker (two terminals):

```bash
pnpm api:dev   # terminal 1
pnpm web:dev   # terminal 2
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

Configure with `X_TO_DEMO_OUTPUT_DIR`. Artifact `phase_key` values: `feature_spec`, `demo_spec`, `code_spec`.

## Local checks

```bash
pnpm lint
pnpm typecheck
pnpm test
```

Run full suite (including e2e):

```bash
pnpm test:full
```

Run CI checks locally (lint, typecheck, tests); add `--pre-commit` to run pre-commit hooks:

```bash
pnpm ci:local
pnpm ci:local --pre-commit
```

## Development

When implementing multimodal inputs (audio or image), enable the **OpenAI docs MCP** in your environment. Use it to look up supported file types and formats for the OpenAI APIs (e.g. `mcp_openaiDeveloperDocs_search_openai_docs` with queries like "image file types supported vision" or "audio file types supported"). The `.agents/skills/multimodal-inputs` skill uses these allowlists for record/capture/upload validation.

Last reviewed: 2026-03-05
