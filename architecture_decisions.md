# Architecture Decisions (Learning Resource)

This document used to be an incremental build plan. Now that the template is implemented, it serves as a record of **architecture choices**, **alternatives**, and **tradeoffs**.

It’s written for learning: each decision includes the “why”, what you gain/lose, and what you might choose instead in a different project.

## How to use this document

- **Read top-down once**, then jump to decisions relevant to what you’re changing (auth, realtime, uploads, etc.).
- **Prefer “why” over “what”**: the repo code is the “what”; this file explains the reasoning.
- **Treat decisions as local**: the “best” choice depends on team size, latency requirements, compliance, budget, and operational maturity.

## Decision index (where to look)

- **Web**: `apps/web/` (API client, SSE client, upload UI)
- **API**: `apps/api/app/` (routers, auth, DB models, settings, storage, email)
- **Infra**: `infra/terraform/` and `docs/deployment.md`
- **Dev orchestration**: `docker-compose.yml`, root `package.json` scripts

---

## ADR-0001: Monorepo with independent deployables (`apps/web`, `apps/api`)

### Context

We want a single repo that is easy to bootstrap and teaches “fullstack” concerns, while keeping the web and API independently deployable.

### Decision

Use a monorepo layout with separate deployables:

- `apps/web`: Next.js frontend
- `apps/api`: FastAPI backend

### Why

- Keeps shared docs/tooling in one place, while allowing distinct build/deploy pipelines.
- Easier cross-app refactors (e.g. API contract + client wrapper changes).
- Avoids prematurely forcing shared-package architecture; `packages/` can be added later as needed.

### Alternatives (and when to choose them)

- **Separate repos**: good when teams are independent, deployments are fully decoupled, or access control differs.
- **Single deployable (monolith)**: good early on for very small products (one service, one deployment), but mixes concerns.
- **Monorepo with shared types package**: good if you want contract-driven development (OpenAPI/TS generation) immediately.

### Consequences

- CI can be more complex (multiple toolchains).
- Versioning and release discipline matters if you later publish shared packages.

---

## ADR-0002: Web framework = Next.js (App Router) + TypeScript

### Context

We want a modern React experience, SSR/streaming support, and a widely-known stack for learning and hiring.

### Decision

Use Next.js (App Router) with TypeScript in `apps/web`.

### Why

- Strong default architecture (routing, server/client components, env conventions).
- Great ecosystem for authentication, SEO, performance, and deployment options.
- TypeScript improves refactor safety, especially with API/client integration.

### Alternatives

- **Vite SPA**: simpler runtime and hosting; you’ll implement SSR/SEO patterns yourself.
- **Remix**: excellent data-loading model; fewer “magic” conventions than Next in some areas.
- **Astro**: great for content-heavy sites with islands; less ideal if you’re “app-first”.

### Consequences

- You need to understand client/server boundaries (which is a feature for learning).

---

## ADR-0003: UI approach = Tailwind + shadcn/ui-style components

### Context

We want a clean UI system without heavy component-library constraints.

### Decision

Use utility-first styling + composable components (Tailwind + `components/ui` patterns).

### Why

- Easy to learn by reading the final markup (styles live with components).
- “Bring your own components” scales better than locking into a rigid design system too early.

### Alternatives

- **MUI/Chakra/AntD**: faster initial UI, more constraints; can fight custom design and bundle size.
- **CSS Modules**: very explicit; great for teams that dislike utility-first CSS.

### Consequences

- Requires some discipline to avoid inconsistent styling patterns.

---

## ADR-0004: API framework = FastAPI

### Context

We want typed request/response models, OpenAPI support, and a clear learning path for building APIs.

### Decision

Build the API in `apps/api` using FastAPI.

### Why

- Pydantic-based validation with strong DX and OpenAPI output.
- Async support is available when needed (e.g. SSE streaming).
- Large community and straightforward structure for “small-to-medium” services.

### Alternatives

- **Django + DRF**: great batteries-included; heavier framework and ORM-first mindset.
- **Flask**: minimal; you’ll assemble validation/docs/testing conventions yourself.
- **Node (Express/Nest)**: great if your org is JS/TS-first; different performance + typing tradeoffs.

### Consequences

- You’ll decide your own patterns for “service layers” and consistency; FastAPI won’t impose them.

---

## ADR-0005: Database = PostgreSQL (local dev via Docker Compose)

### Context

We want production realism while keeping local setup easy.

### Decision

Use Postgres for primary persistence, run locally via Compose (`docker-compose.yml`).

### Why

- Feature-rich and industry-standard.
- Matches typical cloud hosting (RDS, Cloud SQL, etc.).

### Alternatives

- **SQLite**: great for local-first learning and tiny apps; diverges from production behavior.
- **MySQL**: fine choice; mostly operational preference.
- **Serverless Postgres**: good for scale-to-zero, but introduces vendor-specific behavior.

### Consequences

- You need migrations and a clear local boot sequence.

---

## ADR-0006: ORM/data layer = SQLModel

### Context

We want a tight loop between DB models and API schemas without duplicating definitions everywhere.

### Decision

Use SQLModel models and SQLAlchemy sessions (`apps/api/app/models.py`, `apps/api/app/database.py`).

### Why

- Combines Pydantic validation with SQLAlchemy mapping.
- Great learning tool for “typed persistence” without heavy framework magic.

### Alternatives

- **SQLAlchemy + Pydantic**: more explicit and flexible; more boilerplate.
- **Django ORM**: very productive; strongly couples you to Django conventions.
- **Prisma (TS)**: excellent DX; changes the API stack assumptions.

### Consequences

- You still need to understand SQLAlchemy fundamentals for non-trivial queries and performance.

---

## ADR-0007: Migrations = Alembic

### Context

Schema changes must be versioned, reviewable, and deploy-safe.

### Decision

Use Alembic migrations (`apps/api/alembic/`).

### Why

- Industry-standard in Python for SQLAlchemy/SQLModel-based apps.
- Enables safe deploy workflows (migrate before serving traffic).

### Alternatives

- **No migrations**: acceptable only for throwaway prototypes.
- **Django migrations**: excellent if using Django ORM.
- **Atlas/Flyway/Liquibase**: great for DB-first orgs; more operational overhead.

### Consequences

- Autogenerate is helpful but not infallible; migrations must be reviewed.

---

## ADR-0008: API conventions = versioned prefix + response envelopes

### Context

We want consistent response shapes and a stable upgrade path.

### Decision

- Version API routes under `/api/v1` (`apps/api/app/main.py`).
- Use a response envelope shape (`data` + optional `meta`) for many endpoints (see `apps/api/app/schemas.py` and `apps/web/lib/api.ts`).

### Why

- Versioning reduces “breaking change fear”.
- Envelopes allow adding metadata (pagination, tracing IDs, etc.) without changing every client.

### Alternatives

- **No versioning**: faster early on; painful once multiple clients exist.
- **Header-based versioning**: cleaner URLs; harder to debug with a browser.
- **Raw JSON responses**: simpler; less room for consistent metadata and error shape guarantees.

### Consequences

- The client must understand the envelope (already handled in `apps/web/lib/api.ts`).

---

## ADR-0009: Authentication = JWT access + refresh tokens (with allowlist + rotation)

### Context

We want stateless request auth most of the time, but also want server-side revocation and refresh rotation.

### Decision

- Use **JWT access tokens** (short-lived) for API auth via `Authorization: Bearer ...` (`apps/api/app/auth.py`).
- Use **refresh tokens** (longer-lived) with:
  - a DB **allowlist** table for revocation/lookup (`RefreshToken` in `apps/api/app/models.py`)
  - **rotation** on refresh (`apps/api/app/routers/auth.py`)

### Why

- Access tokens keep most requests stateless and fast.
- Refresh token allowlist enables logout/revocation and prevents unlimited token replay.
- Rotation reduces risk if a refresh token leaks.

### Alternatives

- **Server sessions (cookie + session store)**: simpler security story for browsers; adds stateful infra (Redis/DB sessions).
- **JWT-only without allowlist**: simplest; logout is mostly client-side and token theft is harder to contain.
- **OAuth2/OIDC (Auth0/Cognito/Keycloak)**: best when you need SSO, enterprise identity, or multi-app auth at scale.

### Consequences (important!)

- The web client currently stores the access token in `localStorage` (`apps/web/lib/api.ts`). This is convenient for a template, but for high-security apps you’d typically prefer **HTTP-only cookies** + CSRF defenses (or a BFF pattern) to reduce XSS token theft risk.

---

## ADR-0010: Realtime = Server-Sent Events (SSE) with cookie-based auth for EventSource

### Context

Browsers’ `EventSource` API does not let you attach custom `Authorization` headers, but it *does* send cookies.

### Decision

- Provide an SSE endpoint at `/api/v1/sse/events` (`apps/api/app/routers/sse.py`).
- Authenticate SSE requests via an **HTTP-only cookie** (`sse_token`) set during login/refresh (`apps/api/app/routers/auth.py`).
- Allow anonymous connections as well (auth is optional).
- Use an in-memory pub/sub manager for broadcasting (`apps/api/app/pubsub.py`).
- Configure CORS with `allow_credentials=True` so the browser can send cookies (`apps/api/app/main.py`), and connect client-side with `withCredentials: true` (`apps/web/lib/sse.ts`).

### Why

- SSE is easy to operate behind typical HTTP infrastructure (ALBs, proxies) compared to WebSockets.
- Cookie auth fits `EventSource` constraints cleanly.
- In-memory pub/sub is enough for a single-process learning template.

### Alternatives

- **WebSockets**: bidirectional; more complex infra and scaling concerns.
- **Long polling**: simplest; higher overhead and latency tradeoffs.
- **SSE + Redis pub/sub (or NATS/Kafka)**: needed once you have multiple API instances.

### Consequences

- In-memory pub/sub won’t broadcast across multiple API processes/instances.
- Cookie-based auth requires careful CORS/origin configuration in production.

---

## ADR-0011: File uploads = presigned direct-to-storage uploads (S3/MinIO default)

### Context

Uploading large files through the API is expensive and slower (API becomes a bandwidth bottleneck).

### Decision

- The API returns a presigned **POST** upload instruction from `/api/v1/uploads` (`apps/api/app/routers/uploads.py`).
- Storage providers implement a simple protocol (`apps/api/app/storage/base.py`).
- Default provider is S3-compatible (works with AWS S3 and MinIO) (`apps/api/app/storage/s3.py`).
- GCS and Azure providers exist as explicit stubs for learning (`apps/api/app/storage/gcs.py`, `apps/api/app/storage/azure.py`).
- The web client performs the direct upload using the instruction (`apps/web/components/FileUpload.tsx`, `apps/web/lib/upload.ts`).

### Why

- Reduces load on the API (bandwidth and memory).
- Storage services are designed for big payloads and multipart uploads.
- Provider interface keeps the template “multi-cloud friendly” without forcing abstraction everywhere.

### Alternatives

- **Upload through API**: simpler authorization; expensive at scale and harder to tune timeouts.
- **Presigned PUT instead of POST**: simpler client; fewer built-in form constraints.
- **Resumable protocols (tus, multipart)**: better UX for large uploads; more moving parts.

### Consequences

- You must validate upload intent (content type, size) and bucket policies carefully.
- You still need a “finalize”/“claim upload” step in real apps if uploads represent user-owned objects.

---

## ADR-0012: Emails = Jinja2 templates + MJML rendering (dev sink)

### Context

We want emails that are maintainable and render well across clients.

### Decision

- Author email templates in MJML + Jinja (`apps/api/app/email/templates/*.mjml.j2`).
- Validate template context strictly (Jinja `StrictUndefined`) and render MJML to HTML in Python (`apps/api/app/email/service.py`).
- “Send” emails to a development sink (logging) controlled by settings (`apps/api/app/config.py`).

### Why

- MJML dramatically improves cross-client rendering compared to hand-written HTML.
- Strict context validation catches mistakes early (missing variables break tests, not production).
- Dev sink avoids needing SMTP/provider credentials for local dev.

### Alternatives

- **React Email**: great DX for TS teams; introduces a separate build pipeline.
- **Plain HTML (no MJML)**: fewer dependencies; more time spent fighting email client quirks.
- **External provider templates (SendGrid/Mailgun)**: good for production; harder to version control and test locally.

### Consequences

- MJML is an extra dependency; keep tests to ensure it remains available in your deployment environment.

---

## ADR-0013: Dev orchestration = Docker Compose with optional profiles

### Context

Local environments should be reproducible and “one command” when possible.

### Decision

Use Docker Compose for local services (DB, MinIO, MailHog), with root scripts to start/stop.

### Alternatives

- **Devcontainers**: excellent onboarding; requires VS Code/Docker alignment.
- **Nix**: very reproducible; steeper learning curve.
- **Local-only installs**: fastest runtime; hardest onboarding.

### Consequences

- Compose adds a dependency on Docker availability; the template keeps “no Docker” paths documented too.

---

## ADR-0014: CI/CD = GitHub Actions + container builds + GHCR

### Context

We want predictable checks and production-like builds.

### Decision

Use GitHub Actions for tests/lint and for building/publishing Docker images to GitHub Container Registry (see `.github/workflows/`).

### Alternatives

- **CircleCI/Buildkite**: great at scale; additional vendor/ops complexity.
- **No containers**: simpler early on; less production parity.

### Consequences

- Dockerfiles and CI caching become part of the learning surface area (intentionally).

---

## ADR-0015: Infrastructure = Terraform (AWS-focused)

### Context

We want infra that is reviewable, reproducible, and teachable.

### Decision

Use Terraform in `infra/terraform/` and document deployment in `docs/deployment.md`.

### Alternatives

- **Pulumi**: great if you prefer general-purpose languages; different ecosystem.
- **AWS CDK**: good for AWS-native teams; more “code-y”, less tool-agnostic.
- **ClickOps**: fast for experiments; hard to reproduce and review.

### Consequences

- Requires basic Terraform discipline (state management, secrets handling, workspace/env separation).

---

## ADR-0016: Template ergonomics = bootstrap + rename scripts (no generator)

### Context

A template only helps if first-run is painless and renaming is low-friction.

### Decision

Keep it as a GitHub template with two scripts:

- `scripts/bootstrap`
- `scripts/rename-template`

### Alternatives

- **Copier/Cookiecutter**: best if you need parameterized generation and multiple variants.
- **Custom CLI generator**: powerful; more code and long-term maintenance.

### Consequences

- The template stays transparent (no generation step), but renaming logic must be maintained as the repo grows.
