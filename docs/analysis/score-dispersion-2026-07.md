# Score dispersion: why the scores look similar

**GRS-0223.** Measured 2026-07-30 against the engine at `0d775c7`, coefficient set `retail`,
Methodology v1.2. Reproduce with `tests/test_score_dispersion.py`.

## The question

> "Also all the scores seem surprisingly similar so far..?" — founder, 2026-07-23, restated 26-07

The suspicion is correct and it deserved measuring rather than reassuring. The three showcase
brokerages score:

| Firm | V | B | P | L |
|---|---|---|---|---|
| Revolut | 0.605 | 0.900 | 0.386 | 0.548 |
| Hargreaves Lansdown | 0.572 | 0.983 | 0.314 | 0.457 |
| WeBull | 0.547 | 0.767 | 0.286 | 0.579 |
| **spread** | **0.058** | 0.216 | 0.100 | 0.122 |

V spans 5.8 points of 100 across three genuinely different businesses — a neobank, a traditional
platform and a discount broker. Every component spreads more widely than the number built from them.

## The answer, in one line

**The engine is not compressing anything. Aggregation is.** V averages 9 infrastructure modules,
7 powers and 4 business metrics; a firm that is strong in some places and weak in others is pulled
to the middle by construction, and every real firm is a mixed bag.

## What was measured

### 1. The engine's achievable range is wide

Synthetic documents at the corners of the input space:

| Input | V | B | P | L |
|---|---|---|---|---|
| everything Basic, powers None, metrics ×0.01 | **0.185** | 0.349 | 0.000 | 0.200 |
| everything Frontier, powers Wide, metrics ×5 | **1.000** | 1.000 | 1.000 | 1.000 |

**Achievable span: 0.815 of the nominal [0,1].** Feed the engine extremes and it produces extremes.
Across all 16 corners of the (level × strength) grid at fixed metrics, V spans 0.350–0.970.

So compression is not in the maths. That rules out the first two hypotheses the ticket listed —
the bottleneck term and over-even weights — as the *cause*. Neither prevents an extreme firm from
scoring at an extreme.

### 2. The dominant mechanism is aggregation, and it is measurable

The clean experiment: sample synthetic firms while varying only **how internally consistent a firm
is**, with the engine and coefficients untouched. `rho` is the probability that a given module takes
the firm's own "character" level rather than an independent draw.

| rho | meaning | sd(V) | range(V) |
|---|---|---|---|
| 0.00 | every module rated independently | 0.057 | 0.316 |
| 0.50 | half the modules follow the firm's character | 0.092 | 0.431 |
| 0.75 | | 0.123 | 0.574 |
| 1.00 | every module identical | **0.153** | **0.620** |

**sd(V) rises 2.7× purely from correlation structure.** Nothing about the engine changed between
those rows. A firm only scores at an extreme if it is *consistently* extreme across twenty-odd
ratings, and real firms are not: Revolut has the strongest powers and mid infrastructure, HL the
strongest business metrics and the weakest infrastructure limb.

This is the law of large numbers doing what it does. It is not a defect, and it is not fixable by
re-weighting — averaging more things always concentrates the average.

A hypothesis worth killing explicitly: the three real firms *look* like their components cancel
(HL is highest on B and lowest on L). Under random sampling the components are effectively
independent — sd(V) actual / sd(V) if independent = **1.002**. The apparent cancellation in a
sample of three is noise, not structure.

### 3. Two amplifiers make it worse than it needs to be

**Amplifier A — the rubric is used narrowly.** Across the three showcase specs, module base levels
are:

| Level | score_index | share |
|---|---|---|
| Basic | 0.2 | 3.7% |
| Developing | 0.5 | 51.9% |
| Advanced | 0.8 | 40.7% |
| Frontier | 1.0 | 3.7% |

**92.6% of ratings fall in the middle two levels**, whose score indices span 0.5–0.8: a 0.3-wide
band inside a nominal 0.8-wide scale. Holding everything else equal, drawing ratings from all four
levels instead of the middle two widens sd(V) by **2.06×** (0.0215 → 0.0444).

This is the ticket's fourth hypothesis — assessors clustering on the middle of the rubric — and it
is the largest *addressable* effect found. It is a rubric and calibration problem, not a maths one.

**Amplifier B — B saturates.** The business index reaches 1.000 at roughly twice Revolut's metrics
and stays there:

| metrics | ×0.5 | ×0.75 | ×1.0 | ×1.5 | ×2.0 | ×10 |
|---|---|---|---|---|---|---|
| B | 0.743 | 0.828 | 0.900 | 0.950 | 1.000 | 1.000 |

All three real firms sit at 0.767–0.983, in the top quartile. B carries θ_B = 0.3 of V and moves
very little among firms of real size, so nearly a third of V's weight is doing little
discriminating work. Widening the metric range 100× (×0.05 to ×5) moved sd(V) only from 0.0614 to
0.0631.

**A structural note, not an amplifier.** `MaturityLevel.score_index` floors at **0.2**, so no q_m
and therefore no L can fall below 0.2. The bottom fifth of the nominal range is unreachable for the
whole L limb by construction. That is a deliberate scale choice rather than a bug, but it should be
stated in the explainer: a "0.2" is the floor of the scale, not a fifth of the way up it.

## What this means

The founder's instinct was right and the diagnosis is not the obvious one. The scores are similar
because **the firms are similar once you average twenty ratings**, and because we are using about a
third of the rubric.

Selling an assessment whose headline number moves 6 points between a neobank and a traditional
platform is hard, and the honest fix is not to stretch the number.

## Recommendation

**No engine change, and no recalibration.** Nothing measured here shows the maths misbehaving, and
changing coefficients to widen an output distribution would be fitting the scale to the marketing
rather than to the method. Per non-negotiable #2 that would need an ADR and a methodology version
anyway; this analysis does not justify one.

Three things that would help, in order of value:

1. **Fix the rubric usage, not the maths (largest effect, 2.06×).** Basic and Frontier are being
   used 3.7% of the time each. Either the anchors make them unreachable in practice, or assessors
   avoid the ends. This is answerable by reading the anchors and by a calibration exercise, and it
   is where the discrimination actually is. Feeds the C-rubric authoring work.
2. **Revisit the B metric interpolation ceiling.** A third of V's weight saturates above roughly
   £40bn AUA-equivalent. Either the upper anchors are set too low for the firms we assess, or B
   should carry less weight. Both are methodology questions.
3. **Report dispersion beside the score.** A V of 0.57 built from modules spanning 0.20–0.80 is a
   *different firm* from a V of 0.57 built from modules all at 0.55, and today both display
   identically. Surfacing the spread of q_m — which the engine already computes — would make a
   mid-range score read as "mixed, with a specific weak spot" instead of "average". This costs
   nothing methodologically and is the fastest way to make the report feel discriminating.

The first two are founder-scoped. The third is a reporting change and could be built now.

## Guard

`tests/test_score_dispersion.py` pins the finding: deliberately different firms must keep producing
a wide V span, so if compression ever does creep into the maths it fails there rather than being
re-discovered by a founder looking at a report.
