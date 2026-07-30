# GRS-0223 — "All the scores seem surprisingly similar": find out why

**Status:** Planned (2026-07-23 item 6, restated 2026-07-26). **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 1. **Relates to:** GRS-0179 (the maths document),
GRS-0086 (four-index v1.4, gated).

## Why

Buried in the founder's item 6 is a sentence that is not a documentation request:

> "Also all the scores seem surprisingly similar so far..?"

They are right to be suspicious, and this deserves its own investigation rather than a paragraph in
an explainer. If every firm scores about the same, the score is not discriminating, and an
assessment that cannot tell two firms apart is not worth selling however well the maths is
documented. GRS-0179 explains the arithmetic; it does not answer this.

A prior note in the programme already flagged "V-compression" as a suspected effect. That suspicion
has never been measured.

## Scope

This is an analysis ticket first. Code changes, if any, come after the finding and require an ADR
and a methodology version (non-negotiable #2). **No silent recalibration.**

1. **Measure the dispersion.** Take every assessment on staging and in the demo set, plus generated
   documents spanning the plausible input range, and report the actual distribution of V and C:
   spread, quartiles, and how much of the theoretical range is used in practice.
2. **Find where the compression happens.** Walk the pipeline stage by stage: subcomponent scores →
   module quality `q_m` → weighted aggregation → V. At which step does the variance collapse? Name
   the step and the mechanism. Candidates worth testing rather than assuming:
   - the bottleneck/minimum behaviour pulling every module toward its weakest subcomponent,
   - weights so even that no module can move the total,
   - a rating-gate mapping that buckets a wide continuous range into a few words,
   - assessors clustering on the middle of the rubric, which would be a rubric problem, not a
     maths problem.
3. **Separate the two possible causes.** Compressed *because the maths compresses*, or compressed
   *because the inputs are all similar*? Distinguishable by feeding deliberately extreme synthetic
   documents through the engine. If extremes produce extremes, the engine is fine and the rubric or
   the assessors are the story. That distinction changes what we fix.
4. **Write it up** as `docs/analysis/score-dispersion-2026-07.md`: what was measured, what was
   found, and what should change. Feeds GRS-0179 so the explainer can be honest about it.
5. **If a change is warranted**, it lands as an ADR plus a methodology version, never as an edit.
   The golden master stays byte-identical until that ADR is accepted.

## Test plan

1. A dispersion test committed with the finding: a fixture set of deliberately different firms must
   produce V values spread by at least the margin the analysis concludes is right. This is the
   regression guard that stops compression creeping back.
2. Golden master byte-identical. This ticket measures; it does not change scoring.
3. Standing gate: pytest, pyright, ruff.

## Out of scope

- Changing scoring, weights or coefficients. That is a separate ADR and methodology version.
- The C-index taxonomy work (GRS-0212).
- The explainer document (GRS-0179), which consumes this.

## Acceptance

The founder gets a straight answer to "why do all the scores look the same", backed by measurements
rather than reassurance, and a recommendation on whether anything needs to change.
