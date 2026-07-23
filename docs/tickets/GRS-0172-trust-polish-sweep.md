# GRS-0172 — Trust-polish sweep (staging-rerun assorted findings)

**Status:** Done (2026-07-23). The bounded low/med findings from the 2026-07-22 rerun.
**Loop:** rerun remediation.

## Items shipped

1. **LockedScore spacing** — explicit space before the uncertainty tag ("P10–P90MEDIUM" run-on).
2. **Pipeline stale 409 banner** — the illegal-move notice clears on the next successful create.
3. **ΔV label** — "(score points ×100)" → "in display score points (0–100 scale)" (the value was
   already in points; the annotation was wrong).
4. **Commission rate display** — `formatBps`: 375 bps renders "3.75%", never "3.8%" (a quoted rate
   is schedule-exact, not rounded).
5. **Module-table formula footnote** — the q_m table now discloses the min-term:
   L = α·(Σ weight·q_m) + (1−α)·min(critical q_m); the one table that invited recomputation no
   longer fails it unexplained.
6. **Prospect-name substance** — server-side refusal (422) of names with no letter/digit
   ("🚀🚀🚀" was a real CRM record polluting conversion stats); unicode names still pass.
7. **Bad-id bounce banner** — detail-page 404/422 bounces carry `?notfound=1`; the pipeline,
   portfolio, and engagements lists show a dismissible "that record doesn't exist or isn't in your
   book" notice instead of a mystery redirect.
8. **Engagement empty-state copy** — now points at linking an existing finalised assessment
   instead of only "Start an assessment" (personas nearly built duplicates).

## Left on the list (lower value / needs design)

Deliverables Audience column + duplicate-generation warning; US date locale; Academy
lesson-completion discoverability; drawer stage-history staleness; `/assessments/new` 422.
