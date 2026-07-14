# ADR-0016 — Bench-time queue priority + self-scoped performance

- **Status:** Accepted
- **Loop:** 5 (GRS-0026)
- **Normative source:** PRD §6 (Bench-Time Queue; Knowledge Base & Performance); CLAUDE.md #9
  (data scoping absolute).
- **Builds on:** ADR-0013 (certification ladder — the queue's top priority), ADR-0014 (drills +
  coursework), ADR-0015 (arena scenarios).

## Context

An idle advisor needs a single, unambiguous next action, and a way to see their own development.
Two design questions needed pinning: what the queue's priority ORDER is (and how to keep it
deterministic), and how far the performance view is scoped.

## Decision

### 1. The queue is a derived view with a fixed, golden-mastered priority order

`BenchQueue` and `PerformanceSummary` are **never persisted** — they are recomputed on every read
from the advisor's own records, so they can never drift from the certification/drill/arena/pipeline
state they summarise. The assembler (`workbench/bench.py::assemble_queue`) is a **pure function** of
already-fetched inputs (no DB, no clock), and the priority order is the product decision, so it is
pinned by a **golden master** over the three canonical states the ticket names (fresh,
mid-certification, fully-certified-with-drills):

1. **Next certification step** — highest priority (advancement is the advisor's core goal). Derived
   from the ladder state (`promotion_blockers`/`next_level`): the next incomplete **coursework**
   module when that is the blocker (self-actionable, links to the module), otherwise the single
   most-blocking requirement as guidance. A Certified Lead has no certification item.
2. **Due drills** — one aggregate item counting all due cards, pointing at the soonest-due one.
3. **A practice-arena scenario** — one the advisor has not yet attempted (else a re-practice).
4. **An Opportunity Radar research task** — always the tail item, so an advisor is *never* left
   without a next action.

Only applicable items appear, in that fixed order; priorities are assigned `1..n` by position.

### 2. Opportunity Radar is a real pipeline linkage, with a documented placeholder boundary

The full Opportunity Radar (a sourcing-research surface) is future scope. This ticket wires the
**linkage that already has data**: if the advisor owns an early-stage prospect (`PROSPECT`/`NURTURE`),
the research task points at it (`ref_id`) — sourcing credit already theirs (PRD §6). With no such
prospect it degrades to a standing "scan for new opportunities" prompt. So the queue slot and its
priority are in place; the dedicated research workspace is a later ticket.

### 3. Performance is self-only here — even for an admin

Conversion rate, engagements, learning progress, drill streak and the arena trend are computed
**only for the caller** (`get_performance_summary` refuses any `advisor_id` but the caller's own with
a `NotFoundError` → 404, *not shown to exist*). Unlike the rest of the repository, this view does
**not** grant admins a cross-advisor read: the admin/cohort aggregate ("the full picture per PRD") is
**Holy Corner scope**, deliberately not built here, so nothing in Grassmarket can surface a
cross-advisor leaderboard. A foreign id is a 404 for admin and advisor alike.

Because an admin *is* a real consultant with their own pipeline, "self only" has to be enforced by
the data access too, not just the id check: the bench methods read prospects and engagements through
**strictly owner-scoped** helpers (`_own_prospects` / `_own_engagement_statuses`), never the
admin-aware `list_prospects` / `list_engagements` — otherwise an admin's own dashboard would fold in
the whole org's pipeline and surface another advisor's prospect as their research nudge. The
already-owner-scoped sources (drills, arena sessions, content completions) are reused directly.

## Consequences

- The queue can never silently drift (derived, golden-mastered) and always yields at least one
  action; a future priority change is a visible edit to the pinned order, not an accident.
- Certification → drills → arena → research is now one coherent bench surface feeding GRS-0027's
  dashboard; the workbench frontend consumes `BenchQueue`/`PerformanceSummary` directly.
- **Accepted scope boundaries:** the Opportunity Radar research *workspace* and the admin/cohort
  performance aggregate are out of scope (the latter is Holy Corner's). "Client ratings" from PRD §6
  are not yet a data source (no rating is captured on engagements today) and are omitted rather than
  fabricated; they slot into `PerformanceSummary` when that field exists.
