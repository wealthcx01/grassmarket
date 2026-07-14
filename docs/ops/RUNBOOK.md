# Grassmarket operations runbook

Operational reference for the Advisor Studio production service: deploy, rollback, backup/restore,
incident basics, and the support path. Grassmarket runs on **Railway** (managed service + Postgres);
the frontend is a Next.js app. Config is read via `src/grassmarket/config.py` (pydantic-settings),
which **refuses to boot in production** with an insecure secret, SQLite, or a placeholder transcript
key — a misconfiguration fails loud rather than serving in an unsafe state.

> Credentialed cutover steps (provisioning prod, DNS/TLS, inviting the real cohort, restore/rollback
> drills) are owned by the operator — see `docs/ops/launch-cutover.md`. This runbook is the standing
> reference the cutover checklist points back to.

## Service topology

| Piece | Where | Notes |
|---|---|---|
| API (FastAPI) | Railway service, NIXPACKS build | Start: `uv run uvicorn grassmarket.web.main:app --host 0.0.0.0 --port $PORT` (`railway.toml`, `Procfile`) |
| Database | Railway managed Postgres | `DATABASE_URL` injected by Railway; config refuses SQLite in production |
| Schema | Alembic migrations | Run on app startup via `run_migrations(engine)` in `create_app`; `migrations/versions/` is the source of truth |
| Frontend | Next.js (`frontend/`) | Talks to the API origin; CORS locked to `GM_FRONTEND_ORIGIN` |
| Healthcheck | `GET /health` | Railway healthcheck path; liveness only, never touches the DB |

## Environment variables (production)

Set these in the Railway **service variables** (never in the repo). `.env.example` is the template;
`config.py` is the authority.

| Var | Purpose | Production rule |
|---|---|---|
| `GM_ENV` | `local`/`ci`/`staging`/`production` | Must be `production` — flips the fail-loud guards on |
| `GM_JWT_SECRET` | JWT signing secret | 48-byte urlsafe token; **placeholder refused in prod**. Generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `DATABASE_URL` | Postgres DSN | Injected by Railway; **SQLite refused in prod** |
| `GM_TRANSCRIPT_ENCRYPTION_KEY` | Fernet key for at-rest transcript encryption (GRS-0029) | **Placeholder refused in prod**. Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `GM_JWT_ISSUER` | Token issuer | `advisors.bruntsfieldcapital.com` |
| `GM_JWT_AUDIENCE` | Token audience | `bruntsfield` |
| `GM_INVITE_TTL_HOURS` | Invitation validity | `168` (7 days) |
| `GM_FRONTEND_ORIGIN` | CORS allowlist | The deployed frontend origin (e.g. `https://advisors.bruntsfieldcapital.com`) |

**Rotating a secret:** set the new value in Railway variables → redeploy. Rotating `GM_JWT_SECRET`
invalidates all live sessions (users re-login). Rotating `GM_TRANSCRIPT_ENCRYPTION_KEY` makes
existing encrypted transcripts unreadable — do **not** rotate it without a re-encryption migration;
treat it as long-lived.

## Deploy

Grassmarket ships via GitHub → Railway (Railway auto-deploys the tracked branch, or deploy manually).

1. Merge to `main` with CI green (backend ruff·pyright·pytest, frontend type-check·lint·test, E2E).
2. Railway builds (NIXPACKS) and starts the service. **Migrations run automatically at startup**
   (`run_migrations`), so a deploy that adds a migration applies it on boot.
3. Watch the deploy logs until `GET /health` returns `{"status":"ok", "env":"production"}`.
4. Verify readiness: `GET /health/ready` returns `{"status":"ready"}` (this one pings the DB — a
   `500`/`503` means the store is unreachable, not a hollow OK).
5. Run the smoke suite against the live URL (see below). Green = deploy good.

Config errors surface as a **boot failure** (the app refuses to start), not a running-but-broken
service — check the deploy logs for the `Refusing to run in production...` message and fix the
offending variable.

### Frontend deploy (`grassmarket-web`)

The web service is **not currently GitHub-connected** — merging to `main` auto-deploys the **API
only**. Until the service is wired to GitHub, the frontend ships **manually** from repo root:

```bash
railway link                      # project: grassmarket, env: production
railway up frontend --path-as-root --service grassmarket-web
```

`--path-as-root` is **required**: without it, `railway up` archives the whole repo, picks up the
root `railway.toml` (the API's `uvicorn` start command), and the web service boots the API instead
of Next.js — which then fails on the missing `GM_JWT_SECRET`. With `--path-as-root frontend`,
`package.json` is at the archive root and Railway's builder correctly detects Next.js.

**Durable fix (do this once, in the Railway dashboard — the CLI cannot connect a repo):** connect
`grassmarket-web` to GitHub `wealthcx01/grassmarket`, set **Root Directory = `frontend`** and branch
`main`. After that, frontend merges auto-deploy like the API and the manual step above is retired.

## Rollback

Migrations run on startup and can add schema, so rollback is two independent moves — **redeploy the
previous image** and, only if the bad deploy applied a migration you must undo, **downgrade the
schema**.

1. **Code:** in Railway, redeploy the last-known-good deployment (Railway keeps deploy history), or
   revert the merge on `main` and let it redeploy.
2. **Schema (only if a migration must be undone):** `uv run alembic downgrade -1` (one step) or
   `uv run alembic downgrade <revision>` against the production `DATABASE_URL`. Prefer forward-fixes;
   only downgrade a migration that is genuinely incompatible with the rolled-back code.
3. Re-run `/health/ready` + the smoke suite to confirm the rollback is healthy.

Because scoring runs are immutable and append-only (CLAUDE.md #6), a rollback never corrupts prior
runs — the worst case is that new runs pause until the service is healthy again.

## Backup & restore

Railway managed Postgres provides automated backups. The **restore drill** (must be exercised once
before launch — `docs/ops/launch-cutover.md`) proves they actually restore:

1. Trigger/confirm a recent automated backup exists in the Railway Postgres dashboard.
2. Restore it into a **scratch** database (never overwrite production in a drill).
3. Point a staging app at the restored DB; run the smoke suite read-only paths and confirm row
   counts are sane (`SELECT count(*)` on `consultants`, `scoring_runs`, `audit_events`).
4. Record the restore time and any surprises in this runbook's incident log.

A manual logical dump is the belt-and-braces backup:
`pg_dump "$DATABASE_URL" > grassmarket-$(date +%F).sql` (run from a trusted operator machine; the
dump contains personal data — store encrypted, honour the GDPR retention posture in ADR-0021).

## Smoke suite

`scripts/prod_smoke.py` probes a running API: health + authenticated reads, and (with `--write`) a
solo write path — create → advance stages → open assessment → autosave a scoreable doc → **live
score** → archive the prospect. It exits non-zero on any failure.

Finalise → deliverable is **not** run by the live script: it is governance-gated (dual-rating +
committee, §8/§9) and needs server-seeded principals, so it is covered end-to-end in CI only (see
below). A green prod run validates health, auth, the read paths, and the scoring path — not
deliverable generation on prod.

```bash
# Read-only (safe against production — health + authenticated reads, no writes):
uv run python scripts/prod_smoke.py --base-url https://advisors.bruntsfieldcapital.com \
    --email OP_EMAIL --password OP_PASS

# + the solo write path (creates a disposable prospect + assessment, archives the prospect) —
# prefer staging or a maintenance window:
uv run python scripts/prod_smoke.py --base-url https://... \
    --email OP_EMAIL --password OP_PASS --write
```

The suite's logic is covered by `tests/test_prod_smoke.py`, which runs the same steps against an
in-process app in CI — **and** drives the full finalise → deliverable lifecycle there (the part the
live script can't do solo) — so the smoke script itself can't silently rot.

## Incident basics

1. **Is it up?** `GET /health` (liveness) and `GET /health/ready` (DB). If `/health` fails, the
   service is down — check Railway deploy status/logs. If `/health` is OK but `/ready` fails, the
   database is unreachable — check the Postgres service and `DATABASE_URL`.
2. **Boot loop after deploy?** Almost always a config guard: read the logs for
   `Refusing to run in production...` and fix the variable, or roll back the deploy.
3. **Auth failures across the board?** Check `GM_JWT_SECRET` wasn't rotated unexpectedly (rotating it
   logs everyone out) and that `iss`/`aud` match the frontend's expectations.
4. **Data-exposure concern?** Scoping is enforced in the repository layer and tested; if a scoping
   bug is suspected, treat as a security incident — pull the audit log (`GET /compliance/audit`,
   admin-only, append-only) for the affected window.
5. **Escalate** per the support path below with: timestamp, `env`, the failing endpoint, the
   `/health` + `/health/ready` results, and the relevant log excerpt.

## Support & escalation path

- **Primary owner / operator:** John Gallagher (john.gallagher@wealthcx.com).
- **Repo / issues:** github.com/wealthcx01/grassmarket — file an issue for non-urgent defects; tag
  the owner for anything blocking advisors.
- **Compliance / GDPR requests:** `GET /compliance/personal-data/{id}` (export) and
  `POST /compliance/personal-data/{id}/delete` (erasure = anonymisation, ADR-0021), self-or-admin.
- **Incident log:** append dated entries below.

### Incident log

_(append `YYYY-MM-DD — summary — resolution` entries here)_
