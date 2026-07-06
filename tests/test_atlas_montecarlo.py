"""Uncertainty-engine tests (GRS-0005, Methodology v1.1 §7).

Each test fixes the seed and asserts a behavioural guarantee that fails if Monte Carlo is wrong:
bands are ordered and reproducible; P50 sits on the deterministic point; evidence grade drives the
width (all-E4 tighter than all-E1); the tornado ranks a known high-leverage input on top; a
Not-Assessed input widens the band versus the same input assessed. The RNG is always injected and
seeded — never module-global — which is what keeps the golden-master determinism intact.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest
from bcap_contracts.assessments import SubcomponentRating
from bcap_contracts.common import (
    EvidenceGrade,
    MaturityLevel,
    MetricConfidence,
    NonScoreState,
    StrengthRating,
)
from bcap_contracts.registry import Registry, load_registry
from bcap_contracts.uncertainty import UncertaintyModel
from pydantic import ValidationError

from grassmarket.atlas import (
    AssessmentInputs,
    MetricObservation,
    PowerObservation,
    draft_v1_uncertainty_model,
    run_monte_carlo,
    score,
)
from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set

_FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "golden_master.json"
_E4 = EvidenceGrade.E4_OBSERVED
_E1 = EvidenceGrade.E1_SELF_REPORTED
_ADV = MaturityLevel.ADVANCED

SubOverride = tuple[MaturityLevel, EvidenceGrade] | NonScoreState


@pytest.fixture(scope="module")
def registry() -> Registry:
    return load_registry()


@pytest.fixture(scope="module")
def coeffs(registry: Registry):
    return draft_v1_coefficient_set(registry)


@pytest.fixture(scope="module")
def model() -> UncertaintyModel:
    return draft_v1_uncertainty_model()


def _meridian_inputs() -> AssessmentInputs:
    gm = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    subs = [
        SubcomponentRating(
            module_key=m["key"], subcomponent_key=s["key"], state=NonScoreState(s["state"])
        )
        if s["state"]
        else SubcomponentRating(
            module_key=m["key"],
            subcomponent_key=s["key"],
            level=MaturityLevel(s["level"]),
            evidence_grade=EvidenceGrade(s["evidence"]),
        )
        for m in gm["modules"]
        for s in m["subcomponents"]
    ]
    metrics = [
        MetricObservation(
            metric_key=r["key"],
            raw=None if r["state"] else r["raw"],
            state=NonScoreState(r["state"]) if r["state"] else None,
        )
        for r in gm["business"]["metrics"]
    ]
    powers = [
        PowerObservation(
            power_key=p["key"],
            benefit=StrengthRating(p["benefit"]),
            barrier=StrengthRating(p["barrier"]),
        )
        for p in gm["powers"]["powers"]
    ]
    return AssessmentInputs(subcomponents=tuple(subs), metrics=tuple(metrics), powers=tuple(powers))


def _uniform_inputs(
    registry: Registry,
    *,
    level: MaturityLevel = _ADV,
    evidence: EvidenceGrade = _E4,
    overrides: dict[str, SubOverride] | None = None,
    metric_confidence: MetricConfidence | None = None,
    power_grade: EvidenceGrade | None = None,
) -> AssessmentInputs:
    overrides = overrides or {}
    subs: list[SubcomponentRating] = []
    for module in registry.modules:
        for sub in module.subcomponents:
            ov = overrides.get(sub.key)
            if isinstance(ov, NonScoreState):
                subs.append(
                    SubcomponentRating(module_key=module.key, subcomponent_key=sub.key, state=ov)
                )
            elif isinstance(ov, tuple):
                subs.append(
                    SubcomponentRating(
                        module_key=module.key,
                        subcomponent_key=sub.key,
                        level=ov[0],
                        evidence_grade=ov[1],
                    )
                )
            else:
                subs.append(
                    SubcomponentRating(
                        module_key=module.key,
                        subcomponent_key=sub.key,
                        level=level,
                        evidence_grade=evidence,
                    )
                )
    metrics = [
        MetricObservation(
            metric_key=m.key,
            raw=float(m.normalisation.anchors[1].raw),
            confidence=metric_confidence,
        )
        for m in registry.metrics
    ]
    powers = [
        PowerObservation(
            power_key=p.key,
            benefit=StrengthRating.EMERGING,
            barrier=StrengthRating.EMERGING,
            benefit_grade=power_grade,
            barrier_grade=power_grade,
        )
        for p in registry.powers
    ]
    return AssessmentInputs(subcomponents=tuple(subs), metrics=tuple(metrics), powers=tuple(powers))


def _width(band) -> float:
    return band.p90 - band.p10


# --- Determinism & band ordering --------------------------------------------------------


def test_bands_ordered_and_run_to_run_deterministic(registry, coeffs, model) -> None:
    inputs = _meridian_inputs()
    r1 = run_monte_carlo(inputs, coeffs, registry, model, random.Random(20260705), draws=800)
    r2 = run_monte_carlo(inputs, coeffs, registry, model, random.Random(20260705), draws=800)
    for band in (r1.v_band, r1.l_band, r1.b_band, r1.p_band):
        assert band.p10 <= band.p50 <= band.p90
    # Same seed + same draws ⇒ byte-identical result (the injected-RNG guarantee).
    assert r1 == r2


def test_different_seeds_differ_but_stay_ordered(registry, coeffs, model) -> None:
    inputs = _meridian_inputs()
    a = run_monte_carlo(inputs, coeffs, registry, model, random.Random(1), draws=800)
    b = run_monte_carlo(inputs, coeffs, registry, model, random.Random(2), draws=800)
    assert a.v_band != b.v_band  # sampling actually varies with the seed
    for band in (a.v_band, b.v_band):
        assert band.p10 <= band.p50 <= band.p90


# --- P50 sits on the deterministic point ------------------------------------------------


def test_p50_sits_on_the_deterministic_point(registry, coeffs, model) -> None:
    inputs = _meridian_inputs()
    point = score(inputs, coeffs, registry).composite.v_index
    res = run_monte_carlo(inputs, coeffs, registry, model, random.Random(7), draws=3000)
    assert res.v_band.p50 == pytest.approx(point, abs=0.01)
    assert res.v_band.p10 <= point <= res.v_band.p90


# --- Evidence grade drives the width ----------------------------------------------------


def test_all_e4_is_strictly_narrower_than_all_e1(registry, coeffs, model) -> None:
    # Same assessment (all Advanced), only the evidence grade differs — width must follow evidence.
    e4 = _uniform_inputs(registry, evidence=_E4)
    e1 = _uniform_inputs(registry, evidence=_E1)
    r4 = run_monte_carlo(e4, coeffs, registry, model, random.Random(99), draws=1500)
    r1 = run_monte_carlo(e1, coeffs, registry, model, random.Random(99), draws=1500)
    assert _width(r4.v_band) < _width(r1.v_band)
    # And the E4 assessment reads as lower uncertainty overall.
    assert r4.overall_uncertainty.value == "Low"
    assert r1.overall_uncertainty.value in {"High", "Very High"}


def test_unmodelled_b_and_p_are_labelled_point_estimates(registry, coeffs, model) -> None:
    # Meridian carries no metric confidence or power grades → B and P are NOT modelled. They must be
    # degenerate AND flagged modelled=False — a point estimate, never a (falsely confident) band.
    res = run_monte_carlo(_meridian_inputs(), coeffs, registry, model, random.Random(5), draws=400)
    assert res.b_band.p10 == res.b_band.p50 == res.b_band.p90
    assert res.p_band.p10 == res.p_band.p50 == res.p_band.p90
    assert res.b_band.modelled is False
    assert res.p_band.modelled is False
    # V and L are always modelled (subcomponents drive them).
    assert res.v_band.modelled is True
    assert res.l_band.modelled is True


def test_unmodelled_bands_are_always_flagged_points(registry, coeffs, model) -> None:
    # The honesty invariant: an UNMODELLED band (modelled=False) is ALWAYS a point (p10=p50=p90) —
    # it is never handed a spurious width, and the flag tells a renderer to show it as a point,
    # never a (falsely confident) tight band. On Meridian, B and P are the unmodelled indices.
    res = run_monte_carlo(_meridian_inputs(), coeffs, registry, model, random.Random(6), draws=1000)
    for band in (res.v_band, res.l_band, res.b_band, res.p_band, *res.module_qm.values()):
        if not band.modelled:
            assert band.p10 == band.p50 == band.p90, "an unmodelled band was given spurious width"
    assert res.b_band.modelled is False
    assert res.p_band.modelled is False


def test_metric_confidence_drives_b_width(registry, coeffs, model) -> None:
    audited = _uniform_inputs(registry, metric_confidence=MetricConfidence.AUDITED)
    estimated = _uniform_inputs(registry, metric_confidence=MetricConfidence.ESTIMATED)
    r_aud = run_monte_carlo(audited, coeffs, registry, model, random.Random(8), draws=1500)
    r_est = run_monte_carlo(estimated, coeffs, registry, model, random.Random(8), draws=1500)
    assert r_aud.b_band.modelled and r_est.b_band.modelled
    assert _width(r_aud.b_band) < _width(r_est.b_band)  # weaker source → wider B


def test_power_evidence_drives_p_width(registry, coeffs, model) -> None:
    strong = _uniform_inputs(registry, power_grade=EvidenceGrade.E4_OBSERVED)
    weak = _uniform_inputs(registry, power_grade=EvidenceGrade.E1_SELF_REPORTED)
    r_strong = run_monte_carlo(strong, coeffs, registry, model, random.Random(9), draws=1500)
    r_weak = run_monte_carlo(weak, coeffs, registry, model, random.Random(9), draws=1500)
    assert r_strong.p_band.modelled and r_weak.p_band.modelled
    assert _width(r_strong.p_band) < _width(r_weak.p_band)  # weaker evidence → wider P


def test_uncertainty_model_rejects_incomplete_metric_spreads() -> None:
    m = draft_v1_uncertainty_model()
    with pytest.raises(ValidationError):
        m.model_validate({**m.model_dump(), "metric_spreads": {"audited": 0.02}})


# --- Tornado ranks a known high-leverage input on top -----------------------------------


def test_tornado_ranks_the_known_high_leverage_input_first(registry, coeffs, model) -> None:
    # All subcomponents Advanced/E4 (tight, ±1-level support) EXCEPT one Not-Assessed subcomponent
    # in a critical-for-L module (OEMS) — full Basic↔Frontier support + high L leverage. It must top
    # the tornado.
    lever = "OEMS_ASSET_COVERAGE"
    inputs = _uniform_inputs(registry, overrides={lever: NonScoreState.NOT_ASSESSED})
    res = run_monte_carlo(inputs, coeffs, registry, model, random.Random(3), draws=50)
    assert res.tornado[0].subcomponent_key == lever
    assert res.tornado[0].swing > res.tornado[1].swing


# --- Not Assessed widens the band vs the same input assessed ----------------------------


def test_not_assessed_widens_the_band_vs_assessed(registry, coeffs, model) -> None:
    lever = "OEMS_ASSET_COVERAGE"
    assessed = _uniform_inputs(registry, overrides={lever: (_ADV, _E4)})
    not_assessed = _uniform_inputs(registry, overrides={lever: NonScoreState.NOT_ASSESSED})
    r_assessed = run_monte_carlo(assessed, coeffs, registry, model, random.Random(11), draws=1500)
    r_na = run_monte_carlo(not_assessed, coeffs, registry, model, random.Random(11), draws=1500)
    assert _width(r_na.v_band) > _width(r_assessed.v_band)


# --- Weight stability -------------------------------------------------------------------


def test_weight_stability_interval_brackets_the_point(registry, coeffs, model) -> None:
    inputs = _meridian_inputs()
    res = run_monte_carlo(inputs, coeffs, registry, model, random.Random(4), draws=100)
    ws = res.weight_stability
    assert ws.v_low <= ws.v_point <= ws.v_high
    assert ws.v_low < ws.v_high  # θ/α movement actually moves V — a real sensitivity interval


# --- UncertaintyModel validation --------------------------------------------------------


def test_uncertainty_model_rejects_non_monotone_spreads() -> None:
    m = draft_v1_uncertainty_model()
    with pytest.raises(ValidationError):
        m.model_validate(
            {**m.model_dump(), "evidence_spreads": {"E1": 0.1, "E2": 0.2, "E3": 0.3, "E4": 0.4}}
        )


def test_uncertainty_model_rejects_missing_grade() -> None:
    m = draft_v1_uncertainty_model()
    with pytest.raises(ValidationError):
        m.model_validate({**m.model_dump(), "evidence_spreads": {"E1": 0.5, "E2": 0.25, "E3": 0.1}})


def test_draft_uncertainty_model_is_not_client_usable() -> None:
    assert draft_v1_uncertainty_model().client_usable is False
