# x-to-demo

`x-to-demo` turns raw Input X into a runnable-demo code spec via a three-phase, opinionated pipeline.

## What It Does

- Accepts raw Input X from the web app (notes, docs, tickets, emails, transcripts, and similar text input).
- Runs a chained LLM pipeline (Responses API) across three major phases:
- Phase 1: Input -> SDD Feature Spec
- Phase 2: Feature Spec -> Demo Spec
- Phase 3: Demo Spec -> Code Spec
- Returns all phase artifacts in the UI.
- Saves phase markdown outputs and the final code spec to disk.

## Quick Start

1. Copy environment config.

```bash
cp config/env.example .env
```

2. Set your OpenAI key in `.env`.

```bash
OPENAI_API_KEY=<your-key>
```

3. Start the stack.

```bash
pnpm dev:full
```

4. Open:
- Web: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`

## Using The Product

1. Register or sign in on the landing page.
2. Upload an Input X file or paste raw Input X text into the `Input X` panel.
3. Optionally provide:
- `Feature name hint`
- `Additional context`
4. Click `Run pipeline`.
5. Review phase artifacts and copy the final code spec.
6. Find saved artifacts under `artifacts/x-to-demo/<run-id>/` (or your configured output dir).

## API Endpoint

`POST /api/v1/x-to-demo/runs` (auth required)

Request body:

```json
{
  "x_input": "Raw Input X text...",
  "additional_context": "Optional constraints/context",
  "feature_name_hint": "Optional feature label",
  "model": "gpt-5.2",
  "reasoning_effort": "high"
}
```

Response (enveloped):

- `run_id`
- `created_at`
- `model`
- `reasoning_effort`
- `artifacts[]` (`phase_key`, `title`, `markdown`, `saved_path`)
- `final_code_spec`
- `final_code_spec_path`

## Artifact Persistence

Default location:

`artifacts/x-to-demo/<run-id>/`

Typical files:

- `01-phase-1-input-to-feature-spec.md`
- `02-phase-2-feature-spec-to-demo-spec.md`
- `03-phase-3-demo-spec-to-code-spec.md`
- `run-manifest.json`

Note: phase order is defined by artifact ordering and titles.

Configure output path with `X_TO_DEMO_OUTPUT_DIR`.

## Project Structure

```text
apps/web/                  # Next.js frontend (auth + pipeline workspace UI)
apps/api/                  # FastAPI backend (auth, pipeline endpoint, persistence)
apps/api/app/services/     # X-to-Demo pipeline orchestration service
.plans/                    # Master plan + sub-plans
.plans/milestones/         # Milestone trackers for plan execution
config/env.example         # Environment variable template
```

## Environment Variables (Pipeline)

- `OPENAI_API_KEY` (required)
- `X_TO_DEMO_MODEL` (default: `gpt-5.1`; supported: `gpt-5.2`, `gpt-5.1`, `gpt-5-mini`, `gpt-5-nano`, `gpt-4.1-nano`)
- `X_TO_DEMO_OUTPUT_DIR` (default: `artifacts/x-to-demo`)
- `X_TO_DEMO_STORE_RESPONSES` (default: `false`)
- `X_TO_DEMO_MAX_INPUT_CHARS` (default: `60000`)
- Per-run `reasoning_effort` (optional): for `gpt-5.2` use `none|low|medium|high|xhigh`; for other GPT-5 models use `minimal|low|medium|high`

## Local Development Commands

- `pnpm dev` -> web + api
- `pnpm dev:db` -> web + api + db
- `pnpm dev:full` -> web + api + db + storage + MailHog
- `pnpm dev:down` -> stop all dev services

## Tests And Lint

```bash
# Web
pnpm -C apps/web lint
pnpm -C apps/web typecheck
pnpm -C apps/web test

# API
uv run ruff check apps/api/app apps/api/tests
uv run pytest -q -c apps/api/pyproject.toml apps/api/tests
```

## Current Prototype Constraints

- Input X currently optimized for text-like raw inputs.
- One pipeline run produces one code spec artifact set.
- Pipeline is synchronous per request.
- Output is designed for demo-build handoff, not production architecture.

## Related Docs

- Master plan: `/.plans/x-to-demo-master-plan.md`
- Pipeline simplification plan: `/.plans/x-to-demo-pipeline-simplification.md`
- Output contracts: `/.plans/x-to-demo-output-contracts.md`
- Deployment: `/docs/deployment.md`
- Architecture notes: `/architecture_decisions.md`

Last reviewed: 2026-02-12
