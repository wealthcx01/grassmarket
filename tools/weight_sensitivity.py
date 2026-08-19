"""Weight sensitivity: does the ranking survive perturbing the coefficients? (GRS-0237 scope 4)

The question a due-diligence reviewer asks that the existing θ/α variant grid does not answer:
**the weights are expert judgements, so how much does the answer depend on them?** An instrument
whose module ordering reshuffles under a 20% weight nudge is reporting the weights, not the firm.

This sweeps four families the θ/α grid leaves fixed — λ (subcomponent loadings), δ (module weights),
W_g (metric group weights) and the ordinal strength encoding — and reports, across the three
showcase firms:

- **rank stability** of the nine infrastructure modules (Kendall's τ against the unperturbed run),
- **V displacement** in score points,
- whether the **ordering of the three firms by V** ever changes, which is the property the product
  actually relies on when it says one firm scores below another.

Deterministic and offline: perturbations come from a seeded `random.Random`, so re-running
reproduces the committed table exactly. No network, no model calls, no wall-clock.

    uv run python -m tools.weight_sensitivity            # print the table
    uv run python -m tools.weight_sensitivity --json     # machine-readable, for the guard test

The finding is written up in `docs/analysis/weight-sensitivity-2026-08.md`, and
`tests/test_weight_sensitivity.py` fails if the stability properties stop holding.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import random
from collections.abc import Iterator, Sequence
from typing import Any

from bcap_contracts.assessments import CoefficientSet

from grassmarket.assessments.service import deterministic_result
from grassmarket.atlas.active import profile_key_of, profile_scoring_context
from grassmarket.demo.brokerage_showcase import SHOWCASE, BrokerageSpec

#: Fixed so the committed numbers reproduce. Changing it invalidates the analysis document.
SEED = 20260819

#: How far each weight may move, as a fraction of itself. 0.20 is deliberately larger than any
#: plausible disagreement between two competent panellists — if the ranking survives this, it
#: survives the elicitation actually landing somewhere other than the starter values.
PERTURBATION = 0.20

#: Draws per family. Enough for a stable worst case without pretending this is a distribution:
#: the reported statistic is the WORST run observed, not a mean, because a reviewer cares about
#: whether the ordering can break, not about how often it does.
DRAWS = 40

FAMILIES = ("lambda_loadings", "delta", "group_weights", "strength_encoding")


def _jitter(rng: random.Random, value: float) -> float:
    """Move a weight by up to ±PERTURBATION of itself, never through zero.

    Clamped at a small positive floor rather than allowed to reach 0: a zero weight does not
    perturb a weight, it *deletes a term*, which is a different question (structural sensitivity)
    and would make the sweep report a model change as a weighting effect.
    """
    factor = 1.0 + rng.uniform(-PERTURBATION, PERTURBATION)
    return max(value * factor, 1e-6)


def perturbed(base: CoefficientSet, family: str, rng: random.Random) -> CoefficientSet:
    """`base` with one weight family jittered. Every other family is untouched.

    One family at a time, because a reviewer's question is attributable — "which weights matter?"
    cannot be answered by moving all of them at once.
    """
    current = getattr(base, family)
    # SORTED, always. The RNG is consumed in iteration order, so if that order varies the same seed
    # produces different perturbations. Some weight families are built from set comprehensions
    # upstream, and Python randomises string hashing per process (PYTHONHASHSEED) — so dict
    # insertion order, and therefore this sweep's output, varied from run to run. It was measured
    # doing exactly that: three consecutive runs reported a worst δ displacement of 0.55, 0.53 and
    # 0.47 points. Sorting the keys makes the draw assignment depend only on the seed.
    if family == "lambda_loadings":
        updated: Any = {
            module: {key: _jitter(rng, loadings[key]) for key in sorted(loadings)}
            for module in sorted(current)
            for loadings in (current[module],)
        }
    elif family == "strength_encoding":
        # The encoding is ORDINAL: None < Emerging < Established < Wide. Jittering each level
        # independently could invert two of them, which is not a weighting perturbation — it is a
        # different rating scale. Perturb, then re-sort onto the original level order so the
        # ordering constraint (ADR-0004) survives.
        levels = sorted(current, key=lambda k: current[k])
        values = sorted(_jitter(rng, current[level]) for level in levels)
        updated = dict(zip(levels, values, strict=True))
    else:
        updated = {key: _jitter(rng, current[key]) for key in sorted(current)}
    return (
        dataclasses.replace(base, **{family: updated})
        if dataclasses.is_dataclass(base)
        else (base.model_copy(update={family: updated}))
    )


def _score(
    spec: BrokerageSpec, coefficients: CoefficientSet | None = None
) -> tuple[float, list[str], dict[str, float]]:
    """(V, module keys ordered weakest-first) for one firm.

    The module ordering is the thing the report actually acts on — the constraint section names the
    weakest modules — so it is the ranking whose stability matters, not the raw q_m values.
    """
    document = spec_document(spec)
    registry, default_coefficients = profile_scoring_context(profile_key_of(document))
    result = deterministic_result(document, coefficients or default_coefficients, registry)
    # `q_m is None` means the module had nothing assessed. It is EXCLUDED rather than sorted as
    # zero: a Not Assessed module contributes to no score (D9), so ranking it as the weakest would
    # invent a finding the engine deliberately refuses to make.
    scored = [m for m in result.modules if m.q_m is not None]
    modules = sorted(scored, key=lambda m: (m.q_m, m.key))
    return (
        result.composite.v_index,
        [m.key for m in modules],
        {m.key: float(m.q_m) for m in scored if m.q_m is not None},
    )


def spec_document(spec: BrokerageSpec):  # noqa: ANN201 - the document type is internal to the demo
    from grassmarket.demo.brokerage_showcase import showcase_document

    return showcase_document(spec)


def kendall_tau(a: Sequence[str], b: Sequence[str]) -> float:
    """Kendall's τ-a between two orderings of the same items.

    Written out rather than pulled from scipy: the repo has no scipy dependency, the input is nine
    items, and a reviewer reading this file should be able to see exactly what was computed.
    """
    position = {key: index for index, key in enumerate(b)}
    concordant = discordant = 0
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            left = position[a[i]] - position[a[j]]
            if left < 0:
                concordant += 1
            elif left > 0:
                discordant += 1
    total = concordant + discordant
    return (concordant - discordant) / total if total else 1.0


def sweep() -> dict[str, Any]:
    """Run every family across every showcase firm and return the worst case per family."""
    rng = random.Random(SEED)
    baseline = {spec.subject: _score(spec) for spec in SHOWCASE}
    baseline_order = [
        subject for subject, _ in sorted(baseline.items(), key=lambda kv: kv[1][0], reverse=True)
    ]

    results: dict[str, Any] = {
        "seed": SEED,
        "perturbation": PERTURBATION,
        "draws": DRAWS,
        "baseline": {
            s: {"v": round(v, 6), "modules": order} for s, (v, order, _) in baseline.items()
        },
        "baseline_firm_order": baseline_order,
        "families": {},
    }

    for family in FAMILIES:
        worst_tau = 1.0
        worst_dv = 0.0
        order_breaks = 0
        modules_ever_moved = 0
        for _ in range(DRAWS):
            run_order: list[tuple[str, float]] = []
            for spec in SHOWCASE:
                _, coefficients = profile_scoring_context(profile_key_of(spec_document(spec)))
                if not getattr(coefficients, family):
                    continue  # a family this profile's set does not populate
                v, modules, q_by_key = _score(spec, perturbed(coefficients, family, rng))
                base_v, base_modules, base_q = baseline[spec.subject]
                worst_tau = min(worst_tau, kendall_tau(modules, base_modules))
                worst_dv = max(worst_dv, abs(v - base_v))
                modules_ever_moved += sum(
                    1 for key, value in q_by_key.items() if abs(value - base_q[key]) > 1e-12
                )
                run_order.append((spec.subject, v))
            ordered = [s for s, _ in sorted(run_order, key=lambda kv: kv[1], reverse=True)]
            if ordered and ordered != baseline_order:
                order_breaks += 1

        results["families"][family] = {
            # WITHOUT this count the τ figure is uninterpretable. δ, W_g and the strength encoding
            # do not enter q_m at all — they weight modules INTO L and powers into P, downstream of
            # the module score — so their τ is 1.0 by construction, not by robustness. Reporting
            # the τ alone would be publishing the model's structure as if it were a measurement.
            "module_scores_moved": modules_ever_moved,
            "in_module_score_path": modules_ever_moved > 0,
            "worst_module_rank_tau": round(worst_tau, 4),
            "worst_v_displacement_points": round(worst_dv * 100, 3),
            "firm_order_changes": order_breaks,
        }
    return results


def lambda_breaking_point(max_perturbation: float = 2.0, step: float = 0.05) -> dict[str, Any]:
    """How far λ has to move before the module ranking actually breaks.

    ±20% leaves the ordering untouched, which is the answer a reviewer wants — but "we tried one
    magnitude and nothing happened" is a weak claim. Walking the perturbation up until the ranking
    does break turns it into a bounded one: the ordering survives everything below X.
    """
    global PERTURBATION  # noqa: PLW0603 - the sweep reads it; this walks it deliberately
    original = PERTURBATION
    try:
        magnitude = step
        while magnitude <= max_perturbation:
            PERTURBATION = magnitude
            rng = random.Random(SEED)
            broke = False
            for _ in range(DRAWS):
                for spec in SHOWCASE:
                    _, coefficients = profile_scoring_context(profile_key_of(spec_document(spec)))
                    _, modules, _ = _score(spec, perturbed(coefficients, "lambda_loadings", rng))
                    if kendall_tau(modules, baseline_modules(spec)) < 1.0:
                        broke = True
                        break
                if broke:
                    break
            if broke:
                return {"first_break_at": round(magnitude, 3), "searched_to": max_perturbation}
            magnitude += step
        return {"first_break_at": None, "searched_to": max_perturbation}
    finally:
        PERTURBATION = original


def baseline_modules(spec: BrokerageSpec) -> list[str]:
    return _score(spec)[1]


def _rows(results: dict[str, Any]) -> Iterator[str]:
    yield (
        f"{'family':<20} {'in q_m?':>8} {'worst τ':>9} {'worst ΔV (pts)':>16} {'order breaks':>14}"
    )
    for family, stats in results["families"].items():
        # "n/a" rather than 1.000 when the family never reaches a module score: a number here would
        # be read as evidence, and there is no evidence to report.
        tau = f"{stats['worst_module_rank_tau']:.3f}" if stats["in_module_score_path"] else "n/a"
        yield (
            f"{family:<20} {('yes' if stats['in_module_score_path'] else 'no'):>8} {tau:>9} "
            f"{stats['worst_v_displacement_points']:>16.2f} "
            f"{stats['firm_order_changes']:>10} / {results['draws']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args()
    results = sweep()
    if args.json:
        print(json.dumps(results, indent=2))
        return
    print(f"seed={results['seed']}  ±{results['perturbation']:.0%}  draws={results['draws']}\n")
    for row in _rows(results):
        print(row)


if __name__ == "__main__":
    main()
