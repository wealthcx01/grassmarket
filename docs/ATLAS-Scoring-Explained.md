# How ATLAS scoring works

This document explains, in plain English, how ATLAS turns an assessment into its scores: Platform
Value (V), the Customer Proposition (C), and the three lenses underneath them. Read this instead of
the Methodology if you want to understand the scoring. Read the Methodology
(`docs/ATLAS-Methodology-v1.2.md`) only if you intend to change the scoring, because a scoring change
is an architecture decision record and a new Methodology version, never an edit to this file.

Where this document needs the strategic framing behind the Powers, it points to
`docs/ATLAS-7Powers-Adaptation.md` (the adaptation of Hamilton Helmer's mathematics) rather than
repeating it, so the two documents cannot drift apart.

## 1. The three lenses and the composite

ATLAS scores a platform through three lenses, each on a 0 to 100 scale:

- **Business (B)** — the commercial engine, read from business metrics such as assets, clients, and
  revenue.
- **Powers (P)** — durable competitive advantage, rated across the seven strategic powers.
- **Infrastructure (L)** — the technology and operations layer, rated across the infrastructure
  modules. (The letter L stands for the technology layer.)

Platform Value is a weighted average of the three:

```
V = θ_B · B  +  θ_P · P  +  θ_L · L
```

The three weights `θ_B`, `θ_P`, `θ_L` add up to 1. They are not the same for every kind of firm,
because what drives value differs by segment. The live weights, taken directly from the scoring
code, are:

| Operating model | θ_B (Business) | θ_P (Powers) | θ_L (Infrastructure) | Source |
|---|---|---|---|---|
| Retail brokerage (draft) | 0.30 | 0.30 | 0.40 | `src/grassmarket/atlas/draft_coefficients.py`, `theta` default |
| Wealth advisory (elicited starter) | 0.45 | 0.30 | 0.25 | `src/grassmarket/atlas/elicited_coefficients.py`, `elicited_wealth_coefficient_set` |
| Exchange / infrastructure (elicited starter) | 0.30 | 0.37 | 0.33 | `elicited_coefficients.py`, `elicited_exchange_coefficient_set` |

The reasoning is recorded alongside each set in the code. For **wealth**, franchise economics lead,
so Business carries the most weight; Infrastructure is trimmed because it is largely hygiene whose
cost is already priced into the Business result. For **exchange**, the moat (Powers) is the top term,
and Business rises because traded volume is roughly half of revenue. The **retail** weights are a
uniform draft, pending elicitation.

A note on status: the retail set is a draft, and the wealth and exchange sets are research-refined
starters. A change to any of these weights is governed by an architecture decision record, not an
edit here.

**The Customer Proposition (C) is reported alongside V, not folded into it.** C is scored on its own
0 to 100 scale from the customer-experience widgets and their ease, usability, and depth ratings. A
future direction (recorded in the code as a draft only, marked not client-usable) would split the
weights into four and give C its own weight `θ_C` of 0.15, with the other three re-split to 0.25 /
0.25 / 0.35. That four-index weighting is **not live**. Today C sits next to V and never inside it.

## 2. How a lens score is built: module maturity

The Powers and Infrastructure lenses are built from module scores. Each module gets a maturity
index, written `q_m`, on the same 0 to 100 scale. A module is made of subcomponents, each rated on a
four-rung maturity scale whose index values are Basic 20, Developing 50, Advanced 80, and Frontier
100.

A module score is **not** a simple average of its subcomponents. A module cannot outrun its weakest
critical subcomponent. Each module has one or more subcomponents marked critical (shown with a star
in the wizard), and if a critical subcomponent is weak, it holds the whole module down. This is the
bottleneck rule: fixing a strong part while a critical part is weak does not move the module.

**A worked example.** Suppose a module has three subcomponents, two rated Advanced (80) and one
critical subcomponent rated Developing (50). A plain average would read about 70. The module score is
pulled toward the weak critical part instead, so it lands below that average, closer to the 50 the
bottleneck sets. The exact blend combines a weighted average of the parts with the minimum of the
critical parts.

The Infrastructure lens then combines its module scores the same way, so a weak critical module drags
the whole lens down by design:

```
L = α · (Σ weight · q_m)  +  (1 − α) · (minimum q_m over the critical modules)
```

The first term is the weighted average of the modules; the second is the weakest critical module. The
factor `α` sets how much weight goes to the average versus the bottleneck. This is the same formula
the live-score panel discloses in the wizard, so the document and the screen agree. In the retail
draft set the module weights are uniform: with nine modules, each module's weight is one ninth, about
11.1%, so no single module can pull the average far on its own.

**Words communicate, numbers prioritise.** Each module also carries a band in words (Basic to
Frontier). The band is what you defend out loud to a client. The continuous score underneath, which
is more precise, is what decides which weakness to fix first.

## 3. Uncertainty, and what P10, P50, and P90 mean

ATLAS does not just produce a single score; it produces an honest range around it. It does this with
a Monte Carlo simulation, which works like this: every input carries an evidence grade that says how
well supported it is, the simulation re-samples each input within the confidence its grade allows,
and it re-scores the whole platform many times. The result is a distribution of possible scores
rather than one number.

From that distribution, three points are reported:

- **P50** is the median outcome, the middle of the distribution.
- **P10** and **P90** are the tenth and ninetieth percentiles: the honest range within which the
  score is likely to fall.

A wider P10 to P90 range means the evidence is thinner or weaker-graded, so the assessment is less
certain. A narrow range means strong, well-graded evidence.

```
        P10            P50            P90
         |--------------[X]-------------|
   less certain      median       less certain
      (weaker           |          (stronger
       evidence)   likely range     evidence)
```

**The one quoted number is always the same number.** The headline always quotes the deterministic
score, the single point the engine computes directly. The prose around it quotes the range from the
simulation. The two never disagree, because the headline is the point and the range is context around
that same point. And when an input has no evidence grade, the score cannot be modelled for
uncertainty, so it is shown as an honest labelled point rather than a falsely tight range.

## 4. Why do the demo scores look so similar?

The founder asked this directly, and the honest answer is that it is an artefact of draft weights and
demo data, not a property of the mathematics.

- **The maturity rungs quantise the scores.** Subcomponents can only be Basic, Developing, Advanced,
  or Frontier, whose index values are 20, 50, 80, and 100. Nearby inputs collapse onto the same rung,
  so module scores land near a few plateaus rather than spreading smoothly.
- **The retail draft weights are uniform.** Every module carries the same one-ninth weight, so no
  module can pull the average far from the middle.
- **Business saturates.** Business is built from only a few metrics, so it tends to sit high and flat
  across different subjects rather than spreading them out.
- **The demo subjects were seeded deliberately similar.** Revolut, Hargreaves Lansdown, and WeBull
  were built as comparable showcase firms, so their scores are close by design.

What will spread scores in real use: the elicited, non-uniform segment weights (which let some
modules and lenses matter more than others), more metrics feeding Business, and the real dispersion
of genuinely different businesses. The clustering is a feature of the draft configuration and the
demo set, and it opens up as the weights and the data become real.

## 5. How Hamilton Helmer would treat these

The full treatment is in `docs/ATLAS-7Powers-Adaptation.md`, authored under Helmer's permission
grant; this section summarises only what is needed here.

In 7 Powers terms, Business and Infrastructure are **operational excellence**. They are necessary to
run the business, but on their own they are not a durable advantage, because a competitor can match
good operations over time. **Powers** is the Helmer-native lens, because Helmer defines a Power as
requiring **both** a Benefit (something that materially improves cash flow) **and** a Barrier
(something that stops competitors arbitraging that benefit away). ATLAS rates each power as
`strength = min(Benefit, Barrier)`, which is exactly that dual test: a strong benefit with no barrier
is competed away, and a barrier around no benefit protects nothing. This is the same minimum the
wizard applies to every power.

So why does an advisory product still score the whole platform, and not only its moat? Because the
client is buying an operating assessment, not only a verdict on durable advantage. Business,
Infrastructure, and the Customer Proposition all matter to whether the platform is sound, even though,
in Helmer's strict sense, only Powers is durable advantage. For the per-power treatment (Scale
Economies, Network Economies, Counter-Positioning, Switching Costs, Branding, Cornered Resource, and
Process Power) and the full mapping of Business, Infrastructure, Powers, and Customer to Helmer's
framework, see the adaptation document.
