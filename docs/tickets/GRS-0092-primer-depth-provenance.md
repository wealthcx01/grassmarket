# GRS-0092 — Primer depth, rationale & provenance

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** —

## Why

The primer (`/guide`) is worth having but the founder's verdict is that it "shouldn't be a two-minute
flick-through" — it is too thin. The audience is smart, experienced **senior operators** who can handle
complexity, so the primer should be **more detailed and academic, but plain-English and clearly
communicated**. Today it explains the *what* without the *why*: it does not convey the rationale behind
Platform Power, where the framework is derived from, or how it works end-to-end. This ticket expands the
primer from a flick-through into a proper explainer.

## What to build

**Primer (`frontend/app/guide/page.tsx`)**
- Add the **rationale behind Platform Power** — why the framework exists and what question it answers.
- Add **provenance / derivation**: where the framework comes from — Hamilton Helmer's 7 Powers plus the
  infrastructure deep-dive lineage — the "why" behind the design.
- Add a **how-it-works end-to-end** walkthrough of the framework.
- Recalibrate tone throughout: detailed and academic, yet plain-English for senior operators.
- Carry the ATLAS → Platform Power naming (GRS-0090) wherever the primer names the framework.

## Acceptance / verification

- The primer explains the rationale, the derivation (Helmer + infrastructure deep-dive lineage), and how
  the framework works end-to-end — not just what it is.
- Tone is detailed/academic but plain-English; no unexplained jargon.
- The primer no longer reads as a two-minute flick-through.

## Not in scope

- The lens/label content (GRS-0093), the 7 Powers detail (GRS-0094), evidence grades (GRS-0095), reading
  outputs (GRS-0096) — sibling primer tickets.
- The guide navigation shell (sequenced last, separate ticket).
