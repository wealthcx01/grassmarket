# GRS-0157 — Prod deploy hotfix: httpx runtime dep + Alembic version-column overflow

**Status:** Done (2026-07-20). Hotfix — the Railway backend had been un-deployable for ~5 days.
**Loop:** Ops. Found while deploying the session's work to Railway (backend stuck at DB rev 0018).

## Symptom
The `grassmarket-api` service's GitHub auto-deploy had silently stopped succeeding; the live API was
missing every change since mid-July. Manual `railway up` built fine but the container never passed its
health check. Two distinct boot-time failures, both invisible to local/CI (SQLite) and only fatal on
the prod Postgres:

## Bug 1 — `httpx` was dev-only but imported in production
`src/grassmarket/auth/google_oauth.py` imports `httpx` at module load, which is on the app-import path
(`web/app.py`). But `httpx` sat under `[project.optional-dependencies].dev`, and the prod build runs
`uv sync --no-dev` → `ModuleNotFoundError: No module named 'httpx'` → crash-loop. **Fix:** moved
`httpx>=0.27` into runtime `dependencies`; regenerated `uv.lock` (the build is `--frozen`).

## Bug 2 — revision id overflowed Alembic's `version_num varchar(32)`
Once the app booted, migrations ran and failed at 0029:
`StringDataRightTruncation: value too long for type character varying(32)` — the revision id
`0029_contacts_and_prospect_website` is 34 chars, and Alembic's default `alembic_version.version_num`
is `varchar(32)`. SQLite (local/CI) ignores column length, so it only bit Postgres. **Fix:** `0029`'s
`upgrade()` now widens `alembic_version.version_num` to `VARCHAR(255)` first (Postgres-only, guarded on
`bind.dialect.name`; a no-op on SQLite), so it — and any future longer id — records cleanly in the same
transaction.

## Also
- `railway.toml` `healthcheckTimeout` 120 → 300: migrations run synchronously at app import
  (`create_app → run_migrations`), so a deploy several revisions behind needs boot headroom.

## Deploy note
The prod DB was mid-way at 0018; the recovery deploy advanced it cleanly to head (0031). Deploying a
migration-heavy backend contends for table locks with the still-serving old instance (Railway's
zero-downtime overlap), so a deploy that must run many migrations may need the old instance stopped
first (`railway down` then `railway up`) or the migrations run out-of-band.

## Prevention (follow-up, non-blocking)
- CI builds/boots against Postgres (not just SQLite) so both classes of bug surface pre-merge.
- A lint/test asserting every migration revision id ≤ 32 chars (until the column widening is universal).
