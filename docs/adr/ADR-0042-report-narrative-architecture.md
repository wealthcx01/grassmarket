# ADR-0042 — Report narrative architecture: story first, technique in the appendix

- **Status:** Proposed (2026-07-23). Founder-directed (feedback 23/07/2026, item 17); ratifies
  with GRS-0189.
- **Deciders:** Founder (structure and tone), Engineering (implementation).
- **Normative source:** ADR-0002 (three-layer value bridge; score-points and currency never
  mix), ADR-0008 (honest bands), ADR-0009 (AI narrative approval), ADR-0040 (one-number rule),
  GRS-0161 (deliverable presentation).

## Context

The deliverables compose in data order: scores, statements, tables, then an appendix — with
default-styled charts. The founder's verdict is that the formatting and context are far below
what the collected data and the design system support: the report should tell a story,
generally a good-news story, centred on the thing the client can do to improve their standing,
with technical material moved to an appendix.

## Decision

Every client-facing deliverable follows a five-part narrative:

1. **Executive letter** — where the client stands, the headline in words, led by strengths.
2. **The one thing** — the bottleneck and what fixing it unlocks, told in plain language.
3. **The path** — prioritised upgrades priced through the three-layer value bridge (cost £ /
   lever NPV £ / strategic ordinal — never a score-to-pounds conversion).
4. **Evidence highlights** — a small number of charts designed to the Bruntsfield system
   (Source Serif 4, paper/ink, Bottle Green), each titled and annotated.
5. **Technical appendix** — every formula, module table, uncertainty method, version block, and
   the AI-approval trail. Nothing technical is deleted; it is relocated.

The AI drafter (approval-gated) writes sections 1–3 from the scored document; the deterministic
template remains the offline fallback. An Executive Summary .pptx variant (same tokens, same
gates and watermarks) joins the deliverable set for boardroom use.

## Consequences

- Honesty invariants carry into narrative: every quoted figure recomputes exactly (ADR-0040);
  ranges accompany points; the good-news framing may order content but never omits a gate,
  caveat, or uncertainty statement.
- Deliverable generation gains a structural review point: the founder gate (ADR-0041) now
  reviews a story, which is the artefact clients actually receive.
- python-pptx joins python-docx in the report stack.
