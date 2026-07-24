# ADR-0046 — Embedding the 7 Powers mathematics, under Helmer's permission grant

- **Status:** Proposed (2026-07-23). Founder-directed; ratifies with GRS-0180. External
  reviewer: **Hamilton Helmer will review the resulting work.**
- **Deciders:** Founder (rights and scope of use), Engineering (embedding architecture),
  Hamilton Helmer (review of the adaptation).
- **Normative source:** ADR-0007 (benefit/barrier triad), Methodology §4 (Powers), §5.4
  (P computation), non-negotiable #2 (scoring changes are ADRs + methodology versions).

## Context

ATLAS's Powers lens has always been Helmer-derived in structure (Power requires a Benefit and a
Barrier; strength = min(Benefit, Barrier), ADR-0007), but the source material — the 7 Powers
audiobook supplement (Helmer, 2016: the Fundamental Equation of Strategy, per-power Surplus
Leader Margin derivations, the Power Intensity Determinants, the Power Dynamics toolkit and
glossary) — was copyright-restricted, so the product could only gesture at it.

**That constraint has changed.** The founder holds personal permission from Hamilton Helmer to
embed and adapt the supplement — specifically the mathematics — into our use case: **wealth
platforms**, defined as wealth advisory firms, brokerages, and exchanges. The grant was
communicated to engineering on 2026-07-23. Helmer will review the work produced under it, which
sets the quality bar: the adaptation must be faithful where it embeds and explicit where it
adapts.

## Decision

1. **Rights registration.** The grant (grantor, grantee, date, scope: the supplement's
   mathematics, adapted for wealth platforms; condition: Helmer reviews the output) is recorded
   in this ADR and in `docs/ATLAS-7Powers-Adaptation.md`'s front matter. Every surface that
   embeds the material carries the attribution line: *"Adapted from Hamilton Helmer, 7 Powers:
   The Foundations of Business Strategy, with the author's permission."* Material outside the
   grant's scope (narrative chapters, case-study prose) stays out.
2. **One normative adaptation document** — `docs/ATLAS-7Powers-Adaptation.md` (authored in
   GRS-0180 from the full-supplement extraction): the Fundamental Equation with every symbol
   defined; per power, the definition, Benefit, Barrier, Surplus Leader Margin formula, and
   intensity determinants — each *adapted* with worked wealth-platform readings for the three
   segments (retail brokerage, wealth advisory, exchange/market infrastructure); the Power
   Dynamics time-window mapping. Where we adapt rather than transcribe, the document says so in
   the text, so Helmer's review can distinguish his mathematics from our application of it.
3. **The wizard embeds the adaptation** (GRS-0201): per-power guidance in the Powers step is
   rebuilt from the adaptation document — benefit/barrier definitions, intensity determinants
   as rating anchors, and one segment-correct example per power — replacing today's summary
   guidance in `frontend/lib/powerGuidance.ts`. The Guide's Seven Powers section follows the
   same source.
4. **Scoring is unchanged at this stage.** The P computation (strength = min(Benefit, Barrier),
   w-weighted mean, Methodology §5.4) already implements Helmer's dual condition and does not
   move; the golden master stays byte-identical. Any future quantitative use of the SLM
   formulas (for example an SLM-informed intensity input to benefit/barrier grades) is a
   **separate ADR + Methodology v1.7**, taken only after Helmer's review of this stage.
5. **The review loop is a deliverable.** GRS-0201 produces a "Helmer review packet": the
   adaptation document, the wizard Powers-step screens, and the §4/§5.4 methodology extract —
   assembled for the founder to send, with a recorded slot for the feedback and a follow-up
   amendment to this ADR when it lands.

## Consequences

- The Powers lens gains a citable, author-sanctioned mathematical foundation — a genuine
  differentiator for technical due-diligence audiences.
- The adaptation document becomes the single source for all Powers content (wizard, Guide,
  Academy, reports); drift between surfaces becomes a defect, not a style choice.
- The permission is personal and scoped: if the scope ever needs to widen (for example,
  Academy course content quoting narrative passages), that is a new grant, not an
  interpretation of this one.
- Helmer's review may require changes; the ADR stays Proposed until the founder confirms the
  packet has been reviewed, then moves to Accepted with the outcome recorded.
