# Web (`apps/web`)

Next.js + TypeScript frontend for the fullstack template. Use this app as the web client when bootstrapping or extending the template.

## What’s included

- **Next.js** – App Router, TypeScript
- **UI** – shadcn/ui, Tailwind CSS
- **Auth** – Login/register UI, token handling, protected flows
- **Uploads** – File upload component and gallery, presigned URL flow
- **Realtime** – SSE hook (`useSSE`) for live updates
- **API client** – Typed helpers and auth-aware requests
- **Testing** – Vitest (unit), Playwright (e2e)

## Development

### First run (no Docker)

```bash
# From repository root
pnpm install
cd apps/web
pnpm dev
```

Set `NEXT_PUBLIC_API_URL` to your API base (default `http://localhost:8000/api/v1`). You can put it in the root `.env` for local dev.

### Run with the full stack

From the repo root, `pnpm dev:full` starts the API, web app, db, MinIO, and MailHog. Then open http://localhost:3000.

### Tests

```bash
# Unit tests
pnpm test

# E2E (Playwright)
pnpm e2e
```

### Lint and typecheck

```bash
pnpm lint
pnpm typecheck
```

## Project layout

- `app/` – Pages, layout, globals
- `components/` – AuthForm, AuthSection, FileUpload, FileGallery, UI primitives
- `lib/` – api client, auth helpers, upload, SSE client, utils
- `hooks/` – useSSE
- `tests-e2e/` – Playwright specs
