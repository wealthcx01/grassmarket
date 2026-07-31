# GRS-0159 — Repeatable demo-data seed (Revolut + HL end-to-end)

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: Done (2026-07-22). `grassmarket.demo.brokerage_showcase` + extended `scripts/seed_demo.py`:._
Revolut/HL/WeBull complete DEMO assessments (V+C), engagements, real deliverables, £49,500 statement;
idempotent; one-command path documented in the README. So a demo instance is never empty when showing
advisor hires.
**Priority:** HIGH — demo enabler. **Loop:** demo-readiness.

## Why

To show the studio to potential advisor hires it must be populated on demand. The staging run built a
faithful end-to-end for Revolut + Hargreaves Lansdown (pipeline → finalised sandbox assessment →
deliverables → engagement → recorded product commissions → £49,500 earnings). That was driven by ad-hoc
scripts (`tools/staging-e2e/brokerage_e2e.py`, `earnings_e2e.py`). Make it a first-class, repeatable seed.

## Scope

- New `scripts/seed_demo.py` (extend the existing stub): builds the two showcase brokerages
  (Revolut, HL) as **complete** assessments from review-grounded inputs, finalises them (sandbox),
  generates the standard deliverables, opens engagements, and records the illustrative product
  commissions so `/earnings` shows a populated statement.
- Idempotent (safe re-run); clearly demo-flagged so it's never confused with real data.
- Keep the input mappings in-repo (not scratch) so they're reviewable and versioned.
- Document a one-command "spin up a demo instance" path.

## Acceptance

One command populates a clean environment with the two showcase reports, a live pipeline, and a
non-zero earnings statement — ready to demo.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `1da1509` (GRS-0159: repeatable demo-data seed — the brokerage showcase).

This ticket carried no *What shipped* record; the commits above are that record.
