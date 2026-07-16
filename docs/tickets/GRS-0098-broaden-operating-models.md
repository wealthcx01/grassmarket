# GRS-0098 — Broaden beyond retail brokerages (framing + naming)

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Phase:** A (build now)
**Depends on:** ADR-0025 (profiles) / GRS-0077–0079

## Why

The portfolio and wizard today assume the subject is a retail brokerage, but the tool must cover
**wealth managers** (boutiques like St. James's Place through to commercial banks like Standard
Chartered — some digital, some advice-only, several not brokerages at all) and **infrastructure
players** (OMS vendors, market-data providers, exchanges). This is not new framework work: it is the
**profiles program** already specced as ADR-0025 / GRS-0077–0079 — the mechanism, exchange content and
wizard selector exist there. What this ticket adds is the **portfolio-side framing and naming**: retire
"Your Brokerages" (too narrow) for a neutral label (e.g. "Your Portfolio" / "Assessments"), rework the
create form and its copy ("New brokerage — subject") so the `segment` field becomes the real
operating-model **profile selector** wired to GRS-0079, not a cosmetic tag.

## What to build

**Portfolio list + create form (`app/assessments/page.tsx`)**
- Rename the page heading and nav label away from "Your Brokerages" to an operating-model-neutral term.
- Rework the create form so the subject-type / `segment` control is the profile selector (retail /
  wealth / infrastructure), with copy that no longer presumes "brokerage". REUSE the GRS-0079 wizard
  profile selector rather than authoring a second selector — this is the same profile, chosen earlier.

**Wizard copy (`components/steps.tsx`)**
- Sweep step titles and blurbs that hardcode "brokerage" so they read for the selected operating model.

## Acceptance / verification

- The portfolio page and create form carry no "brokerage"-only wording; the label is operating-model
  neutral.
- Creating an assessment selects a profile (retail / wealth / infrastructure) that feeds the same
  profile mechanism as GRS-0079 — not a free-standing field.
- Existing retail assessments continue to open and score unchanged (retail stays the v1 default).

## Not in scope

- The profile mechanism, exchange/wealth content, and the wizard selector itself — GRS-0077–0079.
- Per-row completeness metric — GRS-0099.
- Entity/company linking — GRS-0100 (Phase B).
