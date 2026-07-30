"""Deterministic module scores on the live payload (GRS-0227).

The dispersion figure the summary renders is only as honest as the field it reads. This file guards
that field: it carries the DETERMINISTIC q_m (ADR-0040, not a Monte Carlo median), it carries a
value for every module that scored, and it carries nothing at all for a module that did not (D9).

The rendering itself is tested in `frontend/lib/dispersion.test.ts` and
`frontend/components/LiveScorePanel.dispersion.test.tsx`.
"""

from __future__ import annotations

import dataclasses
import random

import pytest
from bcap_contracts.common import MaturityLevel

from grassmarket.assessments.service import deterministic_result, live_score
from grassmarket.atlas.active import (
    active_uncertainty_model,
    profile_key_of,
    profile_scoring_context,
)
from grassmarket.demo.brokerage_showcase import REVOLUT, SHOWCASE, showcase_document


def _live(spec) -> tuple:
    document = showcase_document(spec)
    registry, coefficients = profile_scoring_context(profile_key_of(document))
    score = live_score(
        document,
        coefficients,
        registry,
        active_uncertainty_model(profile_key_of(document)),
        random.Random(1),
    )
    return score, document, registry, coefficients


def test_the_points_are_the_deterministic_scores_not_the_bands() -> None:
    """ADR-0040: the quoted number is the engine point. The MC median sits systematically below it,
    and headlining a median is the bug that made the score jump at finalisation (GRS-0167). A
    dispersion range built from medians would inherit exactly that."""
    score, document, registry, coefficients = _live(REVOLUT)
    assert score.scoreable

    expected = {
        module.key: module.q_m
        for module in deterministic_result(document, coefficients, registry).modules
        if module.q_m is not None
    }
    assert expected, "no module scored, so this test proves nothing"
    assert score.module_qm_point == pytest.approx(expected)

    # Worth being precise about WHY this field exists, because the obvious reason is not the real
    # one. For a fully rated module the MC median lands exactly on the deterministic point — there
    # is no rating uncertainty to draw over — so reading medians would not, here, drift the module
    # numbers. The drift is at the composite, where aggregation pulls the median below the point:
    assert score.v_point is not None and score.v is not None
    assert score.v.p50 < score.v_point, (
        "the MC median no longer sits below the deterministic V; ADR-0040's premise has changed"
    )
    # ...and the reason the dispersion range must read points rather than bands is COVERAGE, not
    # drift: an unassessed module carries a modelled band and no point. That is asserted next.


def test_an_unassessed_module_contributes_nothing() -> None:
    """D9: Not Assessed is not a score. A module with no rating must be ABSENT from the mapping —
    not zero, not a neutral default — because a zero would drag the reported range down to the floor
    and invent a weak spot nobody measured."""
    stripped = dataclasses.replace(
        REVOLUT,
        subject="revolut-one-module-unassessed",
        v_base=tuple(
            (key, level) for key, level in REVOLUT.v_base if not key.startswith("CUSTODY")
        ),
    )
    score, document, registry, coefficients = _live(stripped)
    if not score.scoreable:
        pytest.skip("dropping the module made the assessment unscoreable; nothing to assert")

    result = deterministic_result(document, coefficients, registry)
    unscored = {module.key for module in result.modules if module.q_m is None}
    for key in unscored:
        assert key not in score.module_qm_point, (
            f"{key} has no q_m but appears in module_qm_point; an unassessed module would be read "
            f"as a real low score by the dispersion range"
        )
    assert set(score.module_qm_point) == {
        module.key for module in result.modules if module.q_m is not None
    }


def test_every_showcase_firm_reports_a_spread_far_wider_than_the_scores_differ() -> None:
    """The finding GRS-0227 exists to surface, asserted on the real demo data.

    The three showcase firms span 0.058 of V — near-identical headlines. Their MODULES span roughly
    half the scale. That gap between the two numbers is the whole argument for the feature, so if it
    ever closes, this fails and the feature's premise gets re-examined rather than quietly outliving
    its evidence."""
    v_values = []
    spreads = []
    for spec in SHOWCASE:
        score, *_ = _live(spec)
        assert score.scoreable
        points = list(score.module_qm_point.values())
        assert len(points) > 1
        v_values.append(score.v_point)
        spreads.append(max(points) - min(points))

    v_span = max(v_values) - min(v_values)
    assert v_span < 0.10, f"the showcase firms now differ by {v_span:.3f} of V"
    for spread in spreads:
        assert spread > v_span * 3, (
            f"a showcase firm's modules span only {spread:.3f} while the firms' scores span "
            f"{v_span:.3f}; the headline is no longer hiding the unevenness GRS-0227 surfaces"
        )
    # And at least one firm is on the rubric floor while its headline reads mid-range — the single
    # sharpest example of the problem.
    assert min(min(_live(spec)[0].module_qm_point.values()) for spec in SHOWCASE) == pytest.approx(
        MaturityLevel.BASIC.score_index
    )


def test_a_uniformly_rated_firm_reports_no_spread() -> None:
    """The other end: a genuinely even firm must report a spread of zero rather than an artefact."""
    uniform = dataclasses.replace(
        REVOLUT,
        subject="synthetic-uniform",
        v_base=tuple((key, MaturityLevel.DEVELOPING.value) for key, _ in REVOLUT.v_base),
        v_over=(),
        c_base=tuple((key, MaturityLevel.DEVELOPING.value) for key, _ in REVOLUT.c_base),
    )
    score, *_ = _live(uniform)
    assert score.scoreable
    points = list(score.module_qm_point.values())
    assert points
    assert max(points) - min(points) == pytest.approx(0.0, abs=1e-9)
