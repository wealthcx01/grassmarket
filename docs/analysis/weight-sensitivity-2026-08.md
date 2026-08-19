# Weight sensitivity: how much of the answer is the weights?

**GRS-0237 scope 4.** Measured 2026-08-19 against the engine at `ee8270f`, Methodology v1.6.
Reproduce with `uv run python -m tools.weight_sensitivity`; guarded by
`tests/test_weight_sensitivity.py`.

## The question

Every coefficient in ATLAS is an expert judgement, and as of today most of them are *starter*
judgements (see the limitations register in the white paper). A reviewer's fair challenge follows
immediately: **if the weights are not yet elicited, how much of the output is the weights rather
than the firm?**

The existing θ/α variant grid answers this for the two headline blend parameters. It leaves four
families untested: λ (subcomponent loadings), δ (module weights), W_g (metric group weights), and
the ordinal strength encoding. This sweep covers those four.

## Method

Each family is perturbed **one at a time** — a reviewer's question is attributable, and moving
everything at once cannot say which weights matter. Each weight moves by up to **±20%** of itself,
drawn from a seeded RNG (`seed=20260819`), **40 draws per family**, across all three showcase firms.

Two constraints on the perturbation, both deliberate:

- **Weights never reach zero.** A zero weight does not perturb a term, it deletes one; that is
  structural sensitivity, a different question, and folding it in here would report a model change
  as a weighting effect.
- **The strength encoding is re-sorted after jittering.** It is ordinal (None < Emerging <
  Established < Wide, ADR-0004). Jittering the four levels independently can invert two of them,
  which is not a perturbed weighting — it is a different rating scale.

The reported statistic is the **worst run observed**, not a mean. A reviewer cares whether the
ordering *can* break, not how often it does.

## Result

| Family | In the module-score path? | Worst module-rank τ | Worst ΔV | Firm-order changes |
|---|---|---|---|---|
| λ subcomponent loadings | yes | **1.000** | 0.11 pts | 0 / 40 |
| δ module weights | no | n/a | 0.64 pts | 0 / 40 |
| W_g metric group weights | no | n/a | 0.97 pts | 0 / 40 |
| strength encoding | no | n/a | **1.99 pts** | 0 / 40 |

**The ordering of the three firms by V did not change in any of the 160 runs.** The largest V
displacement anywhere was 1.99 points of 100, from the power-strength encoding.

## Two corrections this analysis had to make to itself

Both were caught by checking a result that looked too good, and both are recorded because a reader
deciding how much to trust this table should know how it was arrived at.

### 1 — The numbers did not reproduce

The first committed table was **not reproducible**. Three consecutive runs of the same seeded sweep
reported a worst δ displacement of **0.55, 0.53 and 0.47** points.

The cause: several weight families are built from set comprehensions upstream, Python randomises
string hashing per process, and the sweep consumed the RNG in dict-iteration order — so the same
seed assigned different draws to different weights on every run. `perturbed()` now sorts keys before
drawing, and the output is identical under any `PYTHONHASHSEED`.

The guard that should have caught this asserted `sweep() == sweep()`, which passes trivially: both
calls seed a fresh generator in the same interpreter. It proved the only thing never in doubt.
`test_the_sweep_is_deterministic_ACROSS_processes` now runs the sweep in two subprocesses under
different hash seeds, which is the only way to catch this class of defect from inside pytest.

**A committed number that does not reproduce is not evidence**, and this document would have been
citing four of them.

### 2 — τ = 1.000 was three-quarters tautology

The first version of this sweep reported **τ = 1.000 for all four families** and read as a strong
robustness result. It was not one.

Checking rather than accepting it: δ, W_g and the strength encoding move **zero** module scores.
They cannot — δ weights modules *into* L, W_g weights metric groups into B, and the encoding maps
power ratings into P, all of them **downstream** of q_m. Their τ is 1.0 by construction.

Publishing that as evidence would have been reporting the model's own structure as a measurement,
which is precisely the failure this document exists to guard against. The table above says `n/a`
where there is nothing to measure. Only λ is testable for rank stability, and only λ carries a τ.

## How far λ has to move before the ranking breaks

"We tried ±20% and nothing happened" is a weak claim. Walking the perturbation upward until the
ordering actually breaks turns it into a bounded one:

> **The module ranking is stable until λ is perturbed by ±110%.**

More than doubling a subcomponent loading, in either direction, is required before any showcase
firm's nine modules reorder at all. The ranking an advisor acts on — which module is the
constraint — is not an artefact of the loadings.

## Why λ moves so little

Two structural reasons, both worth stating because they bound the result rather than inflate it:

1. **λ is normalised within a module.** Reweighting a convex combination of *identical* values
   returns the same value, so a module whose subcomponents were all rated the same is completely
   insensitive to λ. In the 2026-08-19 run, a ±20% λ perturbation moved a module score in only
   **2 of 9** modules on Revolut; the other seven are uniform inside themselves.
2. **q_m is part min().** The bottleneck term is a `min` over subcomponents, and a min is
   unaffected by weights entirely. Whatever share α gives the bottleneck is λ-immune by
   construction.

So λ's low sensitivity is partly a real property and partly a consequence of the rubric being used
narrowly — the same finding `score-dispersion-2026-07.md` reached from the other direction. **If
raters begin using the full rubric width, λ sensitivity will rise**, and this sweep should be re-run
at that point. It is not a permanent result.

## What this does and does not license

**It licenses:** saying that the module ranking and the relative ordering of firms do not depend on
the un-elicited weights, within any plausible elicitation outcome.

**It does not license:** saying the *level* of V is robust. A 1.99-point displacement from the
strength encoding alone is small but not nothing, and this sweep says nothing about whether V's
absolute level is *correct* — only that it is stable under reweighting. Correctness is an outcome
question, and the outcome register (Guide §1.2, Stage 3) has no data in it yet.

**It also does not test:** θ and α (covered by the existing variant grid), the critical-control cap
κ, or the C-index families. The cap is a documented discontinuity by design (ADR-0038) and would
need its own analysis.
