# GRS-0116 — Clarify the engagement ↔ assessment link

**Status:** Shipped
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** GRS-0039 (LinkAssessmentControl)

## Why

An engagement carries an assessment behind it, but the relationship is illegible in the UI: a tester
looking at an engagement can't tell *which* assessment it consumes, what state that assessment is in, or
how to get to it — and from an assessment there's no way to see which engagement(s) rely on it. The
`LinkAssessmentControl` already exists (GRS-0039) so the wiring is present, but the surfaced information
is thin and one-directional. The founder also flagged that the vocabulary (engagement vs assessment vs
deliverable) reads as interchangeable when it isn't. This ticket makes the link explicit and two-way and
tightens the in-copy vocabulary — it is a clarity/UI change, not a data-model change.

## What to build

**Engagement detail (`frontend/app/engagements/[id]/page.tsx`, `DeliverablesPanel.tsx`)**
- Show the linked assessment's identity and live state inline: status, Platform Value (V), coverage %, and
  last-updated, with a clear link through to that assessment. REUSE the existing `LinkAssessmentControl`
  (`LinkAssessmentControl.tsx`) for the bind/unbind action rather than adding a second linking path.
- Tighten the surrounding copy so "engagement", "assessment", and "deliverable" are used consistently and
  each is briefly disambiguated where they first appear together.

**Assessment detail (`frontend/app/assessments/[id]/`)**
- Add the reverse view: show which engagement(s) consume this assessment, with a link back to each. This
  closes the two-way loop so neither screen dead-ends into the other.

## Acceptance / verification

- From an engagement, a tester can see the linked assessment's status, V, coverage, and last-updated, and
  click through to it.
- From an assessment, a tester can see the consuming engagement(s) and click back to each.
- The engagement/assessment/deliverable vocabulary is consistent across both screens.

## Not in scope

- The watermarked end-to-end demo dataset — GRS-0117.
- Backlink/breadcrumb navigation across the wider flow — GRS-0118.
- Any change to how assessments are linked or stored (reuse GRS-0039's mechanism as-is).

## What shipped (Status: Shipped — branch grs-0116-engagement-assessment-link)

Made the engagement ↔ assessment link legible in both directions:

**Engagement → assessment** (`app/engagements/[id]/page.tsx`)
- Each linked assessment now renders a rich card (`LinkedAssessment`) showing its **subject**, a **state**
  badge (Draft / In progress / Finalised), **Platform Value (V)** with the uncertainty rating when
  finalised, **coverage %**, and **last-updated**, with a clear "Open →" link through. State comes from
  the lightweight `brokeragePortfolio()` summary (one call, matched by `assessment_id`) — no per-
  assessment fetch. `LinkAssessmentControl` (GRS-0039) still owns bind/unbind. Copy tightened to
  disambiguate engagement vs. assessment vs. deliverable.

**Assessment → engagement** (`components/ConsumingEngagements.tsx`, mounted in `WizardClient`)
- The reverse view: a "Consumed by engagement(s):" line under the assessment title linking back to each
  engagement that consumes it, filtered client-side from `listEngagements` (owner-scoped, no new
  endpoint). Renders nothing when the assessment isn't linked anywhere yet — so neither screen
  dead-ends into the other.

**Backend** — `BrokeragePortfolioEntry.coverage` (assessed / applicable, Not-Applicable excluded),
computed in `list_brokerage_portfolio`; schema + TS mirror updated.

## Acceptance / verification

`tests/test_brokerage_portfolio.py::test_portfolio_surfaces_coverage`. The engagement shows each linked
assessment's identity + live state with a link through; the assessment shows which engagement(s) consume
it; the two-way loop no longer dead-ends. Backend + frontend gates green; schema parity green.
