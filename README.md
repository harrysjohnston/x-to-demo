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
pnpm ci:local
```

Or run individual jobs:

```bash
./scripts/ci-local --pre-commit   # pre-commit on all files (CI checks everything, not just staged)
./scripts/ci-local --docker       # Docker build + health checks
```

**Why CI might fail when local checks pass:**

- **Pre-commit**: CI runs `pre_commit run --all-files`; a normal `pre-commit run` only checks staged files, so unstaged or untracked issues are missed.
- **Pre-commit**: CI installs deps from repo root with `uv pip install --system`; your venv or tool versions may differ.
- **Docker**: CI runs on `ubuntu-latest`; platform/arch differences (e.g. macOS vs Linux) can cause build or runtime failures.

## Current Prototype Constraints

- Input X currently optimized for text-like raw inputs.
- One pipeline run produces one code spec artifact set.
- Pipeline is synchronous per request.
- Output is designed for demo-build handoff, not production architecture.
- Phase-2 `DemoSpec` artifacts now require `interaction_contracts` that enumerate every per-screen interactive control with behavior, observable effects, enable/disable rules, and loading-state expectations.
- Phase-2 `DemoSpec` artifacts now require `synthetic_demo_inputs.required_assets` (empty list allowed) to inventory every required synthetic text/image/audio asset with purpose, usage mapping, format/size constraints, and explicit synthetic labels.
- Phase-3 `CodeSpec` artifacts now require `asset_generation_plan` describing per-modality OpenAI API/model choices, local generation scripts/commands, repo storage/naming, app loading/labeling behavior, mandatory guardrails, and `no_live_generation_on_startup=true`.
- Phase-3 `CodeSpec` artifacts now require `testing_strategy.interaction_test_matrix` that maps each control id to enabled/disabled/loading assertions under the no-inert-controls rule.
- Phase-3 `CodeSpec` artifacts now require `testing_strategy.synthetic_assets_validation` proving synthetic assets exist, pass basic file sanity checks, and that seeded startup flows do not depend on live generation calls.
- Phase-3 `CodeSpec` artifacts now require `openai_integration.request_validation` describing preflight request checks, fail-fast behavior, and clear UI-visible error handling when validation fails.
- Phase-3 `CodeSpec` artifacts now require `testing_strategy.openai_test_tiers` defining mocked tests that run by default and opt-in live smoke tests gated by `OPENAI_API_KEY` (and optional explicit flags) that can be skipped without failing the default suite.
- Artifact schema version is now `0.3`; pre-`0.3` runs may fail edit/resume validation due stricter required fields and should be regenerated when needed.

## Related Docs

- Master plan: `/.plans/x-to-demo-master-plan.md`
- Pipeline simplification plan: `/.plans/x-to-demo-pipeline-simplification.md`
- Output contracts: `/.plans/x-to-demo-output-contracts.md`
- Deployment: `/docs/deployment.md`
- Architecture notes: `/architecture_decisions.md`

Last reviewed: 2026-02-20
