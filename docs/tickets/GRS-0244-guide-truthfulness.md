# GRS-0244 — The Guide must describe the product that exists

**Status:** Planned (2026-07-31, first-time-user review). **Priority:** MED. **Type:** Bug (docs).
**Loop:** first-time-user coherence. **Extends GRS-0175.** **Relates to:** GRS-0188, GRS-0211.

## Why

The rewritten Guide (`/guide`) is good — and it now contradicts the product in two load-bearing
places, verified 31/07/2026:

1. **It describes the retired governance twice over.** The ASSESSMENT walkthrough step 4 says
   finalising is gated on "a second independent rater and a resolved consensus, and any high-stakes
   rating needs Rating Committee sign-off" — the dual-rating and committee machinery Methodology
   v1.6 / GRS-0188 made dormant — and then, two sections later, correctly describes the founder
   gate ("Send it to John"). A new advisor reads both and cannot know which is true. The wrong one
   is the kind of claim that makes everything else on the page suspect.
2. **The Deliverables section predates the client-report wave.** It walks the docx pack flow
   ("pick the document and an audience… review each AI-drafted section") and never mentions the
   client report editor, the six prose sections, the branded PDF or the share link — the flagship
   surface a new advisor most needs walked through, shipped 31/07.

Smaller, same page: the pipeline walkthrough says "ten stages" (the board shows seven headers on
staging — count and fix whichever is wrong); and the wizard section still calls it "the seven-step
wizard" while the stepper shows 7 numbered stages including Scenarios — verify the count against
the shipped stepper rather than assuming.

## Scope

1. **One governance story.** Remove the dual-rater/committee paragraph from the walkthrough;
   the founder-gate section stands as the only description; a line notes that peer governance is
   dormant by design (Methodology v1.6) for readers who find references elsewhere.
2. **A client-report walkthrough.** New Deliverables section: engagement → deliverable → report
   page → six sections → save → founder review where it applies → PDF download → share link, with
   the read-tracking disclosure explained to the advisor (what the client is told, what they can
   see). The docx pack flow stays, described as the internal/technical pack path.
3. **Count the counts.** Stages, steps, tabs — every numeral in the Guide checked against the
   shipped UI in the same session, corrected, and covered by the doc test below.
4. **A staleness guard.** A doc-structure test (pattern: `tests/test_docs_powers_adaptation.py`)
   pinning the Guide's governance claims and required sections — it fails if "Rating Committee"
   reappears outside the dormancy note, and fails if the client-report section is missing. Not a
   prose freeze; a contradiction tripwire.

## Test plan

1. The doc test above, verified to fail against today's Guide before the fix (the GRS-0221 lesson:
   guards must be shown to bite).
2. Manual: Guide read end-to-end against a staging session; each walkthrough step performed as
   written; discrepancies listed in the PR (found-and-fixed or found-and-ticketed).
3. Standing gate: tsc, ESLint (the Guide is a frontend page), pytest for the doc test.

## Out of scope

- Home/empty-state copy (GRS-0243) and the app-wide sweep (GRS-0205).
- The white paper (GRS-0237) — the Guide links it when it exists.

## Acceptance

A new advisor can follow the Guide's walkthroughs step by step against the live product and never
hit an instruction the product refuses or a gate the product no longer has.
