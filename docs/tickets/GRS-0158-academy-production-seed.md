# GRS-0158 — Academy content: seed it into production (the empty-Workbench fix)

**Status:** Planned (2026-07-21). Root-caused on the staging deep-dive; the founder saw an empty Workbench.
**Priority:** HIGH — demo blocker. **Loop:** demo-readiness.

## Why

The Academy catalogue is empty in production. The ~2,171 lines of authored course content
(`src/grassmarket/workbench/content/`: sales_egoist, sales_ops_playbook, openbb/benzinga/brandfetch,
practice_scenarios) are published only by `seed_academy_content()`, whose **only caller is the dev-only
`scripts/seed_dev.py`** (targets `local.db`). Prod boot (`web/app.py`) runs only migrations; migration
`0026` creates the empty `course` tables and inserts zero rows → the Academy correctly renders
"No courses published yet." Proven on staging: after running the seed, the full catalogue rendered
(Sales Egoist 8 lessons, Benzinga 18, Brandfetch 19, OpenBB 22, Sales Ops Playbook 4).

## Scope

- New `scripts/seed_academy.py`: idempotent — ensure an admin principal exists (create `admin@…` with
  `Role.ADMIN` if absent), then call `seed_academy_content(repo, admin, now=…)`. **No demo prospect/
  assessment data** (that's GRS-0159); this ships to prod.
- Wire it into the Railway **release phase** (a pre-deploy/release command, or a boot-time call in
  `app.py` after `run_migrations`, guarded so it runs once and is safe on every boot).
- Run once against production; verify the Academy lists all seeded courses.
- CI: assert a fresh DB + this seed → `list_published_courses` non-empty.

## Acceptance

A freshly-migrated environment serves the full Academy catalogue with no manual step.
