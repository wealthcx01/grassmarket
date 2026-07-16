# GRS-0099 — Portfolio home: detail + completeness

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Phase:** A (build now)
**Depends on:** —

## Why

The portfolio home ("Your Brokerages") is basic and lacks the at-a-glance detail a senior operator
expects, and — the founder's sharpest point — there is **no "how complete is this assessment" metric**
on any row. An advisor can't tell which assessments are barely started versus ready to finalise. The
engine already computes coverage per assessment, so this is a **surfacing** job, not new computation:
put a per-row completeness / coverage % on each entry alongside richer detail and a better use of the
space.

## What to build

**Portfolio list (`app/assessments/page.tsx`)**
- Add a per-row completeness / coverage indicator (percentage plus a compact visual) so each assessment
  shows how far along it is.
- Enrich each row with the detail the list currently omits (subject, profile/segment, status, V when
  scoreable, last updated) and rework the layout for a more considered use of space.

**Contract surfacing (`BrokeragePortfolioEntry`)**
- Surface the already-computed coverage on `BrokeragePortfolioEntry` so the list renders it without the
  frontend recomputing anything. REUSE the engine's existing coverage output — do not re-derive
  completeness in the UI.

## Acceptance / verification

- Every portfolio row shows a completeness / coverage % sourced from the engine's coverage output.
- `BrokeragePortfolioEntry` carries the coverage value; the frontend reads it rather than recomputing.
- A freshly created assessment reads near-0% and a fully-entered one reads near-100%.

## Not in scope

- The completeness *computation* itself (engine coverage already exists) — surfacing only.
- Renaming / broadening the page — GRS-0098.
