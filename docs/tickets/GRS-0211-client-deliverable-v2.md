# GRS-0211 — The client deliverable, rebuilt: branded PDF and an interactive web report

**Status:** Planned (2026-07-26, staging review items 9 and 10). **Priority:** HIGHEST.
**Loop:** founder-feedback remediation, Wave 3. **Extends GRS-0189 / ADR-0042.**

## Why

The founder opened Deutsche Börse at 100% coverage, went to Summary and Interpretation, downloaded
the Deliverable Preview, and wrote: "It is terrible. It is so complicated, doesn't read well at all
and has no branding."

This is the artefact the client sees. It is the only part of Grassmarket a paying client ever
touches, and it is the worst part of the product. GRS-0189 was written for this and has not been
started. This ticket replaces it with something specific enough to be built.

What the founder asked for, in their words:

- the final review delivered as a **PDF and as an interactive web page**, both Bruntsfield branded
  at a minimum,
- interaction on the web version tracked, so we know what the client read,
- the scoring explained far better, in "clear and simple (not simplistic) English with a lot of
  detail",
- the maths disambiguated away from the reader on both the client and the advisor side,
- the sections that already work better ("What this means", "Maturity Radar", "How Platform Value
  builds up", "Module breakdown") kept and made more visual,
- narrative closer to the **Acquired** podcast: a story about the business that uses the 7 Powers
  as an analytical spine rather than presenting a scorecard.

There is also a straightforward layout bug: the "Platform Value Finalised" box is fixed on the page
and the "recommended to sell" box scrolls underneath it.

## Scope

1. **Structure, borrowed from how Acquired actually works.** The report opens with the business,
   not the score. Order:
   - what this firm is and how it makes money, in plain prose,
   - where its durable advantage sits, framed through the Powers that apply, and where it does not,
   - the honest reading of what is holding it back,
   - what to do about it, with the levers ranked and priced,
   - what that is worth if they act,
   - **technical appendix**: coefficients, weights, uncertainty method, coverage, the full module
     breakdown, every number the body refers to.
   No score appears in the body without a sentence saying what it means for this firm.
2. **Two renditions from one content model.** A single narrative model produces:
   - **PDF** via the python-docx/report stack, Bruntsfield branded: paper/ink palette, Bottle
     Green, Source Serif 4 and Inter, cover, running heads, page numbers.
   - **Interactive web report** at a signed per-client URL, same content, with the radar, the
     value build-up and the module breakdown as live visuals rather than flat images.
3. **Read tracking on the web version**, per section, tied to the client link. Recorded against the
   engagement so the advisor can see what was read and for how long. Disclosed on the page; no
   covert tracking.
4. **The maths moves out of the reader's way.** P10/P50/P90 never appear in the body. The body says
   "our central estimate is X, and on the evidence we have it could reasonably be between Y and Z".
   The appendix keeps the exact terms and points at `docs/ATLAS-Scoring-Explained.md`.
5. **Fix the sticky box.** The Platform Value Finalised panel and the recommended-to-sell panel
   stop overlapping on scroll. Reproduce at the founder's viewport first.
6. **Approval gate unchanged.** Every AI-drafted section carries the founder review gate
   (ADR-0041, non-negotiable #8). Nothing reaches a client without a recorded approval.

## Test plan

1. Golden-master report test: one finalised assessment renders to a PDF and a web report whose
   text content matches a committed fixture, so prose regressions are visible in review.
2. Assert no P10/P50/P90 token appears outside the appendix section of the rendered body.
3. Approval test: an unapproved narrative section cannot render into a client-facing artefact.
4. Vitest per file for the web report shell, the radar, the value build-up and the scroll
   behaviour of the two panels.
5. Manual: the founder's own Deutsche Börse record rendered both ways, both attached to the PR.
6. Standing gate: pytest, pyright, tsc, ESLint.

## Out of scope

- Free versus paid tiering of what the client receives (GRS-0214).
- The scenario narrative assistant (GRS-0213).
- Course assets (GRS-0215).
- Any change to scoring. The golden master stays byte-identical.

## Acceptance

The founder downloads the Deutsche Börse review as a PDF and opens the web version, and both read
like something Bruntsfield would put its name on. The maths is in the appendix. The panels do not
overlap.
