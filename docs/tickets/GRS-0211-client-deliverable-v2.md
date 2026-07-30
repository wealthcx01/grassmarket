# GRS-0211 — The client deliverable, rebuilt: what it says

**Status:** Planned (2026-07-26, staging review items 9 and 10). **Priority:** HIGHEST.
**Loop:** founder-feedback remediation, Wave 3. **Extends GRS-0189 / ADR-0042.**

**This ticket owns the narrative and the content model.** The renditions are split out so they can
be built in parallel and reviewed separately: **GRS-0219** is the branded PDF, **GRS-0220** is the
interactive web page with read tracking, **GRS-0221** is the Stage 6 sticky-panel bug. Both
renditions consume the single content model defined here.

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
2. **One content model, rendition-agnostic.** A structured narrative model that knows its sections,
   their order, which tier each belongs to (GRS-0214), and which figures each references. It must
   contain no formatting: the PDF (GRS-0219) and the web page (GRS-0220) both consume it, and
   anything print-specific or web-specific leaking into the model makes the two renditions drift
   apart in front of a client.
3. **The maths moves out of the reader's way.** P10/P50/P90 never appear in the body. The body says
   "our central estimate is X, and on the evidence we have it could reasonably be between Y and Z".
   The appendix keeps the exact terms and points at `docs/ATLAS-Scoring-Explained.md`.
4. **Every figure is declared.** A section names the run values it cites, so a renderer can show
   them and the narrative assistant (GRS-0222) can be checked against them. A number that appears
   in prose without being declared is a build failure, not a proofreading problem.
5. **Approval gate unchanged.** Every AI-drafted section carries the founder review gate
   (ADR-0041, non-negotiable #8). Nothing reaches a client without a recorded approval.

## Test plan

1. Golden-master content test: one finalised assessment produces a content model matching a
   committed fixture, so prose regressions are visible in review.
2. Assert no P10/P50/P90 token appears outside the appendix section.
3. Declared-figure test: every numeric token in a section's prose appears in that section's
   declared figure set.
4. Approval test: an unapproved narrative section cannot enter a client-facing content model.
5. Manual: the founder's own Deutsche Börse record, rendered through GRS-0219 and GRS-0220.
6. Standing gate: pytest, pyright, ruff.

## Out of scope

- The PDF rendition (GRS-0219) and the web rendition (GRS-0220).
- The Stage 6 sticky-panel bug (GRS-0221).
- Free versus engaged tiering (GRS-0214).
- The narrative assistant (GRS-0222).
- Course assets (GRS-0215).
- Any change to scoring. The golden master stays byte-identical.

## Acceptance

The founder reads the Deutsche Börse review and it tells the story of that business, with the maths
in the appendix and every number traceable.

## What shipped — the content model (scope items 1–5)

`bcap_contracts.client_report` is the narrative spine, and `grassmarket.deliverables.client_report`
builds it from a finalised run. The four rules are enforced by the model itself, not by a renderer,
so neither rendition can opt out of one:

1. **Order is the report.** `SECTION_ORDER` — business → advantage → constraint → actions → value →
   appendix — is validated. A missing, repeated or out-of-order section does not construct. The
   report opens with the business and the BUSINESS section declares no figures at all, which is the
   structural answer to "it reads as a scorecard".
2. **The maths is out of the reader's way.** `P10`/`P50`/`P90` are refused anywhere but the
   appendix. The body says "our central estimate is X, and it could reasonably be between Y and Z".
3. **Every figure is declared.** Each section declares the numbers its prose may state, each with
   the run field it came from (`run.modules.APP_SERVER.q_m`). A number in prose that is not declared
   raises — a build failure, not a proofreading problem, exactly as the ticket asked.
4. **Nothing AI-drafted reaches a client unapproved.** An AI-drafted section must name its
   narrative, and `assert_client_ready` refuses a report whose drafts are not in the approved set.

**Prose is an input, not an invention.** "What this firm is and how it makes money" cannot be
derived from a scoring run, so the builder takes it and refuses loudly when a section has none
(`MissingReportProseError`). Fabricating it would be precisely the silent fallback non-negotiable #3
forbids. GRS-0222 will draft that prose; ADR-0041 approves it.

Two honesty behaviours are tested rather than assumed: an **unmodelled** V band declares no range at
all (ADR-0008 — printing one would claim a tight estimate we do not have), and an unassessed module
is **absent** from the appendix rather than zero-filled (D9).

Scoring is untouched: the golden master is unchanged and still passes.

### What this ticket does NOT make visible

Per the founder's rule that "shipped" means they can see it working, this ticket on its own changes
nothing the founder can open. It is the model both renditions consume; **GRS-0219 (branded PDF)** and
**GRS-0220 (interactive web page)** are what put it in front of them, and the existing docx preview
is still what the app serves until those land. Branding was named in the founder's complaint and
belongs to those two tickets.

Gate: ruff clean, pyright clean on both new modules, 37 new tests, golden master byte-identical.
