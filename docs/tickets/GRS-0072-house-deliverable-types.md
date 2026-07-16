# GRS-0072/0073 — House deliverable types (Outside Read Deck · Note · Primer · Strategic Assessment)

**Status:** Audited — delta specified; build gated (see Gates)
**Loop:** Track A (estate reconciliation — deliverable types)
**Branch:** `grs-0072-house-deliverables-audit`
**Source of truth for house structure:** the OneDrive ASX / NSI packs (**not** in this repo) +
`NEXT-STEPS-2026-07.md` §3.2.

## Why

The estate sweep found that the *real* house output is **Outside Read Deck, Note, Primer, and
Strategic Assessment / 7 Powers Brief** (the ASX/NSI packs), and the PRD's seven types don't include
them (NEXT-STEPS §3.2). This ticket audits the gap against the shipped deliverable builder and
specifies the build — but does not add half-built types (a type in the enum with no working builder
would 500 / render a blank button, violating "every button works").

## What ships today (GRS-0015/0018)

A clean, well-factored single-run builder architecture (`deliverables/service.py`
`_SINGLE_RUN_BUILDERS`): each `DeliverableType` → a `build_*(context, mode, narratives) -> bytes`
docx builder, gated (client-usable + committee + uncertainty), reproducible from the immutable run.
Shipped types: Executive Summary, Platform Power Report, Infrastructure Heatmap, Modernisation
Roadmap, Technical Appendix, Workshop Output, Score Evolution. These cover the advisor's day-1
diagnostic needs; the house-branded narrative types are the refinement.

## The house types → existing builders (the delta)

| House type | Closest shipped builder | Gap to a house artifact |
|---|---|---|
| **Strategic Assessment / 7 Powers Brief** | Platform Power Report + Executive Summary | The flagship client narrative: headline V, the 7-Powers moat story (benefit/barrier per power → the strategic reading), the L constraint, the "so what". Composes existing sections but needs the house **narrative structure + order** from the packs. |
| **Outside Read Deck** | *(none — deck, not report)* | A slide-deck outside-in read. New render path (deck layout, not the `start_document` report template). House deck structure from the packs. |
| **Note** | Executive Summary (closest in brevity) | A short house **Note** — 1–2 pages, a specific house voice/structure. |
| **Primer** | *(none)* | An educational primer on a company/sector — house explainer structure. |

Also per §3.2: check the shipped **Workshop Output** template against the real **Outside Read**
pattern (they may be the same artifact under two names).

## Gates (why this is a ticket, not a build in this PR)

1. **Founder decision #5** (NEXT-STEPS §4): approve harvesting the ASX/NSI pack structure
   (anonymised) as deliverable templates. **The house structure IS the thing being approved** —
   building it from scratch would both pre-empt that decision and risk diverging from real house
   style (rework). Recommended: approve.
2. **The packs are not in this repo** and (per the carried-over estate rule) are never committed —
   they're reference-only; the templates are authored *from* them, and any case-study/vignette use is
   anonymised first.
3. **Deck render path** (Outside Read Deck) is genuinely new plumbing (slides, not the report
   template) — a larger build than the other three.

## Recommended build sequence (once #5 clears + packs available)

1. **Strategic Assessment / 7 Powers Brief** first — highest value, mostly composes existing
   sections; add `DeliverableType.STRATEGIC_ASSESSMENT` + `build_strategic_assessment` + register in
   `_SINGLE_RUN_BUILDERS` + `title_for` (the registry keeps title/builder in lockstep — no 500).
2. **Note** and **Primer** — light single-run builders on the same pattern.
3. **Outside Read Deck** — new deck render path; reconcile against Workshop Output first.
4. Frontend: extend the `DeliverableType` TS union + the DeliverablesPanel type picker for each, as it
   lands (one working builder per enum value — never a dead option).
5. Golden-style test per type: renders non-empty docx, honours the client-usable + committee gates.

## Guardrails

- Every new enum value ships **with** a working builder + title in the same PR (the
  `_SINGLE_RUN_BUILDERS` single-source-of-truth pattern) — no dead buttons.
- Score-domain only unless the value bridge is explicitly included (ADR-0002); honest uncertainty
  (§7) and Not-Assessed coverage (§3.2) as every existing builder does.

## What shipped (this PR)

- `docs/tickets/GRS-0072-house-deliverable-types.md` — this audit + delta spec. No code change.
