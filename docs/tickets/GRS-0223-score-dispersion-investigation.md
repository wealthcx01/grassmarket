# GRS-0223 — "All the scores seem surprisingly similar": find out why

**Status:** In review (2026-07-30, PR pending) — **measured, answered, no engine change
recommended.** **Priority:** HIGH. **Loop:** founder-feedback remediation, Wave 1.
**Relates to:** GRS-0179 (the maths document), GRS-0086 (four-index v1.4, gated).
**Produced:** `docs/analysis/score-dispersion-2026-07.md` + `tests/test_score_dispersion.py`.
**Spun out:** GRS-0227 (surface dispersion beside the score — the one recommendation buildable now).

## The answer

**The engine is not compressing anything. Aggregation is.**

- Fed extremes the engine produces extremes: V spans **0.185–1.000**, i.e. 0.815 of the nominal
  range. That rules out the ticket's first two hypotheses — the bottleneck term and over-even
  weights — as the cause. Neither stops an extreme firm scoring at an extreme.
- The mechanism is measurable. Varying only *how internally consistent a firm is*, with the engine
  and coefficients untouched, moves sd(V) from **0.057 to 0.153 — a 2.7x range**. V averages nine
  modules, seven powers and four metrics; a mixed firm is pulled to the middle by construction.
- A hypothesis worth killing: the three real firms *look* like their components cancel. Under random
  sampling sd(V) actual / sd(V) if independent = **1.002**. The apparent cancellation is noise in a
  sample of three, not structure.

**Two amplifiers, one of them large and addressable:**

1. **The rubric is used at about a third of its width.** 92.6% of module ratings across the three
   showcase specs are Developing or Advanced (score indices 0.5 and 0.8) — a 0.3-wide band inside a
   0.8-wide scale. Drawing from all four levels instead widens sd(V) by **2.06x**. This is the
   ticket's fourth hypothesis and the largest thing anybody can actually fix.
2. **B saturates.** The business index hits 1.000 at roughly twice Revolut's metrics and all three
   real firms sit at 0.767–0.983. B carries theta_B = 0.3 of V and barely discriminates among firms
   of real size; widening the metric range 100x moved sd(V) only 0.0614 to 0.0631.

A structural note rather than an amplifier: `MaturityLevel.score_index` floors at **0.2**, so no
q_m and no L can fall below 0.2. The bottom fifth of the nominal range is unreachable by
construction — a scale choice, not a bug, but the explainer must say so or every low score is
misread.

## Recommendation: no engine change, and no recalibration

Nothing measured shows the maths misbehaving. Widening the output distribution by moving
coefficients would be fitting the scale to the marketing rather than to the method, and per
non-negotiable #2 it would need an ADR and a methodology version anyway. This analysis does not
justify one.

Three things that would help, in order of value:

1. **Fix the rubric usage, not the maths** (2.06x, largest effect). Basic and Frontier are each used
   3.7% of the time. Either the anchors make the ends unreachable or assessors avoid them — both
   answerable by reading the anchors and running a calibration exercise. **Founder-scoped.**
2. **Revisit the B metric interpolation ceiling.** A third of V's weight saturates above roughly
   £40bn AUA-equivalent. Either the upper anchors are too low for the firms we assess, or B should
   carry less weight. Both are methodology questions. **Founder-scoped.**
3. **Report dispersion beside the score.** A V of 0.57 built from modules spanning 0.20–0.80 is a
   different firm from a V of 0.57 built from modules all at 0.55, and today both display
   identically. The engine already computes every q_m. **Buildable now — spun out as GRS-0227.**

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
