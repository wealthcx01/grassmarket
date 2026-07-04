# Bruntsfield Advisor Studio — Frontend (Grassmarket)

Next.js (App Router) + TypeScript shell for the Bruntsfield Advisory Network advisor
platform. **This is the Loop 0 scaffold** — a real, runnable skeleton (root chrome,
dashboard shell, backend-health widget, invitation login form). Feature sections are
placeholders wired up across the build loops (PRD §9).

## Run

```bash
cd frontend
npm install          # first time only
cp .env.local.example .env.local
npm run dev          # http://localhost:3000
```

The dashboard's health widget calls `GET ${NEXT_PUBLIC_API_BASE_URL}/health` — start the
FastAPI backend (default `http://localhost:8000`) to see it go green. Without it, the
widget shows a loud "cannot reach API" error rather than a fake-healthy state.

### Scripts

| Script              | Purpose                          |
| ------------------- | -------------------------------- |
| `npm run dev`       | Dev server (Turbopack)           |
| `npm run build`     | Production build                 |
| `npm run start`     | Serve the production build       |
| `npm run lint`      | ESLint (next/core-web-vitals)    |
| `npm run type-check`| `tsc --noEmit` (strict)          |

## Design tokens

Single source of truth: **`app/globals.css`** (`:root` CSS variables). From the
Bruntsfield website design system:

- **Palette** — paper/ink: paper `#FAF8F3` (background), ink `#1A1A1A` (text),
  accent **Bottle Green `#1A3B26`**.
- **Fonts** — Source Serif 4 (headings), Inter (body), IBM Plex Mono (mono/numbers),
  loaded via `next/font/google` in `app/layout.tsx` and exposed as
  `--font-serif` / `--font-sans` / `--font-mono`.

Restrained and editorial by intent — this is a professional advisory tool.

## Layout

```
frontend/
├── app/
│   ├── layout.tsx          # root layout: fonts, top bar, page chrome
│   ├── globals.css         # design tokens (single source of truth) + resets
│   ├── page.tsx            # advisor dashboard shell + section nav
│   ├── health-widget.tsx   # client component: backend /health status
│   └── login/page.tsx      # invitation login (POST /auth/login)
├── lib/api.ts              # typed fetch helper (NEXT_PUBLIC_API_BASE_URL, fail-loud)
├── .env.local.example
├── next.config.mjs
├── eslint.config.mjs
├── tsconfig.json           # strict
└── package.json
```

## Backend contract (assumed — reconcile with the API as it lands)

- `POST /auth/login` — body `{ email, password }` → `{ access_token, token_type }`.
- `GET /health` — `{ status, version?, service? }` (only `status` is required; read
  defensively).

The login token is stored in `localStorage` as a **placeholder only**; real session
management (httpOnly cookies / refresh, Holy Corner claim shape) arrives in Loop 6.
