"""The elicited v1 coefficient set (GRS-0033) — client-usability, provenance, and gate flip.

Four guarantees:
1. It constructs client-usable with a Weight Provenance Record on *every* populated family.
2. It validates against the real registry (covers every dimension exactly — ADR-0001).
3. The GRS-0015 client gate OPENS under it and REFUSES under the draft set — the one behaviour
   that separates a client pack from an internal draft.
4. Its elicited weights actually flow through the engine: a golden master pins the composite, and
   it is distinct from the draft set's (proving the elicited θ / strength-encoding are real inputs,
   not the draft placeholders under a new name).
"""

from __future__ import annotations

import pytest
from bcap_contracts.assessments import CoefficientSet
from bcap_contracts.common import WeightMethod
from bcap_contracts.registry import load_registry
from pydantic import ValidationError

from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set
from grassmarket.atlas.elicited_coefficients import elicited_v1_coefficient_set
from grassmarket.atlas.engine import score
from grassmarket.deliverables.gate import ClientUsabilityError, resolve_mode

from ._atlas_inputs import uniform_inputs

# Every family the elicited set populates must carry provenance (Methodology §6, ADR-0001 §3).
_EXPECTED_PROVENANCE_FAMILIES = {
    "theta",
    "alpha_l",
    "alpha_module",
    "lambda",
    "delta",
    "w_power",
    "w_metric",
    "group_weights",
    "strength_encoding",
}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def test_elicited_set_is_client_usable(registry) -> None:
    cs = elicited_v1_coefficient_set(registry)
    assert cs.client_usable is True
    assert cs.version == "v1-elicited-2026"


def test_every_populated_family_carries_provenance(registry) -> None:
    # The construction-time guarantee: 'every elicited weight traces to a provenance record'.
    cs = elicited_v1_coefficient_set(registry)
    assert set(cs.provenance) == _EXPECTED_PROVENANCE_FAMILIES
    for family, record in cs.provenance.items():
        assert record.set_by == "bruntsfield-elicitation-panel-2026", family
        assert record.review_due > record.set_on, family


def test_theta_is_non_uniform_and_sums_to_one(registry) -> None:
    # Distinct from the draft's placeholders — the panel weights barrier/lifecycle over benefit.
    cs = elicited_v1_coefficient_set(registry)
    assert (cs.theta_b, cs.theta_p, cs.theta_l) == (0.25, 0.35, 0.40)
    assert cs.theta_b + cs.theta_p + cs.theta_l == pytest.approx(1.0)


def test_alpha_values_are_pinned(registry) -> None:
    # α_L and α_module do not move the composite on the uniform fixture (L is identical to the draft
    # and no critical-module lifecycle blend fires), so the golden master cannot guard them — pin
    # them directly, or a fat-fingered α at ratification would slip through CI silently.
    cs = elicited_v1_coefficient_set(registry)
    assert cs.alpha_l == 0.65
    assert set(cs.alpha_module.values()) == {0.75}
    assert set(cs.alpha_module) == set(registry.module_keys())


def test_validate_against_real_registry_passes(registry) -> None:
    # Covers every populated registry dimension exactly — construction already ran this, but pin it.
    elicited_v1_coefficient_set(registry).validate_against(registry)  # must not raise


def test_dropping_any_provenance_family_refuses_construction(registry) -> None:
    # Prove the guarantee is structural, not incidental: strip one family's provenance and the set
    # will not construct (CoefficientSet refuses a populated family with no provenance record).
    cs = elicited_v1_coefficient_set(registry)
    for family in _EXPECTED_PROVENANCE_FAMILIES:
        maimed = dict(cs.provenance)
        del maimed[family]
        payload = cs.model_dump()
        payload["provenance"] = {k: v.model_dump() for k, v in maimed.items()}
        with pytest.raises(ValidationError):
            CoefficientSet.model_validate(payload)


# --- The GRS-0015 client gate flips on client_usable -------------------------------------------


def test_client_gate_opens_under_elicited(registry) -> None:
    from bcap_contracts.deliverables import DeliverableMode

    cs = elicited_v1_coefficient_set(registry)
    assert resolve_mode(cs, client_facing=True) is DeliverableMode.CLIENT


def test_client_gate_refuses_under_draft(registry) -> None:
    draft = draft_v1_coefficient_set(registry)
    with pytest.raises(ClientUsabilityError):
        resolve_mode(draft, client_facing=True)


def test_internal_draft_allowed_on_both_sets(registry) -> None:
    from bcap_contracts.deliverables import DeliverableMode

    elicited = elicited_v1_coefficient_set(registry)
    draft = draft_v1_coefficient_set(registry)
    assert resolve_mode(elicited, client_facing=False) is DeliverableMode.DRAFT_INTERNAL
    assert resolve_mode(draft, client_facing=False) is DeliverableMode.DRAFT_INTERNAL


# --- Golden master: the elicited weights reach the score ---------------------------------------


def test_elicited_golden_master(registry) -> None:
    """Regression pin on the composite the elicited set produces on the uniform fixture. These are
    the PROVISIONAL panel values, not a hand-computed truth oracle — the pin exists so that when the
    panel ratifies the real θ/strength-encoding, updating them is a deliberate change to this test,
    never a silent edit (ADR-0022). θ moves V; strength encoding moves P; α is pinned separately in
    test_alpha_values_are_pinned (it is invisible to this fixture)."""
    result = score(uniform_inputs(registry), elicited_v1_coefficient_set(registry), registry)
    assert result.composite.b_index == pytest.approx(0.558333)
    assert result.composite.p_index == pytest.approx(0.35)
    assert result.composite.l_index == pytest.approx(0.5)
    assert result.composite.v_index == pytest.approx(0.462083)
    assert result.v_display_0_100 == pytest.approx(46.2083)
    assert result.coefficient_version == "v1-elicited-2026"


def test_elicited_composite_differs_from_draft(registry) -> None:
    # The elicited set is not the draft under a new label: different θ and strength encoding move
    # the composite. (Same B — the metric anchors are identical; P and V diverge.)
    inputs = uniform_inputs(registry)
    elicited = score(inputs, elicited_v1_coefficient_set(registry), registry)
    draft = score(inputs, draft_v1_coefficient_set(registry), registry)
    assert elicited.composite.v_index != draft.composite.v_index
    assert elicited.composite.p_index != draft.composite.p_index


def test_draft_stays_the_active_default() -> None:
    # Activation of the elicited set is a deliberate, panel-gated flip (ADR-0022), never automatic.
    # The engine's active coefficient set must remain the (non-client-usable) draft until then.
    from grassmarket.atlas import active_coefficient_set

    registry = load_registry()
    active = active_coefficient_set(registry)
    assert active.client_usable is False
    assert active.version == draft_v1_coefficient_set(registry).version


# --- The §7 uncertainty twin: the second client-usability-gated artifact -----------------------


def test_elicited_uncertainty_model_is_client_usable() -> None:
    from grassmarket.atlas.montecarlo import elicited_v1_uncertainty_model

    model = elicited_v1_uncertainty_model()
    assert model.client_usable is True
    assert model.version == "v1-elicited-2026"
    # It carries a real panel provenance record, not a DIRECT placeholder.
    assert model.provenance.set_by == "bruntsfield-elicitation-panel-2026"
    assert model.provenance.method is not WeightMethod.DIRECT


def test_active_uncertainty_model_stays_draft() -> None:
    # The uncertainty seam flips in the SAME reviewed commit as the coefficient seam (ADR-0022), so
    # a client pack never mixes elicited weights with draft widths. Until then, both stay draft.
    from grassmarket.atlas import active_uncertainty_model

    model = active_uncertainty_model()
    assert model.client_usable is False
    assert model.version == "v1-draft-pending-elicitation"


# --- Segment starter sets (GRS-0150, ADR-0037) — built, validated, but NOT active ---------
def test_segment_elicited_starter_sets_build_and_validate() -> None:
    from bcap_contracts.registry import load_profile

    from grassmarket.atlas.elicited_coefficients import (
        elicited_exchange_coefficient_set,
        elicited_wealth_coefficient_set,
    )

    r = load_registry()
    for profile, fn, version in (
        ("wealth", elicited_wealth_coefficient_set, "wealth-v1-elicited-starter-2026"),
        ("exchange", elicited_exchange_coefficient_set, "exchange-v1-elicited-starter-2026"),
    ):
        view = r.for_profile(load_profile(profile))
        cs = fn(view)
        cs.validate_against(view)  # covers the profile view exactly (fail-loud)
        assert cs.client_usable is True
        assert cs.version == version
        assert abs(cs.theta_b + cs.theta_p + cs.theta_l - 1.0) < 1e-9
        # Research-refined: weights are non-uniform (not the draft placeholders).
        assert len(set(cs.delta.values())) > 1
        assert len(set(cs.w_power.values())) > 1


def test_segment_starter_sets_are_not_active() -> None:
    # The starter sets exist but the engine still scores non-retail on the DRAFT set — activation is
    # a deliberate flip (ADR-0022). Guards against an accidental client-usable default.
    from grassmarket.atlas.active import profile_scoring_context

    for profile in ("wealth", "exchange"):
        _, active = profile_scoring_context(profile)
        assert active.client_usable is False
        assert "elicited" not in active.version
