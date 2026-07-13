# GRS-0034 — Launch readiness

- **Loop:** 6 (closes the build)
- **Branch:** `grs-0034-launch-readiness`
- **Status:** Planned
- **Normative source:** PRD §1 (portals/domains), §9; CLAUDE.md.
- **Depends on:** GRS-0032, GRS-0033.

## Goal

First real advisors onboarded on production.

## Scope

1. Production Railway environment: separate service + Postgres from staging; secrets rotated; backups verified with an actual restore drill.
2. Domain wiring: advisors.bruntsfieldcapital.com; TLS; main-site login routing.
3. First advisor cohort invited (invitation-only flow exercised for real).
4. Knowledge-base seed content loaded (playbook, primers, initial vignettes).
5. E2E smoke suite runnable against production: read-only paths + one synthetic engagement end-to-end (created, assessed, finalised, deliverable generated, then archived).
6. Operations runbook: deploy, rollback, backup/restore, incident basics, support contact path.
7. Phase-2 seams documented: what Holy Corner consumes from `bcap-contracts`, what Viewforth will read.

## Exit criteria

- A real advisor completes login → training module → practice assessment on production.
- Restore drill and rollback exercised once each, documented in the runbook.
- Smoke suite green against production.
