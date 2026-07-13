# GRS-0026 — Bench-time queue + performance view

- **Loop:** 5
- **Branch:** `grs-0026-bench-queue-performance`
- **Status:** Planned
- **Normative source:** PRD §6 (Bench-Time Queue; Knowledge Base & Performance).
- **Depends on:** GRS-0023–0025 (queue sources).

## Goal

Idle advisors always have a prioritised next action; bench time becomes measurable development.

## Scope

1. Queue assembly with priority rules: next certification module → due drills → an arena scenario → an Opportunity Radar research task (with sourcing-credit linkage to the pipeline).
2. Queue is the advisor's dashboard state when no engagement is active.
3. "My Performance": engagements completed, client ratings, conversion rate, learning progress, own-history trend lines. Scoped to self — no cross-advisor leaderboard exposure (admin sees the full picture per PRD; that view is Holy Corner scope, not this ticket).

## Exit criteria

- Queue renders correct priorities for seeded advisor states (fresh, mid-certification, fully certified with due drills).
- Performance view scoped to self (404 pattern on other advisors).
- Full gate green; CI green.
