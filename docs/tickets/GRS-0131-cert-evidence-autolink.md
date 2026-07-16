# GRS-0131 — Auto-link certification evidence to real assessment participation (the actual gap)

**Status:** Planned
**Loop:** Part 2 — Bruntsfield Academy / Workbench (one program)
**Depends on:** ADR-0028 (Bruntsfield Academy / Workbench)

## Why

The founder worried that certification/rating work doesn't tie to real assessments. **Mostly already
satisfied — tell them:** rating-requests, dual-rating, and committee **already link to assessments**
through `assessment_id` and work end-to-end (`ModuleRatingDraft.assessment_id`,
`CommitteeDecision.assessment_id`; blind rating + consensus + committee-gate all wired). The **real gap**
is that **certification evidence is honour-system admin entry, not computed** — `shadow_count` /
`observed_lead_logged` / sign-off are set by
`POST /certification/{advisor_id}/shadow|observed-lead|signoff` and **nothing derives them from an
advisor actually appearing in an assessment's `rater_ids` or leading one** (`certification.py:90-126`).

## What to build

- Make assessment **participation auto-count** toward the ladder: an advisor appearing in an
  assessment's `rater_ids` (shadow) or leading one (observed-lead) should increment
  `shadow_count`/`observed_lead_logged` automatically, rather than relying on the admin POST endpoints.
  Files: `workbench/certification.py`, `web/routers/certification.py`, `data/repository.py`.
- **Reconcile the two high-stakes thresholds** that overlap-but-differ: cert's `requires_certified_lead`
  (module Frontier / power Wide, `workbench/certification.py:73`) vs the committee trigger (power
  Established+, triad > None, module Frontier, `atlas/committee.py`). Align or document the relationship
  so the two gates don't silently disagree.

## Acceptance / verification

- Appearing in an assessment's `rater_ids` (or leading one) auto-increments the corresponding
  certification evidence — no honour-system admin POST required for the derived counts.
- The manual `.../shadow|observed-lead|signoff` endpoints remain only where genuinely needed, not as the
  sole source of evidence.
- The `requires_certified_lead` threshold and the committee trigger are reconciled (aligned or
  documented), with a test covering the overlap.

## Not in scope

- Rebuilding rating-request/dual-rating/committee linkage — it already works via `assessment_id`.
- The certification restructure / course certs (GRS-0127).
