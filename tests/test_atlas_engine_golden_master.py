"""The golden-master test (GRS-0004, CLAUDE.md testing rules).

The engine must reproduce the RATIFIED oracle ``tests/fixtures/golden_master.json`` — the
Meridian Securities assessment — to the last decimal: every intermediate (q_m, coverage, gate
band + note, group means, L terms, B, P, the triad) and the final V = 0.478565. The reference
script (``scripts/build_golden_master.py``) was the spec; this proves the independent engine agrees.

Inputs are reconstructed FROM the fixture; the coefficient set is the shipped v1 draft (uniform).
The one representational alias — the fixture stores non-score states as the enum NAMES
(``NOT_APPLICABLE``) while the engine emits the contract enum VALUES (``Not Applicable``) — is
normalised on load; every number is compared exactly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from bcap_contracts.assessments import SubcomponentRating
from bcap_contracts.common import EvidenceGrade, MaturityLevel, NonScoreState, StrengthRating
from bcap_contracts.registry import load_registry

from grassmarket.atlas import AssessmentInputs, MetricObservation, PowerObservation, score
from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set

_FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "golden_master.json"


@pytest.fixture(scope="module")
def gm() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _state_value(fixture_state: str | None) -> str | None:
    """The fixture stores the enum NAME (NOT_APPLICABLE); the contract value is 'Not Applicable'."""
    return NonScoreState[fixture_state].value if fixture_state else None


def _inputs_from_fixture(gm: dict) -> AssessmentInputs:
    subs: list[SubcomponentRating] = []
    for m in gm["modules"]:
        for s in m["subcomponents"]:
            if s["state"]:
                subs.append(
                    SubcomponentRating(
                        module_key=m["key"],
                        subcomponent_key=s["key"],
                        state=NonScoreState[s["state"]],
                    )
                )
            else:
                subs.append(
                    SubcomponentRating(
                        module_key=m["key"],
                        subcomponent_key=s["key"],
                        level=MaturityLevel(s["level"]),
                        evidence_grade=EvidenceGrade(s["evidence"]),
                    )
                )
    metrics = [
        MetricObservation(
            metric_key=r["key"],
            raw=None if r["state"] else r["raw"],
            state=NonScoreState[r["state"]] if r["state"] else None,
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


@pytest.fixture(scope="module")
def result(gm: dict):
    registry = load_registry()
    coeffs = draft_v1_coefficient_set(registry)
    return score(_inputs_from_fixture(gm), coeffs, registry)


def test_final_v_is_exactly_the_ratified_value(result, gm: dict) -> None:
    assert result.composite.v_index == gm["composite"]["V"] == 0.478565
    assert result.v_display_0_100 == gm["two_track"]["continuous"]["V_display_0_100"] == 47.8565


def test_composite_bpl_reproduced(result, gm: dict) -> None:
    c = gm["composite"]
    assert result.composite.b_index == c["B"]
    assert result.composite.p_index == c["P"]
    assert result.composite.l_index == c["L"]


def test_every_module_reproduced_field_by_field(result, gm: dict) -> None:
    by_key = {m.key: m for m in result.modules}
    assert set(by_key) == {m["key"] for m in gm["modules"]}
    for fm in gm["modules"]:
        em = by_key[fm["key"]]
        assert em.name == fm["name"]
        assert em.n_applicable == fm["n_applicable"]
        assert em.n_assessed == fm["n_assessed"]
        assert em.n_not_applicable == fm["n_not_applicable"]
        assert em.coverage == fm["coverage"]
        assert em.alpha == fm["alpha"]
        assert em.weighted_avg == fm["weighted_avg"]
        assert em.min_term == fm["min_term"]
        assert em.bottleneck_subcomponent == fm["bottleneck_subcomponent"]
        assert em.q_m == fm["q_m"]
        assert em.gate_band == fm["gate_band"]
        assert em.gate_blocked == fm["gate_blocked"]
        assert em.gate_note == fm["gate_note"]
        assert len(em.subcomponents) == len(fm["subcomponents"])
        for es, fs in zip(em.subcomponents, fm["subcomponents"], strict=True):
            assert es.key == fs["key"]
            assert es.critical == fs["critical"]
            assert es.level == fs["level"]
            assert es.index == fs["index"]
            assert es.evidence == fs["evidence"]
            assert es.state == _state_value(fs["state"])


def test_l_terms_reproduced(result, gm: dict) -> None:
    assert result.l_index.weighted_term == gm["L"]["weighted_term"]
    assert result.l_index.min_term == gm["L"]["min_term"]
    assert result.l_index.value == gm["L"]["value"]


def test_business_reproduced_field_by_field(result, gm: dict) -> None:
    assert result.business.b_index == gm["business"]["B"]
    assert result.business.group_means == gm["business"]["group_means"]
    by_key = {r.key: r for r in result.business.metrics}
    assert set(by_key) == {r["key"] for r in gm["business"]["metrics"]}
    for fr in gm["business"]["metrics"]:
        er = by_key[fr["key"]]
        assert er.raw == fr["raw"]
        assert er.unit == fr["unit"]
        assert er.direction == fr["direction"]
        assert er.group == fr["group"]
        assert er.state == _state_value(fr["state"])
        assert er.n_k == fr["n_k"]


def test_powers_reproduced_field_by_field(result, gm: dict) -> None:
    assert result.powers.p_index == gm["powers"]["P"]
    by_key = {p.key: p for p in result.powers.powers}
    assert set(by_key) == {p["key"] for p in gm["powers"]["powers"]}
    assert len(by_key) == 7  # all 7 powers, never N/A
    for fp in gm["powers"]["powers"]:
        ep = by_key[fp["key"]]
        assert ep.benefit == fp["benefit"]
        assert ep.barrier == fp["barrier"]
        assert ep.strength == fp["strength"]
        assert ep.value == fp["value"]


def test_triad_reproduced(result, gm: dict) -> None:
    for dim in ("economic_value", "perceived_value", "defence_value"):
        er = getattr(result.triad, dim)
        assert er.rating == gm["triad"][dim]["rating"]
        assert er.score == gm["triad"][dim]["score"]


def test_gate_bands_match_two_track(result, gm: dict) -> None:
    assert result.gate_bands == gm["two_track"]["gates"]
