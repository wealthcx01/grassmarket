"""Golden-master fixture tests (GRS-0003).

These assert the fixture is well-formed and INTERNALLY CONSISTENT — the recorded intermediates
actually compose into the recorded finals per Methodology §5. The full test that the *engine*
reproduces this fixture exactly is GRS-0004 (the engine doesn't exist yet).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
from bcap_contracts import load_registry

_FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "golden_master.json"
_LEVEL_INDEX = {"Basic": 0.2, "Developing": 0.5, "Advanced": 0.8, "Frontier": 1.0}
_BANDS = {"Basic", "Developing", "Advanced", "Frontier", "Not Rated"}


@pytest.fixture(scope="module")
def gm() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def test_fixture_is_draft_flagged(gm: dict) -> None:
    assert gm["metadata"]["status"] == "draft-pending-ratification"
    assert gm["metadata"]["methodology_version"] == "1.1"


def test_covers_the_registry_exactly(gm: dict) -> None:
    registry = load_registry()
    sub_keys = {s["key"] for m in gm["modules"] for s in m["subcomponents"]}
    assert sub_keys == registry.all_subcomponent_keys()
    assert len(sub_keys) == 51
    assert {m["key"] for m in gm["business"]["metrics"]} == registry.metric_keys()
    assert {p["key"] for p in gm["powers"]["powers"]} == registry.power_keys()


def test_exercises_non_score_states(gm: dict) -> None:
    states = [s["state"] for m in gm["modules"] for s in m["subcomponents"] if s["state"]]
    assert "Not Applicable" in states  # contract enum VALUES (D8), not the enum names
    assert "Not Assessed" in states
    # A Not-Applicable subcomponent is excluded from its module's applicable count.
    for m in gm["modules"]:
        n_na = sum(1 for s in m["subcomponents"] if s["state"] == "Not Applicable")
        assert m["n_not_applicable"] == n_na


def test_module_qm_recomputes_from_blend_and_min(gm: dict) -> None:
    alpha = gm["coefficients"]["alpha_module"]
    for m in gm["modules"]:
        if m["q_m"] is None:
            continue
        assert math.isclose(
            m["q_m"], alpha * m["weighted_avg"] + (1 - alpha) * m["min_term"], abs_tol=1e-6
        )
        # Not-Assessed and N/A never contribute: weighted_avg is the mean of assessed indices only.
        assessed = [_LEVEL_INDEX[s["level"]] for s in m["subcomponents"] if s["level"]]
        assert math.isclose(m["weighted_avg"], sum(assessed) / len(assessed), abs_tol=1e-6)
        assert math.isclose(m["min_term"], min(assessed), abs_tol=1e-6)
        assert 0.0 <= m["q_m"] <= 1.0
        assert m["gate_band"] in _BANDS


def test_no_module_is_frontier_with_a_basic_part(gm: dict) -> None:
    # The rating gate must not report Frontier for a module that has any Basic assessed part.
    for m in gm["modules"]:
        has_basic = any(s["level"] == "Basic" for s in m["subcomponents"])
        if has_basic:
            assert m["gate_band"] != "Frontier"


def test_L_recomputes(gm: dict) -> None:
    alpha_l = gm["coefficients"]["alpha_l"]
    # Fully-unassessed modules (q_m None) are EXCLUDED from both terms — never zero-filled (D9).
    assessed = {m["key"]: m["q_m"] for m in gm["modules"] if m["q_m"] is not None}
    weighted = sum(assessed.values()) / len(assessed)
    crit = [assessed[k] for k in gm["coefficients"]["critical_modules_for_l"] if k in assessed]
    min_term = min(crit)
    L = alpha_l * weighted + (1 - alpha_l) * min_term
    assert math.isclose(gm["L"]["value"], L, abs_tol=1e-6)
    assert math.isclose(gm["L"]["weighted_term"], weighted, abs_tol=1e-6)


def test_B_is_group_weighted(gm: dict) -> None:
    # B = uniform-weighted mean of group means (ADR-0006); state metrics excluded (B4).
    groups: dict[str, list[float]] = {}
    for r in gm["business"]["metrics"]:
        if r["n_k"] is None:  # Not Applicable / Not Assessed metric
            assert r["state"] in ("Not Applicable", "Not Assessed")
            continue
        assert 0.0 <= r["n_k"] <= 1.0
        groups.setdefault(r["group"], []).append(r["n_k"])
    means = {g: sum(v) / len(v) for g, v in groups.items()}
    for g, mean in means.items():
        assert math.isclose(gm["business"]["group_means"][g], mean, abs_tol=1e-6)
    b = sum(means.values()) / len(means)  # uniform group weights (draft)
    assert math.isclose(gm["business"]["B"], b, abs_tol=1e-6)


def test_all_seven_powers_in_scope_never_na(gm: dict) -> None:
    # Powers are never N/A (Methodology v1.1 §8): all 7 carry a Benefit + Barrier, none is dropped.
    powers = gm["powers"]["powers"]
    assert len(powers) == 7
    for p in powers:
        assert p.get("state") is None  # no NOT_APPLICABLE power state
        assert p["benefit"] and p["barrier"]


def test_P_uses_weaker_of_benefit_barrier_over_all_powers(gm: dict) -> None:
    enc = gm["coefficients"]["strength_encoding"]
    rank = {"None": 0, "Emerging": 1, "Established": 2, "Wide": 3}
    powers = gm["powers"]["powers"]
    for p in powers:
        weaker = p["benefit"] if rank[p["benefit"]] <= rank[p["barrier"]] else p["barrier"]
        assert p["strength"] == weaker  # Helmer: a power is only as strong as its weaker side
        assert p["value"] == enc[weaker]
    # P is the mean over ALL 7 powers (no renormalisation — no power is dropped).
    p_index = sum(p["value"] for p in powers) / len(powers)
    assert math.isclose(gm["powers"]["P"], p_index, abs_tol=1e-6)


def test_triad_is_ordinal(gm: dict) -> None:
    ordinals = {"None", "Emerging", "Established", "Wide"}
    for dim in ("economic_value", "perceived_value", "defence_value"):
        assert gm["triad"][dim]["rating"] in ordinals  # ordinal out (ADR-0002)
        assert 0.0 <= gm["triad"][dim]["score"] <= 1.0
    # Defence Value is the barrier-side aggregate across ALL 7 powers (§2 — powers never N/A).
    powers = gm["powers"]["powers"]
    barriers = [gm["coefficients"]["strength_encoding"][p["barrier"]] for p in powers]
    assert math.isclose(
        gm["triad"]["defence_value"]["score"], sum(barriers) / len(barriers), abs_tol=1e-6
    )


def test_V_recomputes_and_display(gm: dict) -> None:
    theta = gm["coefficients"]["theta"]
    assert math.isclose(theta["B"] + theta["P"] + theta["L"], 1.0, abs_tol=1e-9)
    c = gm["composite"]
    V = theta["B"] * c["B"] + theta["P"] * c["P"] + theta["L"] * c["L"]
    assert math.isclose(c["V"], V, abs_tol=1e-6)
    assert 0.0 <= c["V"] <= 1.0
    assert math.isclose(
        gm["two_track"]["continuous"]["V_display_0_100"], c["V"] * 100, abs_tol=1e-6
    )
