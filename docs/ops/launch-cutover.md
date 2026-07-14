# Launch cutover checklist (GRS-0034)

The build is complete. What remains to put the first real advisors on production is a set of
**operator actions that require credentials and are outward-facing** — provisioning, DNS/TLS,
inviting real people, and the backup/restore drills. These were **not** performed autonomously by
design: they touch real infrastructure and real users. This checklist is the runbook for John (or
whoever holds the Railway/DNS/GitHub credentials) to execute the cutover.

Standing reference: `docs/ops/RUNBOOK.md`. Integration boundaries: `docs/phase-2-seams.md`.

Legend: **[operator]** = needs credentials / outward-facing, do by hand · **[built]** = already
delivered in the repo, just verify.

## 1. Production environment (PRD §9 scope 1)

- [ ] **[operator]** Create the production Railway project: a service + **managed Postgres**,
      separate from staging.
- [ ] **[operator]** Set service variables (see `RUNBOOK.md` → Environment variables): `GM_ENV=production`,
      a freshly generated `GM_JWT_SECRET`, a freshly generated `GM_TRANSCRIPT_ENCRYPTION_KEY`,
      `GM_JWT_ISSUER=advisors.bruntsfieldcapital.com`, `GM_JWT_AUDIENCE=bruntsfield`,
      `GM_FRONTEND_ORIGIN=https://advisors.bruntsfieldcapital.com`. Railway injects `DATABASE_URL`.
- [ ] **[built]** Confirm the app **refuses to boot** if any prod guard is violated (insecure secret,
      SQLite, placeholder transcript key) — this is enforced in `config.py` and tested. A clean boot
      to `GET /health` `{"env":"production"}` means the guards passed.
- [ ] **[built]** Migrations apply on startup (`run_migrations`); no manual `alembic upgrade` needed
      for a normal deploy.
- [ ] **[operator]** Verify secrets are **rotated** away from any values ever used in dev/staging.

## 2. Domain & TLS (PRD §9 scope 2)

- [ ] **[operator]** Point `advisors.bruntsfieldcapital.com` at the Railway service (CNAME/custom
      domain in Railway).
- [ ] **[operator]** Provision TLS (Railway-managed cert); confirm HTTPS with a valid chain and that
      HTTP redirects to HTTPS.
- [ ] **[operator]** Wire the main-site login routing by role (advisors → this portal).
- [ ] **[built]** CORS is already locked to `GM_FRONTEND_ORIGIN`; set it to the real HTTPS origin.

## 3. First advisor cohort (PRD §9 scope 3)

- [ ] **[built]** The invitation-only flow is implemented and tested (create → accept → login → me;
      reuse/expiry refused): `tests/test_auth_flow.py` (service + HTTP), plus the end-to-end HTTP
      chain in `tests/test_invitation_flow_http.py`.
- [ ] **[operator]** As an admin, invite the real cohort: `POST /auth/invitations` `{email}` per
      advisor. Each advisor accepts via the emailed token, sets a passphrase, logs in.
- [ ] **[operator]** Confirm at least one real advisor completes **login → training module →
      practice assessment** on production (the ticket's exit criterion).

## 4. Knowledge-base seed content (PRD §9 scope 4)

- [ ] **[built]** The rubric/guidance library backs the wizard (`/guidance/subcomponents/{key}`);
      anchors marked `todo` render "guidance not yet authored" rather than a blank (no silent gaps).
- [ ] **[operator/content]** Author and load the remaining seed content — playbook, primers, initial
      practice-arena vignettes — via the rubric library and workbench content stores. This is a
      content task, not an infra one; track any `todo` anchors still outstanding at launch.

## 5. Production smoke suite (PRD §9 scope 5)

- [ ] **[built]** `scripts/prod_smoke.py` runs health + authenticated reads, and (with `--write`) a
      solo write path: create → assess → live-score → archive the prospect. Finalise → deliverable is
      governance-gated and covered in CI only — `tests/test_prod_smoke.py` drives that full lifecycle
      end-to-end against an in-process app.
- [ ] **[operator]** After cutover, run it against production and confirm green
      (`RUNBOOK.md` → Smoke suite). Read-only against live prod (`--email/--password`, no `--write`);
      run the `--write` path against staging or in a maintenance window. Note a green prod run does
      not exercise deliverable generation on prod (that's CI-only).

## 6. Operations runbook (PRD §9 scope 6)

- [ ] **[built]** `docs/ops/RUNBOOK.md` covers deploy, rollback, backup/restore, incident basics,
      and the support path.
- [ ] **[operator]** Exercise the **restore drill** once (restore a backup into a scratch DB, smoke
      it) and a **rollback** once (redeploy the previous deployment) — record both in the runbook's
      incident log. These are the ticket's exit criteria and cannot be faked from the repo.

## 7. Phase-2 seams documented (PRD §9 scope 7)

- [ ] **[built]** `docs/phase-2-seams.md` maps what Holy Corner consumes from `bcap-contracts`, what
      Viewforth reads, and where the code changes at integration time (repository swap, SSO issuer).

## Exit criteria (ticket GRS-0034)

- [ ] A real advisor completes login → training module → practice assessment on production. **[operator]**
- [ ] Restore drill and rollback exercised once each, documented in the runbook. **[operator]**
- [ ] Smoke suite green against production. **[operator, using the built suite]**

Everything marked **[built]** is done and in the repo. Everything marked **[operator]** needs
credentials or a real user and is intentionally left for the cutover — do not automate these.
