# Web (`apps/web`)

Next.js frontend for local x-to-demo pipeline runs.

## Features

- Input X capture and pipeline execution
- Per-phase artifact inspection/editing
- Resume and artifact download actions

## Run

```bash
pnpm -C apps/web dev
```

Set `NEXT_PUBLIC_API_URL` to your API base (default `http://localhost:8000/api/v1`).

## Test and lint

```bash
pnpm -C apps/web lint
pnpm -C apps/web typecheck
pnpm -C apps/web test
pnpm -C apps/web e2e
```
