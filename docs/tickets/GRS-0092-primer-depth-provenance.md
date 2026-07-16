# GRS-0092 — Primer depth, rationale & provenance

**Status:** Shipped
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** —
**Branch:** `grs-0092-primer-depth-provenance`

## What shipped

Three new sections at the top of the primer (`app/guide/page.tsx`) that give it the missing depth —
why the framework exists, where it comes from, and how it runs end to end — before the existing
"shape of it" content:

- **"Why Platform Power exists"** — the one question under every engagement (can this platform create
  value and hold it?), why answering it means looking at economics + strategy + technology at once, and
  what the framework buys: judgement made **consistent · comparable · defensible** (survives a board's
  / an acquirer's technical due diligence).
- **"Where the framework comes from"** (provenance) — **P** is Hamilton Helmer's *7 Powers* used
  verbatim (benefit protected by a barrier); **L** is the infrastructure deep-dive lineage (9 modules /
  51 subcomponents, front end to liquidity); **B** is the hard economic register. The synthesis —
  strategy + technology + economics under one graded, uncertainty-aware method — is the whole idea.
- **"How it works, end to end"** — a numbered 6-step pipeline (gather + grade evidence → rate against
  rubric anchors → engine computes B/P/L with the bottleneck cap → Monte Carlo P10/P50/P90 → rule-based
  gates for the headline words → the value bridge prices the gaps) ending at the Platform Power Report.

Tone recalibrated to detailed-yet-plain for senior operators; the ATLAS → Platform Power naming
(GRS-0090) is carried throughout.

## Acceptance / verification

The primer now opens with rationale, provenance (Helmer lineage + infrastructure deep-dive + business
economics), and an end-to-end walkthrough, in plain-English-for-operators tone, naming the framework
"Platform Power". Frontend type-check · lint · vitest green.

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
