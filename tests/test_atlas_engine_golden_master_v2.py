"""Golden master v2 — the four-index V (ADR-0023 Stage 2 / Methodology v1.4, GRS-0086).

v1.4 folds C into the headline composite: V = θ_B·B + θ_P·P + θ_L·L + θ_C·C, Σθ = 1. This is the
deterministic change the staged design deferred, so it gets its OWN hand-computed oracle. The v1
golden master (three-index, V=0.478565) is preserved untouched in
`tests/test_atlas_engine_golden_master.py` — this file never edits it.

The oracle: the SAME ratified Meridian B/P/L (from the v1 golden master) plus a fixed C rating
pattern, combined under the DRAFT v1.4 θ split. Because the θ_C panel has not convened, the draft θ
(0.25/0.25/0.35/0.15) is a documented placeholder; when the panel ratifies the real four θ this
oracle is re-cut. The arithmetic identity V = Σθ·index is what is load-bearing here."""

from __future__ import annotations

from bcap_contracts.assessments import AssessmentDocument, SubcomponentRating
from bcap_contracts.common import EvidenceGrade, MaturityLevel
from bcap_contracts.registry import load_registry

from grassmarket.assessments.service import complete_c_subcomponents
from grassmarket.atlas import score
from grassmarket.atlas.draft_coefficients import (
    draft_v1_4_coefficient_set,
    draft_v1_coefficient_set,
)
from tests._atlas_inputs import meridian_inputs

_REGISTRY = load_registry()
_E3 = EvidenceGrade.E3_ARTIFACT

# The ratified Meridian B/P/L (byte-identical to the v1 golden master — v1.4 does not touch them).
_B, _P, _L = 0.67907, 0.271429, 0.483539
# The v2 C rating pattern: CUST_ONBOARDING fully Advanced, the rest completing to Not Assessed. With
# CUST_ONBOARDING a critical-for-C module, the weighted and min C terms are both the Advanced index
# C = 0.8. Fixed here so the oracle is reproducible.
_C = 0.8
# The DRAFT v1.4 θ split (placeholder, pending the θ_C panel).
_THETA_B, _THETA_P, _THETA_L, _THETA_C = 0.25, 0.25, 0.35, 0.15
_V2 = round(_THETA_B * _B + _THETA_P * _P + _THETA_L * _L + _THETA_C * _C, 6)


def _v14_inputs():
    onboarding = _REGISTRY.require_c_module("CUST_ONBOARDING")
    c_doc = AssessmentDocument(
        c_subcomponents=tuple(
            SubcomponentRating(
                module_key=onboarding.key,
                subcomponent_key=s.key,
                level=MaturityLevel.ADVANCED,
                evidence_grade=_E3,
            )
            for s in onboarding.subcomponents
        )
    )
    return meridian_inputs().model_copy(
        update={"c_subcomponents": complete_c_subcomponents(c_doc, _REGISTRY)}
    )


def test_four_index_v_reproduces_golden_master_v2() -> None:
    result = score(_v14_inputs(), draft_v1_4_coefficient_set(_REGISTRY), _REGISTRY)
    assert result.composite.v_index == _V2  # the four-index oracle, to the last decimal
    # V is the four-term composite of the (unchanged) B/P/L and the folded C.
    assert result.composite.b_index == _B
    assert result.composite.p_index == _P
    assert result.composite.l_index == _L
    assert result.composite.c_index == _C
    assert result.methodology_version == "1.4"


def test_v2_v_equals_the_weighted_four_index_sum() -> None:
    result = score(_v14_inputs(), draft_v1_4_coefficient_set(_REGISTRY), _REGISTRY)
    c = result.composite
    expected = round(
        _THETA_B * c.b_index + _THETA_P * c.p_index + _THETA_L * c.l_index + _THETA_C * c.c_index,
        6,
    )
    assert c.v_index == expected  # C is genuinely IN V (not reported alongside)


def test_v1_three_index_master_is_untouched_by_v14() -> None:
    # The ratified Meridian inputs scored under the v1 three-index set still reproduce V byte for
    # byte — folding C in is a NEW methodology version, never an edit to the settled one. (The v1
    # set carries no C coefficients, so it takes the B/P/L inputs only, no C ratings.)
    result = score(meridian_inputs(), draft_v1_coefficient_set(_REGISTRY), _REGISTRY)
    assert result.composite.v_index == 0.478565
    assert result.composite.c_index is None  # v1 does not compute or fold C
    assert result.methodology_version == "1.1"
