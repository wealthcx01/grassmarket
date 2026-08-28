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
from bcap_contracts.registry import load_profile, load_registry
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
    # The construction-time guarantee: 'every weight traces to a provenance record'.
    cs = elicited_v1_coefficient_set(registry)
    assert set(cs.provenance) == _EXPECTED_PROVENANCE_FAMILIES
    for family, record in cs.provenance.items():
        assert record.set_by == "bruntsfield-engineering-provisional-2026-07", family
        assert record.review_due > record.set_on, family


def test_no_provenance_record_claims_a_panel_that_has_not_met(registry) -> None:
    """GRS-0237 scope 3. The record must not assert evidence that does not exist.

    Until 2026-08-19 every family in this set was stamped
    ``set_by="bruntsfield-elicitation-panel-2026"`` with a note reading "elicited by the Bruntsfield
    weight panel". No such panel has met. The methods appendix prints this record for a client to
    check, so it is a claim about evidence, not an internal label.

    Asserted as a **property** rather than as the new literal alone: a future edit that reintroduces
    a panel claim under any wording fails here. When the panel does meet, this test is the thing to
    delete — deliberately, in the same commit that records the session.
    """
    # All three CLIENT-USABLE sets, not just retail. The wealth and exchange sets are the ones
    # actually ACTIVE today (ADR-0037), so a false claim in their records reaches a real client
    # first. Their wording was already honest when this was written; the guard keeps it that way.
    from grassmarket.atlas.elicited_coefficients import (
        elicited_exchange_coefficient_set,
        elicited_wealth_coefficient_set,
    )

    view = load_registry()
    sets = {
        "retail": elicited_v1_coefficient_set(registry),
        "wealth": elicited_wealth_coefficient_set(view.for_profile(load_profile("wealth"))),
        "exchange": elicited_exchange_coefficient_set(view.for_profile(load_profile("exchange"))),
    }
    for label, cs in sets.items():
        for family, record in cs.provenance.items():
            blob = f"{record.set_by} {record.notes or ''}".lower()
            assert "elicitation-panel" not in blob, (
                f"{label}/{family}: provenance names an elicitation panel as the setter. No panel "
                f"has met (founder decision D1). Say what actually set these values."
            )
            # The word "panel" may legitimately appear while saying the panel is PENDING, so the
            # check is on the claim, not the word: a record may not assert the panel did the work.
            # Note this also forbids DENYING it in those words — "not panel-elicited" contains the
            # assertion as a substring, and a client skims phrases rather than parsing logic.
            assert not any(
                phrase in blob
                for phrase in ("elicited by the", "panel-elicited", "expert-elicited")
            ), f"{label}/{family}: provenance claims the weights were elicited. They were not, yet."


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


def test_retail_is_not_activated() -> None:
    """Founder decision D1, 2026-08-27: retail stays on the DRAFT set until the panel runs.

    Activating the v1 set was built and measured, then rejected. It buys only four different
    scalars — every weight family is uniform 1.0 in BOTH sets — and it broke firm-ordering
    stability: perturbing the strength encoding by ±20% reordered the showcase firms in 3 of 40
    draws, where the draft set never did. "This firm scores above that one" would have become
    sensitive to a weight nobody has ratified, on a client-facing document.

    **The flip then reached `main` by accident** — an uncommitted activation was swept up by a
    `git add -A` on an unrelated docs branch, so the PR that recorded "retail stays off" is the one
    that turned it on. This test exists so that cannot happen silently again: it fails the moment
    retail is activated, and says why.

    Accepted consequence: a retail assessment cannot produce a client-facing deliverable. GRS-0150
    is the only route that changes it.
    """
    from grassmarket.atlas import active_coefficient_set, active_uncertainty_model

    registry = load_registry()
    active = active_coefficient_set(registry)
    assert active.client_usable is False
    assert active.version == draft_v1_coefficient_set(registry).version
    # Both seams, because they flip together (ADR-0022) and half a flip is worse than either state.
    assert active_uncertainty_model().client_usable is False


def test_elicited_uncertainty_model_is_client_usable() -> None:
    from grassmarket.atlas.montecarlo import elicited_v1_uncertainty_model

    model = elicited_v1_uncertainty_model()
    assert model.client_usable is True
    assert model.version == "v1-elicited-2026"
    # It carries a real panel provenance record, not a DIRECT placeholder.
    assert model.provenance.set_by == "bruntsfield-elicitation-panel-2026"
    assert model.provenance.method is not WeightMethod.DIRECT


def test_the_uncertainty_seam_stays_draft_with_the_coefficient_seam() -> None:
    """ADR-0022's pairing rule: the two seams flip together or not at all.

    A client pack that mixed activated weights with draft uncertainty widths would carry ranges
    from a set nobody ratified. When D1's activation was attempted, only the coefficients were
    flipped at first — this pairing is what caught it.
    """
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


def test_segment_starter_sets_are_activated() -> None:
    # Wealth and exchange were activated 2026-07-20 (ADR-0037/GRS-0156); RETAIL joined them on
    # 2026-08-27 (founder decision D1), so all three now score on client-usable sets.
    #
    # The paired assertion is the one that matters: both seams flip together. A client pack that
    # mixed activated weights with draft uncertainty widths would carry ranges from a set nobody
    # ratified — and implementing D1 initially flipped only the coefficients, which is exactly
    # what this caught.
    from grassmarket.atlas.active import active_uncertainty_model, profile_scoring_context

    for profile in ("wealth", "exchange"):
        _, active = profile_scoring_context(profile)
        assert active.client_usable is True, profile
        assert "elicited" in active.version, profile
        assert active_uncertainty_model(profile).client_usable is True, profile

    # Retail is the contrast case again (D1, 2026-08-27).
    _, retail = profile_scoring_context("retail")
    assert retail.client_usable is False
    assert active_uncertainty_model("retail").client_usable is False


def test_activated_segment_passes_the_client_pack_gate_end_to_end() -> None:
    # The unblock: a client-facing wealth/exchange pack now clears BOTH gates (coefficients +
    # uncertainty, ADR-0022), where retail still refuses on its draft set.
    from bcap_contracts.deliverables import DeliverableMode

    from grassmarket.atlas.active import active_uncertainty_model, profile_scoring_context
    from grassmarket.deliverables.gate import (
        ClientUsabilityError,
        assert_uncertainty_client_usable,
        resolve_mode,
    )

    for profile in ("wealth", "exchange"):
        _, coeffs = profile_scoring_context(profile)
        assert resolve_mode(coeffs, client_facing=True) is DeliverableMode.CLIENT
        assert_uncertainty_client_usable(active_uncertainty_model(profile), client_facing=True)

    _, retail = profile_scoring_context("retail")
    with pytest.raises(ClientUsabilityError):
        resolve_mode(retail, client_facing=True)
