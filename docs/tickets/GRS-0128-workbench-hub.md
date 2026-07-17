# GRS-0128 — Bench/Workbench as the single "what I should / must / have done" hub

**Status:** Shipped
**Loop:** Part 2 — Bruntsfield Academy / Workbench (one program)
**Depends on:** ADR-0028 (Bruntsfield Academy / Workbench)

## Delivered

The bench queue now folds the **governance + Academy** surfaces into the one hub, extending
`assemble_queue` (no parallel aggregator): three new `BenchItemKind`s — **RATING_REQUEST** (from
`list_my_rating_assignments` — an assigned co-rating blocking an assessment), **COMMITTEE** (from
`list_assessments_for_committee`, for committee members), and **ACADEMY** (the next incomplete
published course, mandatory-first first, from GRS-0121/0122). Priority order: rating + committee
first (others are waiting on them), then certification, Academy, drills, arena, research (the tail).
The defaults add nothing, so a plain advisor's queue is unchanged. `BenchDashboard.tsx` renders the
new kinds; **`app/layout.tsx` gains a global-nav `/workbench` link** (the hub was reachable only from
the dashboard card + `/help` before). Golden master untouched.

## Why

The founder wants the Workbench to be the one place showing everything an advisor should / must / has
done — linked to the whole site. The bench already does most of this: it aggregates a prioritised
next-action queue (`assemble_queue`, `workbench/bench.py:101`; kinds certification/drill/arena/research)
plus a performance grid (`summarise_performance`, `:189`). So **extend it, don't rebuild** — fold in the
missing work surfaces and fix its discoverability (today `/workbench` is reachable only from the
dashboard card + `/help`).

## What to build

- Extend the bench queue/grid to also pull in **assigned assessments/engagements**, **rating-request** +
  **committee** tasks, and **course/learning progress**, so the one hub reflects assessment, governance,
  and Academy work together. Files: `components/workbench/BenchDashboard.tsx`, `workbench/bench.py`.
- Add a **global-nav link to `/workbench`** — the `app/layout.tsx` header currently has only home + Guide.
- Reuse `assemble_queue` (`bench.py:101`) and `summarise_performance` (`:189`); do not stand up a
  parallel aggregator.

## Acceptance / verification

- The bench hub surfaces assigned assessments/engagements, rating-request + committee tasks, and
  learning progress alongside the existing certification/drill/arena/research items.
- `/workbench` is reachable from the global nav in `app/layout.tsx`.
- Aggregation still flows through `assemble_queue`/`summarise_performance` (no new parallel queue).

## Not in scope

- The certification and learning content the hub links to (GRS-0121/0122/0127).
- Certification-evidence auto-linking (GRS-0131).
