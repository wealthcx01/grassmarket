# GRS-0244 — The Guide must describe the product that exists

**Status:** DONE (2026-08-20). _Previously recorded as: Planned (2026-07-31, first-time-user review). **Priority:** MED. **Type:** Bug (docs)._
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

---

## Status reconciliation — 2026-08-01

**DONE** — shipped 2026-08-20, all four scopes.

## Scope 3: both counts were already right

The ticket says to count and fix whichever is wrong. Counted:

| Claim | Shipped | Verdict |
|---|---|---|
| "board holds ten stages" | `PipelineStage` has **10**; `PIPELINE_STAGES` renders all 10 as columns | **correct** |
| "the seven-step wizard" | `WIZARD_STEPS` has **7** entries | **correct** |

The ticket's observation that "the board shows seven headers on staging" was not a Guide error —
the board does render all ten. Nothing was changed; both numerals are now **pinned by tests** that
read the enum and the shipped component, so the next change to either fails here.

### A test that nearly accused a correct Guide

The first version of the wizard-count test counted `{ title:` inside the `WIZARD_STEPS` block and
reported **8**. The eighth match was the declaration's own **type annotation** —
`{ title: string; component: ... }[]` — not a step. Had I trusted it, I would have "corrected" a
Guide that was already right, and shipped a false numeral to fix an imaginary one.

The regex now requires `{ title: "`. Worth recording because the failure mode is the same one the
whole ticket is about: a plausible-looking claim that nobody checked against the thing itself.

## Scope 1 — one governance story

The walkthrough's note told an advisor that finalising needs a second independent rater and Rating
Committee sign-off. ADR-0041 and Methodology v1.6 made that machinery **dormant**, and two sections
later the Guide correctly described the founder gate. An advisor read both and could not know which
was true.

The note now describes the founder gate only, and carries one sentence saying peer governance is
specified, built and **dormant by design** — for readers who meet references to it elsewhere. That
sentence is deliberate: silently deleting the mention would leave the Methodology's own §8/§9
looking like a live requirement the product ignores.

## Scope 2 — the client-report walkthrough

A new section, placed **before** the docx packs because it is the document a client actually reads:
engagement → deliverable → report editor → six sections → declared figures → founder review →
branded PDF → share link. It explains the declared-figure refusal in the advisor's terms (a number
the assessment did not produce is refused, and the refusal names it), and discloses read tracking
honestly — what the client is told before anything is recorded, what the advisor sees back, and
that a client who prints the PDF shows as having read nothing.

The docx pack section stays, re-framed as the internal and technical path rather than as *the* way
to produce a client document, which is what it read as before.

## Scope 4 — the tripwire, verified to bite

`tests/test_docs_guide_truthfulness.py`. **Checked against the pre-fix Guide first: 7 of its 10
tests failed** — the governance contradiction and the whole missing walkthrough. A guard nobody has
watched bite is not yet a guard (the GRS-0221 lesson).

It is a **contradiction tripwire, not a prose freeze**: the Guide is copy and will be reworded. What
it holds is that "Rating Committee" cannot reappear except in a sentence that also says *dormant*,
that the client-report section cannot vanish, and that the two numerals must match the enum and the
component they describe. Comment lines are stripped before matching, so the code comments explaining
*why* the copy says what it says do not trip the check on the copy itself.

## Not done

- **No manual staging read-through** (test-plan item 2). The walkthroughs were verified against the
  source of each surface they describe rather than by performing them in a browser session. The
  claims most at risk — governance, the report route, the counts — are the ones now covered by the
  test.
