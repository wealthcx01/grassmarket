"""Score dispersion (GRS-0223) — the guard on the finding recorded in
`docs/analysis/score-dispersion-2026-07.md`.

The founder asked why every assessment scores about the same. The measured answer is that the
engine is not compressing anything — fed extremes it produces extremes across 0.815 of the nominal
range — and that the similarity comes from aggregation over twenty-odd ratings plus a rubric being
used at about a third of its width.

This file exists so that the first half of that answer stays true. If a future coefficient change,
weight change or scale change quietly narrows what the engine can express, these fail here rather
than being re-discovered by a founder looking at a report a quarter later.

**These tests measure; they do not pin exact values.** The bounds are deliberately loose — well
inside what was measured — because a tight assertion on a scoring output is a golden master, and
there already is one. What is asserted is the *property*: extremes remain reachable, and firms that
differ keep scoring differently.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence

import pytest
from bcap_contracts.common import MaturityLevel, StrengthRating

from grassmarket.assessments.service import deterministic_result
from grassmarket.atlas.active import profile_key_of, profile_scoring_context
from grassmarket.demo.brokerage_showcase import REVOLUT, SHOWCASE, BrokerageSpec, showcase_document

# Measured on 2026-07-30. See the analysis document for the full table.
MEASURED_ACHIEVABLE_SPAN = 0.815
MEASURED_REAL_FIRM_SPAN = 0.058


def _v(spec: BrokerageSpec) -> float:
    document = showcase_document(spec)
    registry, coefficients = profile_scoring_context(profile_key_of(document))
    return deterministic_result(document, coefficients, registry).composite.v_index


def _uniform(level: MaturityLevel, strength: StrengthRating, metric_scale: float) -> BrokerageSpec:
    """A synthetic firm rated identically everywhere — the corners of the input space."""
    return dataclasses.replace(
        REVOLUT,
        subject=f"synthetic-{level.value}-{strength.value}",
        v_base=tuple((key, level.value) for key, _ in REVOLUT.v_base),
        v_over=(),
        c_base=tuple((key, level.value) for key, _ in REVOLUT.c_base),
        powers=tuple((key, (strength.value, strength.value)) for key, _ in REVOLUT.powers),
        metrics=tuple((key, raw * metric_scale, conf) for key, raw, conf in REVOLUT.metrics),
    )


def test_the_engine_can_still_express_a_wide_range() -> None:
    """The headline finding: fed extremes, the engine produces extremes.

    This is the assertion that matters. If it ever fails, the scores really have been compressed by
    the maths and the analysis document's conclusion is out of date.
    """
    floor = _v(_uniform(MaturityLevel.BASIC, StrengthRating.NONE, 0.01))
    ceiling = _v(_uniform(MaturityLevel.FRONTIER, StrengthRating.WIDE, 5.0))

    assert ceiling > floor
    span = ceiling - floor
    assert span >= 0.75, (
        f"the engine's achievable V span has narrowed to {span:.3f}; it measured "
        f"{MEASURED_ACHIEVABLE_SPAN} on 2026-07-30. Compression has entered the maths, which is "
        f"exactly what docs/analysis/score-dispersion-2026-07.md concluded had NOT happened."
    )
    # And the ends are genuinely near the ends, not a wide band floating in the middle.
    assert floor <= 0.30, f"the floor has risen to {floor:.3f}"
    assert ceiling >= 0.90, f"the ceiling has fallen to {ceiling:.3f}"


def test_each_maturity_level_moves_the_score_monotonically() -> None:
    """Raising every subcomponent by one level must raise V, at every step of the rubric.

    A rubric level that does not move the number is a level nobody has a reason to use, and it
    would show up as compression long before anyone measured a distribution.
    """
    scores = [
        _v(_uniform(level, StrengthRating.ESTABLISHED, 1.0))
        for level in (
            MaturityLevel.BASIC,
            MaturityLevel.DEVELOPING,
            MaturityLevel.ADVANCED,
            MaturityLevel.FRONTIER,
        )
    ]
    assert scores == sorted(scores), f"V is not monotonic in maturity level: {scores}"
    for lower, higher in zip(scores, scores[1:], strict=False):
        assert higher - lower >= 0.02, (
            f"a full rubric step moves V by only {higher - lower:.4f}; the levels are not "
            f"separable and the rubric has become decorative"
        )


def test_each_power_strength_moves_the_score_monotonically() -> None:
    strengths = (
        StrengthRating.NONE,
        StrengthRating.EMERGING,
        StrengthRating.ESTABLISHED,
        StrengthRating.WIDE,
    )
    scores = [_v(_uniform(MaturityLevel.DEVELOPING, s, 1.0)) for s in strengths]
    assert scores == sorted(scores), f"V is not monotonic in power strength: {scores}"
    assert scores[-1] - scores[0] >= 0.20, (
        f"the whole power scale moves V by only {scores[-1] - scores[0]:.3f}"
    )


def test_deliberately_different_firms_score_differently() -> None:
    """The ticket's own test-plan item: a fixture set of deliberately different firms must spread.

    The margin is set at 0.30 — comfortably below the 0.62 measured across the level-and-strength
    corners at fixed metrics, and far above the 0.058 the three real showcase firms span. It is a
    guard against the engine losing its ability to separate, not a claim about real firms.
    """
    deliberately_different: Sequence[BrokerageSpec] = (
        _uniform(MaturityLevel.BASIC, StrengthRating.NONE, 1.0),
        _uniform(MaturityLevel.DEVELOPING, StrengthRating.EMERGING, 1.0),
        _uniform(MaturityLevel.ADVANCED, StrengthRating.ESTABLISHED, 1.0),
        _uniform(MaturityLevel.FRONTIER, StrengthRating.WIDE, 1.0),
    )
    scores = [_v(spec) for spec in deliberately_different]
    span = max(scores) - min(scores)
    assert span >= 0.30, f"four deliberately different firms span only {span:.3f} of V"


def test_the_real_showcase_firms_are_still_clustered() -> None:
    """The other half of the finding, asserted so it cannot drift unnoticed.

    Real firms cluster, and that is the thing the founder saw. Pinning it here means that if the
    demo data is ever changed to be more varied — or if someone quietly recalibrates to widen the
    output — this test fails and the analysis document gets revisited rather than silently
    outliving its evidence.
    """
    scores = [_v(spec) for spec in SHOWCASE]
    span = max(scores) - min(scores)
    assert span < 0.25, (
        f"the showcase firms now span {span:.3f} of V, where they spanned "
        f"{MEASURED_REAL_FIRM_SPAN} on 2026-07-30. If this is a deliberate improvement, update "
        f"docs/analysis/score-dispersion-2026-07.md — its central observation no longer holds."
    )
    # Every component spreads more than the number built from them. That IS the aggregation effect.
    documents = [showcase_document(spec) for spec in SHOWCASE]
    composites = []
    for document in documents:
        registry, coefficients = profile_scoring_context(profile_key_of(document))
        composites.append(deterministic_result(document, coefficients, registry).composite)
    for name, values in (
        ("B", [c.b_index for c in composites]),
        ("P", [c.p_index for c in composites]),
        ("L", [c.l_index for c in composites]),
    ):
        component_span = max(values) - min(values)
        assert component_span > span, (
            f"{name} spans {component_span:.3f} but V spans {span:.3f} — V is no longer more "
            f"concentrated than its own inputs, so the aggregation finding needs re-measuring"
        )


def test_the_maturity_scale_floors_at_a_fifth_not_at_zero() -> None:
    """A structural fact the explainer has to state: `score_index` bottoms at 0.2.

    So no `q_m`, and therefore no L, can fall below 0.2 — the bottom fifth of the nominal range is
    unreachable by construction. That is a scale choice rather than a bug, and it is asserted here
    because a reader who assumes 0 is the floor will misread every low score they ever see.
    """
    assert MaturityLevel.BASIC.score_index == pytest.approx(0.2)
    assert MaturityLevel.FRONTIER.score_index == pytest.approx(1.0)

    document = showcase_document(_uniform(MaturityLevel.BASIC, StrengthRating.NONE, 1.0))
    registry, coefficients = profile_scoring_context(profile_key_of(document))
    result = deterministic_result(document, coefficients, registry)
    assessed = [module.q_m for module in result.modules if module.q_m is not None]
    assert assessed, "no module scored, so this test proves nothing"
    assert min(assessed) == pytest.approx(0.2), (
        "an all-Basic firm no longer floors at 0.2; the maturity scale has changed and the "
        "analysis document's structural note needs updating"
    )
    assert result.composite.l_index == pytest.approx(0.2)


def test_aggregation_is_what_concentrates_the_score() -> None:
    """The mechanism itself, reduced to something a test can hold.

    A firm rated identically everywhere reaches the ends of the scale. A firm whose modules
    disagree with each other lands in the middle — not because the engine did anything to it, but
    because V is an average and averages concentrate. Asserting this keeps the *explanation* in the
    codebase rather than only in a document.
    """
    consistent_low = _v(_uniform(MaturityLevel.BASIC, StrengthRating.NONE, 1.0))
    consistent_high = _v(_uniform(MaturityLevel.FRONTIER, StrengthRating.WIDE, 1.0))

    # A deliberately mixed firm: alternating extremes, module by module.
    levels = (MaturityLevel.BASIC.value, MaturityLevel.FRONTIER.value)
    strengths = (StrengthRating.NONE.value, StrengthRating.WIDE.value)
    mixed = dataclasses.replace(
        REVOLUT,
        subject="synthetic-mixed",
        v_base=tuple((key, levels[i % 2]) for i, (key, _) in enumerate(REVOLUT.v_base)),
        v_over=(),
        c_base=tuple((key, levels[i % 2]) for i, (key, _) in enumerate(REVOLUT.c_base)),
        powers=tuple(
            (key, (strengths[i % 2], strengths[i % 2])) for i, (key, _) in enumerate(REVOLUT.powers)
        ),
    )
    mixed_score = _v(mixed)

    assert consistent_low < mixed_score < consistent_high, (
        f"a firm built from alternating extremes scored {mixed_score:.3f}, outside the range its "
        f"own consistent counterparts reach ({consistent_low:.3f}..{consistent_high:.3f})"
    )
    # And it lands nearer the middle than either end — which is the whole finding.
    midpoint = (consistent_low + consistent_high) / 2
    assert abs(mixed_score - midpoint) < abs(mixed_score - consistent_low)
    assert abs(mixed_score - midpoint) < abs(mixed_score - consistent_high)


def test_the_analysis_document_is_committed_beside_the_guard() -> None:
    """The tests are the guard; the document is the answer. One without the other is half a
    ticket."""
    from pathlib import Path

    analysis = Path(__file__).resolve().parents[1] / "docs/analysis/score-dispersion-2026-07.md"
    assert analysis.exists(), "the analysis document GRS-0223 exists to produce is missing"
    text = analysis.read_text()
    # The conclusion, and the two numbers it rests on.
    assert "Aggregation is" in text
    assert "0.815" in text
    assert "92.6%" in text
    assert "No engine change" in text
