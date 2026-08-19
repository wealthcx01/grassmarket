"""Weight sensitivity guard (GRS-0237 scope 4).

The finding recorded in `docs/analysis/weight-sensitivity-2026-08.md` is that the module ranking and
the ordering of firms by V survive ±20% perturbation of λ, δ, W_g and the strength encoding. These
tests exist so that stays true: if a future coefficient or aggregation change makes the output
depend on the un-elicited weights, it fails here rather than being discovered by a reviewer holding
the white paper.

Like `test_score_dispersion.py`, these **measure a property; they do not pin exact values**. A tight
assertion on a scoring output is a golden master and there already is one. The bounds are set well
inside what was measured.
"""

from __future__ import annotations

import os
import random

import pytest

from grassmarket.atlas.active import profile_key_of, profile_scoring_context
from grassmarket.demo.brokerage_showcase import SHOWCASE
from tools.weight_sensitivity import (
    DRAWS,
    FAMILIES,
    SEED,
    kendall_tau,
    perturbed,
    spec_document,
    sweep,
)


@pytest.fixture(scope="module")
def results() -> dict:
    return sweep()


def test_the_module_ranking_survives_perturbing_the_loadings(results: dict) -> None:
    """λ is the only family in the module-score path, so it is the only one that can break rank."""
    stats = results["families"]["lambda_loadings"]
    assert stats["in_module_score_path"], (
        "λ no longer reaches any module score. Either the aggregation changed or the showcase "
        "firms are now uniform inside every module — both invalidate the analysis document."
    )
    assert stats["worst_module_rank_tau"] == 1.0, (
        f"a ±20% λ perturbation now reorders modules (τ={stats['worst_module_rank_tau']}). The "
        f"ranking an advisor acts on has become an artefact of the loadings."
    )


def test_the_firms_never_change_places(results: dict) -> None:
    """The property the product relies on when it says one firm scores below another."""
    for family, stats in results["families"].items():
        assert stats["firm_order_changes"] == 0, (
            f"perturbing {family} by ±20% reordered the showcase firms in "
            f"{stats['firm_order_changes']}/{DRAWS} draws"
        )


def test_v_stays_within_a_couple_of_points(results: dict) -> None:
    """Bound set at 4.0 — twice the 1.99 measured, so this catches a regime change, not noise."""
    for family, stats in results["families"].items():
        assert stats["worst_v_displacement_points"] <= 4.0, (
            f"perturbing {family} by ±20% moved V by "
            f"{stats['worst_v_displacement_points']:.2f} points"
        )


@pytest.mark.parametrize("family", [f for f in FAMILIES if f != "lambda_loadings"])
def test_the_downstream_families_still_do_not_touch_module_scores(
    family: str, results: dict
) -> None:
    """The correction the analysis had to make to itself, pinned.

    δ, W_g and the strength encoding are downstream of q_m, so their rank stability is a tautology
    rather than a measurement. If one of them ever DOES reach a module score, the analysis
    document's `n/a` becomes a lie and this fails to say so.
    """
    assert not results["families"][family]["in_module_score_path"], (
        f"{family} now moves module scores. docs/analysis/weight-sensitivity-2026-08.md reports "
        f"its rank stability as 'n/a' on the grounds that it cannot — that claim is now false."
    )


def test_the_sweep_is_deterministic_within_a_process() -> None:
    """Necessary but nowhere near sufficient — see the test below for why."""
    assert sweep() == sweep()


def test_the_sweep_is_deterministic_ACROSS_processes() -> None:
    """The test that actually matters, and the one whose absence hid a real defect.

    The first version of this file asserted only ``sweep() == sweep()``. That passes trivially:
    both calls seed a fresh ``random.Random(SEED)`` in the same interpreter. It proved the one
    thing never in doubt.

    Meanwhile the sweep was NOT reproducible across runs. Some weight families are built from set
    comprehensions upstream, Python randomises string hashing per process, and the RNG is consumed
    in dict-iteration order — so the same seed assigned different draws to different weights on
    every run. Three consecutive runs reported a worst δ displacement of 0.55, 0.53 and 0.47
    points, and the committed analysis table was therefore not reproducible.

    ``perturbed()`` now sorts keys before drawing. This runs the sweep in two subprocesses under
    DIFFERENT hash seeds, which is the only way to catch a regression of that class from inside
    pytest — the parent process has one fixed seed for its whole life.
    """
    import json
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    outputs = []
    for hash_seed in ("0", "1"):
        proc = subprocess.run(
            [sys.executable, "-m", "tools.weight_sensitivity", "--json"],
            cwd=root,
            capture_output=True,
            text=True,
            env={"PYTHONHASHSEED": hash_seed, "PATH": os.environ.get("PATH", "")},
            check=True,
        )
        outputs.append(json.loads(proc.stdout))

    assert outputs[0] == outputs[1], (
        "the sweep gives different answers under different PYTHONHASHSEED values, so the numbers "
        "committed in docs/analysis/weight-sensitivity-2026-08.md do not reproduce and are not "
        "evidence. Something iterates a hash-ordered collection before consuming the RNG."
    )


def test_a_large_enough_perturbation_does_break_the_ranking() -> None:
    """The negative control.

    Without this, every assertion above is also satisfied by a sweep that silently perturbs
    nothing — the stability would be an artefact of a broken harness rather than a property of the
    engine. λ at ±110% is where the analysis document measured the first break.
    """
    import tools.weight_sensitivity as ws

    original = ws.PERTURBATION
    ws.PERTURBATION = 1.5
    try:
        rng = random.Random(SEED)
        broke = False
        for _ in range(DRAWS):
            for spec in SHOWCASE:
                _, coefficients = profile_scoring_context(profile_key_of(spec_document(spec)))
                _, modules, _ = ws._score(spec, perturbed(coefficients, "lambda_loadings", rng))
                if kendall_tau(modules, ws._score(spec)[1]) < 1.0:
                    broke = True
                    break
            if broke:
                break
        assert broke, (
            "even a ±150% λ perturbation leaves the ranking untouched, which means the harness is "
            "not perturbing anything and the stability result above is meaningless"
        )
    finally:
        ws.PERTURBATION = original
