# GRS-0133 — Gamify My Earnings + earnings chart

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** ADR-0026 (Earnings v7) / GRS-0075–0076; GRS-0123 (product-course carrot)

## Why

My Earnings today is functional but flat — it does not motivate. In the Part-2 review the founder asked for
two near-term things: **a chart/graph** and light **gamification** to incentivise more activity. The point is
the carrot: an adviser should *see* earnings building and *feel* the pull of the next close. The deeper
earnings substrate (the Holy Corner plan, and the EliteVault-style commission relationships with Benzinga /
Brandfetch / OpenBB) is a later build — this ticket is purely the incentive/visual layer over the numbers the
Earnings v7 kernel already computes.

## What to build

**Frontend (`frontend/app/earnings/page.tsx` + earnings views)**
- An **earnings chart** — earnings over time, broken down by product / commission stream (Stream A product vs
  Stream B consultancy, per ADR-0026), and progress toward a target.
- Light **gamification**: milestones, streaks, and a forward "you could earn £X if you close Y" nudge tied to
  the per-product commission figures surfaced in the courses (GRS-0123).

**Reuse, do not re-derive**
- All figures come from the **Earnings v7** compute (ADR-0026 / GRS-0075–0076). Do not re-implement rates or
  totals in the frontend — read the computed commission lines/summary.

**Constraint**
- Honour the currency-free vs Money boundary (ADR-0002): real £ appears only inside the Money domain
  (earnings is one of the few surfaces that legitimately shows currency); nothing here mixes score-points and
  money in one figure.

## Acceptance / verification

- The earnings page renders a chart of earnings over time with a product/stream breakdown, driven entirely by
  the Earnings v7 computed values (no rates duplicated in the frontend).
- At least one forward-looking incentive element (target progress, milestone, or "you could earn £X" nudge)
  is present and reads from real computed figures.
- No change to earnings computation, rounding, or the pay-when-paid lifecycle.

## Not in scope

- The Holy Corner / EliteVault-style earnings substrate and deeper commission relationships (later build).
- Any change to commission rates or the v7 config (governed by ADR-0026).
