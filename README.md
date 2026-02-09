# Fullstack Template

A **fullstack template** to bootstrap a production-ready app: Next.js frontend, FastAPI backend, PostgreSQL, auth, file uploads, realtime (SSE), and email. Use it as a starting point and customize from there.

## Quick start

1. **Clone and bootstrap** (renames the template, installs deps, optional Docker):

   ```bash
   git clone <this-repo> your-project && cd your-project
   ./scripts/bootstrap --project-name your-project
   ```

2. **Run the stack** (from repo root):

   ```bash
   cp config/env.example .env   # if bootstrap didn't create it
   pnpm dev:full                # api + web + db + MinIO + MailHog
   ```

3. Open **http://localhost:3000** (web) and **http://localhost:8000/docs** (API).

For a non-interactive run, pass `--project-name your-app`. If Docker isn't available, use `--skip-compose` and run Postgres (and optionally MinIO/MailHog) locally. See [Local development](#local-development) below.

## What’s included

| Layer      | Tech |
|-----------|------|
| **Web**   | Next.js, TypeScript, shadcn/ui, Tailwind |
| **API**   | FastAPI, SQLModel, JWT auth, REST |
| **DB**    | PostgreSQL, Alembic migrations |
| **Realtime** | Server-Sent Events (SSE) |
| **Uploads** | Presigned URLs (S3; GCS/Azure adapters) |
| **Email** | Jinja2 + MJML templates, dev sink (MailHog) |
| **Testing** | Vitest (web unit), Pytest (API), Playwright (e2e) |
| **Tooling** | Biome (JS/TS), Ruff (Python), pre-commit |
| **Dev**   | Docker Compose (db, MinIO, MailHog profiles) |
| **CI/CD** | GitHub Actions (lint, test, deploy) |

## Repo layout

```
.
├── apps/
│   ├── web/          # Next.js + TypeScript + shadcn/ui
│   └── api/          # FastAPI + SQLModel
├── packages/         # Optional shared packages (types, utils)
├── infra/            # Terraform (AWS), deployment notes
├── .github/workflows/  # CI/CD
├── config/           # env.example, template checklist
├── docs/             # Deployment runbook
├── docker-compose.yml
├── architecture_decisions.md   # Design notes and tradeoffs
└── scripts/          # bootstrap, configure-deploy, rename-template
```

## Using this as a template

After cloning, run the bootstrap script so the repo is renamed and ready for your project:

```bash
./scripts/bootstrap --project-name your-project-name
```

- **Already renamed?** Use `--skip-rename`.
- **No Docker?** Use `--skip-compose` and run services yourself.
- **Python issues?** Activate the venv: `source .venv/bin/activate` (bootstrap creates `.venv` when needed).

Post-bootstrap, work through **config/template-checklist.md** to set project name, JWT issuer/audience, email sender, domains, and Terraform/CI variables.

## Local development

### Env file

```bash
cp config/env.example .env
```

- `DATABASE_URL` is optional when using Compose; the default points at the `db` service.
- For the storage profile, set `S3_ENDPOINT_URL=http://minio:9000` (Compose) or `http://localhost:9000` (local MinIO).

### Dev commands (from repo root)

| Command | Services |
|---------|----------|
| `pnpm dev` | api, web |
| `pnpm dev:db` | api, web, db |
| `pnpm dev:full` | api, web, db, MinIO, MailHog |
| `pnpm dev:down` | stop all |

### Database migrations

Migrations run automatically via Docker Compose when the `db` profile is active. The `migrate` service waits for Postgres to be healthy, applies pending migrations, then exits. The API waits for migrations to complete before starting.

To run migrations manually (e.g., when not using Docker):

```bash
source .venv/bin/activate
python apps/api/scripts/migrate.py upgrade --no-backup-check
```

For production deployments, omit `--no-backup-check` to require backup confirmation before applying migrations.

### URLs

- Web: http://localhost:3000
- API docs: http://localhost:8000/docs
- API health: http://localhost:8000/health
- MailHog (email): http://localhost:8025
- MinIO console (uploads): http://localhost:9001

## Testing

```bash
# All tests (web unit + e2e, API)
pnpm test:full

# Web only
pnpm -C apps/web test
pnpm -C apps/web e2e

# API only (from repo root; activate venv first)
source .venv/bin/activate
python -m pytest -q -c apps/api/pyproject.toml apps/api

# Lint
pnpm lint
```

## Production builds

Images are built on push to `main` via GitHub Actions. To build locally:

```bash
pnpm build:prod
# Or individually:
docker build -f apps/api/Dockerfile --target production -t fullstack-api:prod .
docker build -f apps/web/Dockerfile --target production -t fullstack-web:prod .
```

See **docs/deployment.md** for runbooks, migrations, and AWS/CI/CD.

## Pre-commit hooks

After installing dependencies, enable hooks so Ruff and Biome run before each commit:

```bash
source .venv/bin/activate
uv pip install -e "apps/api[dev]"
pre-commit install
pre-commit run --all-files
```

## Architecture and decisions

**architecture_decisions.md** documents design choices, alternatives, and tradeoffs for this template.
