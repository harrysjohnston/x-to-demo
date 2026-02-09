# Full Test Suite

Run the entire test suite from the repo root (unit + e2e for web, unit for API):

```bash
pnpm test:full
```

**CI-style (lint + typecheck + full tests), same order as CI — use before push:**

```bash
pnpm test:ci
```

## What runs

1. **Web unit** – Vitest in `apps/web` (components, lib, app tests).
2. **Web e2e** – Playwright in `apps/web` (starts dev server, then runs `tests-e2e/`).
3. **API** – Pytest in `apps/api` (with coverage reports).

Execution order is fixed: unit then e2e so the dev server is only started once for Playwright.

## Prerequisites

- **Playwright browsers** – If e2e fails with browser errors, install from the web app dir:
  ```bash
  pnpm -C apps/web exec playwright install --with-deps
  ```
- **API env** – API tests use in-memory SQLite by default. For env parity with production, ensure `config/env.example` (or equivalent) is set up when relevant.

## Relation to CI

CI runs **web** (Biome → Vitest → Playwright) and **api** (Ruff check + Ruff format check → Pytest) in **parallel** jobs.
`test:full` does **not** run lint or typecheck. For a local run that matches CI checks, use **`pnpm test:ci`**: it runs `lint:ci` (web Biome + api Ruff check + api Ruff format check), then `typecheck`, then `test:full`.

## Optional commands

- **CI-style** (lint + typecheck + full tests, same as CI):
  ```bash
  pnpm test:ci
  ```
- **Lint only, CI-style** (web Biome + api Ruff check + api Ruff format check):
  ```bash
  pnpm lint:ci
  ```
- **Typecheck only** (TypeScript in `apps/web`):
  ```bash
  pnpm typecheck
  ```
- **Unit tests only** (no e2e, faster iteration):
  ```bash
  pnpm test
  ```
- **Web-only** (unit + e2e):
  ```bash
  pnpm -C apps/web test && pnpm -C apps/web e2e
  ```
- **API-only**:
  ```bash
  pnpm api:test
  ```

## Possible future improvements

- **Parallel unit runs** – Web unit and API tests are independent; running them in parallel (e.g. with `concurrently` or `npm-run-all`) would reduce total time.
