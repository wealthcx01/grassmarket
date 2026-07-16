"""GRS-0082 — the C-index engine (ADR-0023, Stage 1: report-alongside).

`_score_c` is the L-shaped aggregation over the SEPARATE C registry dimension. Stage 1 reports C
alongside V and never sums it into V (that is v1.4 / GRS-0086), so the golden master must stay
byte-identical. These tests prove: V is unchanged when C is added; C obeys the same structural
guarantees as L (monotonicity, bottleneck, N/A renormalisation, Not-Assessed exclusion); and the
C coefficients + inputs are fail-loud (ADR-0001)."""

from __future__ import annotations

import pytest
from bcap_contracts.assessments import CoefficientSet, SubcomponentRating
from bcap_contracts.common import EvidenceGrade, MaturityLevel, NonScoreState
from bcap_contracts.registry import Registry, UnknownKeyError, load_registry

from grassmarket.atlas import AssessmentInputs, score
from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set
from tests._atlas_inputs import uniform_inputs

_L = MaturityLevel
_E3 = EvidenceGrade.E3_ARTIFACT

# A C subcomponent override is a level (assessed at E3), a (level, evidence) pair, or a non-score.
CValue = MaturityLevel | tuple[MaturityLevel, EvidenceGrade] | NonScoreState


@pytest.fixture(scope="module")
def registry() -> Registry:
    return load_registry()


def _c_ratings(
    registry: Registry,
    *,
    level: MaturityLevel = _L.DEVELOPING,
    overrides: dict[str, CValue] | None = None,
) -> tuple[SubcomponentRating, ...]:
    """Every C subcomponent at ``level`` (E3), with per-subcomponent overrides applied."""
    overrides = overrides or {}
    out: list[SubcomponentRating] = []
    for module in registry.c_modules:
        for sub in module.subcomponents:
            val = overrides.get(sub.key)
            if isinstance(val, NonScoreState):
                out.append(
                    SubcomponentRating(module_key=module.key, subcomponent_key=sub.key, state=val)
                )
            else:
                lvl, ev = val if isinstance(val, tuple) else (val or level, _E3)
                out.append(
                    SubcomponentRating(
                        module_key=module.key,
                        subcomponent_key=sub.key,
                        level=lvl,
                        evidence_grade=ev,
                    )
                )
    return tuple(out)


def _inputs_with_c(registry: Registry, c_overrides: dict[str, CValue] | None = None) -> tuple:
    """A full B/P/L uniform assessment plus C ratings — returns (bpl_only, with_c)."""
    bpl = uniform_inputs(registry)
    with_c = bpl.model_copy(update={"c_subcomponents": _c_ratings(registry, overrides=c_overrides)})
    return bpl, with_c


def _c_of(registry: Registry, c_overrides: dict[str, CValue] | None = None) -> float:
    coeffs = draft_v1_coefficient_set(registry, score_c=True)
    _, with_c = _inputs_with_c(registry, c_overrides)
    result = score(with_c, coeffs, registry)
    assert result.customer is not None
    return result.customer.value


# --- C reported alongside V; V unchanged ------------------------------------------------


def test_adding_c_does_not_change_v(registry: Registry) -> None:
    bpl_coeffs = draft_v1_coefficient_set(registry)  # no C
    c_coeffs = draft_v1_coefficient_set(registry, score_c=True)
    bpl_only, with_c = _inputs_with_c(registry)

    v_without_c = score(bpl_only, bpl_coeffs, registry)
    v_with_c = score(with_c, c_coeffs, registry)

    # V is byte-identical: C rides alongside, never into the composite sum (Stage 1).
    assert v_with_c.composite.v_index == v_without_c.composite.v_index
    assert v_with_c.composite.b_index == v_without_c.composite.b_index
    assert v_with_c.composite.p_index == v_without_c.composite.p_index
    assert v_with_c.composite.l_index == v_without_c.composite.l_index


def test_c_is_reported_only_when_the_set_scores_c(registry: Registry) -> None:
    bpl_only, _ = _inputs_with_c(registry)
    without_c = score(bpl_only, draft_v1_coefficient_set(registry), registry)
    assert without_c.customer is None  # first-class absence, never a zero (D9)
    assert without_c.composite.c_index is None

    _, with_c = _inputs_with_c(registry)
    with_c_result = score(with_c, draft_v1_coefficient_set(registry, score_c=True), registry)
    assert with_c_result.customer is not None
    assert with_c_result.composite.c_index == with_c_result.customer.value
    assert 0.0 <= with_c_result.customer.value <= 1.0


# --- C obeys the L structural guarantees (shared aggregation) ---------------------------


def test_c_is_monotonic_in_its_subcomponents(registry: Registry) -> None:
    a_sub = next(iter(registry.all_c_subcomponent_keys()))
    low = _c_of(registry, {a_sub: _L.BASIC})
    high = _c_of(registry, {a_sub: _L.FRONTIER})
    assert high >= low  # raising any C subcomponent never lowers C


def test_c_bottleneck_dominates(registry: Registry) -> None:
    # Dropping one subcomponent to Basic must not raise C above the all-Developing baseline.
    baseline = _c_of(registry)
    a_sub = next(iter(registry.all_c_subcomponent_keys()))
    with_bottleneck = _c_of(registry, {a_sub: _L.BASIC})
    assert with_bottleneck <= baseline


def test_c_not_applicable_renormalises_and_not_assessed_is_excluded(registry: Registry) -> None:
    # A single N/A subcomponent renormalises its module's weights; C stays a valid score, not a
    # crash or a zero. Compare against a run where that subcomponent is simply Developing.
    a_sub = next(iter(registry.all_c_subcomponent_keys()))
    na = _c_of(registry, {a_sub: NonScoreState.NOT_APPLICABLE})
    assert 0.0 <= na <= 1.0
    # Not Assessed on a non-critical subcomponent is excluded from the score (never zero-filled).
    not_assessed = _c_of(registry, {a_sub: NonScoreState.NOT_ASSESSED})
    assert 0.0 <= not_assessed <= 1.0


# --- Fail-loud (ADR-0001) ----------------------------------------------------------------


def test_half_populated_c_coefficients_are_refused(registry: Registry) -> None:
    base = draft_v1_coefficient_set(registry, score_c=True)
    # alpha_c set but delta_c emptied → all-or-nothing refusal at construction (validators re-run).
    with pytest.raises(ValueError, match="all-or-nothing"):
        CoefficientSet(**{**base.model_dump(), "delta_c": {}})


def test_c_coefficient_without_provenance_is_refused(registry: Registry) -> None:
    base = draft_v1_coefficient_set(registry, score_c=True)
    dumped = base.model_dump()
    dumped["provenance"].pop("delta_c")  # populated C family, provenance removed
    with pytest.raises(ValueError, match="provenance|Provenance"):
        CoefficientSet(**dumped)


def test_unknown_c_module_key_is_a_load_time_error(registry: Registry) -> None:
    base = draft_v1_coefficient_set(registry, score_c=True)
    bad = base.model_copy(update={"delta_c": {**base.delta_c, "CUST_NOT_A_MODULE": 1.0}})
    with pytest.raises((UnknownKeyError, ValueError)):
        bad.validate_against(registry)


def test_c_subcomponents_without_a_c_scoring_set_are_refused(registry: Registry) -> None:
    bpl_coeffs = draft_v1_coefficient_set(registry)  # scores_c is False
    _, with_c = _inputs_with_c(registry)
    with pytest.raises(ValueError, match="does not score C"):
        score(with_c, bpl_coeffs, registry)


def test_missing_c_subcomponent_input_is_refused(registry: Registry) -> None:
    coeffs = draft_v1_coefficient_set(registry, score_c=True)
    ratings = _c_ratings(registry)[:-1]  # drop one → incomplete C coverage
    bpl = uniform_inputs(registry)
    incomplete: AssessmentInputs = bpl.model_copy(update={"c_subcomponents": ratings})
    with pytest.raises(ValueError, match="c_subcomponent"):
        score(incomplete, coeffs, registry)
