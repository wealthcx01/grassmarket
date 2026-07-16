"""GRS-0083 — C capture: the customer-proposition document collection + widget grid (ADR-0023).

The wizard persists C ratings and the 93-widget Level-1 grid into `AssessmentDocument`; the live
panel reports C alongside V (deterministic, Stage 1). These tests pin the contract (widget
validation, round-trip persistence) and the service surfacing (C completion + `LiveScore.c`)."""

from __future__ import annotations

import random

import pytest
from bcap_contracts.assessments import AssessmentDocument, SubcomponentRating, WidgetObservation
from bcap_contracts.common import EvidenceGrade, MaturityLevel, NonScoreState
from bcap_contracts.registry import load_registry
from pydantic import ValidationError

from grassmarket.assessments.service import (
    c_index_of,
    c_scoreable,
    complete_c_subcomponents,
    live_score,
)
from grassmarket.atlas.active import active_coefficient_set, active_uncertainty_model

_E3 = EvidenceGrade.E3_ARTIFACT


def _registry():
    return load_registry()


def _rated_c_module(registry, module_key: str) -> list[SubcomponentRating]:
    """Every subcomponent of one C module rated Advanced (E3) — enough to make C scoreable."""
    module = registry.require_c_module(module_key)
    return [
        SubcomponentRating(
            module_key=module_key,
            subcomponent_key=s.key,
            level=MaturityLevel.ADVANCED,
            evidence_grade=_E3,
        )
        for s in module.subcomponents
    ]


# --- WidgetObservation validation --------------------------------------------------------


def test_present_widget_carries_quality_scores() -> None:
    w = WidgetObservation(widget_key="WDG_X", present=True, ease=4, usability=5, depth=3)
    assert w.present and w.ease == 4


def test_non_present_widget_may_be_paywalled_or_defective() -> None:
    paywalled = WidgetObservation(
        widget_key="WDG_X", present=False, state=NonScoreState.PRESENT_PAYWALLED
    )
    defective = WidgetObservation(
        widget_key="WDG_Y", present=False, state=NonScoreState.PRESENT_DEFECTIVE
    )
    absent = WidgetObservation(widget_key="WDG_Z", present=False)
    assert paywalled.state is NonScoreState.PRESENT_PAYWALLED
    assert defective.state is NonScoreState.PRESENT_DEFECTIVE
    assert absent.state is None


def test_present_widget_rejects_a_non_score_state() -> None:
    with pytest.raises(ValidationError, match="present"):
        WidgetObservation(widget_key="WDG_X", present=True, state=NonScoreState.PRESENT_PAYWALLED)


def test_non_present_widget_rejects_quality_scores() -> None:
    with pytest.raises(ValidationError, match="not present"):
        WidgetObservation(widget_key="WDG_X", present=False, ease=3)


def test_non_present_widget_rejects_a_plain_not_assessed_state() -> None:
    with pytest.raises(ValidationError, match="PRESENT_PAYWALLED|PRESENT_DEFECTIVE"):
        WidgetObservation(widget_key="WDG_X", present=False, state=NonScoreState.NOT_ASSESSED)


def test_widget_scores_are_bounded_1_to_5() -> None:
    with pytest.raises(ValidationError):
        WidgetObservation(widget_key="WDG_X", present=True, ease=6)


# --- Round-trip persistence --------------------------------------------------------------


def test_document_round_trips_c_subcomponents_and_widgets() -> None:
    registry = _registry()
    doc = AssessmentDocument(
        subject="Round-trip",
        c_subcomponents=tuple(_rated_c_module(registry, "CUST_ONBOARDING")),
        widgets=(
            WidgetObservation(widget_key="WDG_A", present=True, ease=4, usability=4, depth=3),
            WidgetObservation(
                widget_key="WDG_B", present=False, state=NonScoreState.PRESENT_PAYWALLED
            ),
        ),
    )
    reloaded = AssessmentDocument.model_validate_json(doc.model_dump_json())
    assert reloaded == doc  # save → reload identical, widget rows and C ratings intact


def test_existing_documents_without_c_deserialise_unchanged() -> None:
    # Backward compatibility: a document persisted before GRS-0083 has no c_subcomponents/widgets.
    legacy = AssessmentDocument.model_validate({"subject": "Legacy"})
    assert legacy.c_subcomponents == ()
    assert legacy.widgets == ()


# --- Service: C completion + surfacing ---------------------------------------------------


def test_untouched_c_subcomponents_complete_to_not_assessed() -> None:
    registry = _registry()
    doc = AssessmentDocument(c_subcomponents=tuple(_rated_c_module(registry, "CUST_ONBOARDING")))
    completed = complete_c_subcomponents(doc, registry)
    by_key = {r.subcomponent_key: r for r in completed}
    # Exact C coverage; the untouched modules complete to Not Assessed, never zero-filled (D9).
    assert set(by_key) == registry.all_c_subcomponent_keys()
    untouched = registry.require_c_module("CUST_FEES_PRICING").subcomponents[0].key
    assert by_key[untouched].state is NonScoreState.NOT_ASSESSED
    assert by_key[untouched].level is None


def test_c_is_not_scoreable_until_a_critical_module_is_rated() -> None:
    registry = _registry()
    empty = AssessmentDocument()
    assert not c_scoreable(empty, registry)
    assert c_index_of(empty, registry) is None
    # A rating in a NON-critical-for-C module is not enough on its own.
    non_critical = AssessmentDocument(
        c_subcomponents=tuple(_rated_c_module(registry, "CUST_FEES_PRICING"))
    )
    assert not c_scoreable(non_critical, registry)


def test_c_is_reported_once_a_critical_module_is_rated() -> None:
    registry = _registry()
    doc = AssessmentDocument(c_subcomponents=tuple(_rated_c_module(registry, "CUST_ONBOARDING")))
    assert c_scoreable(doc, registry)
    c = c_index_of(doc, registry)
    assert c is not None and 0.0 <= c <= 1.0


def test_live_score_reports_c_alongside_v() -> None:
    registry = _registry()
    coeffs = active_coefficient_set(registry)
    model = active_uncertainty_model()
    doc = AssessmentDocument(c_subcomponents=tuple(_rated_c_module(registry, "CUST_ONBOARDING")))
    # C surfaces even while B/P/L is still blocked (no metrics/powers yet) — independent of V.
    result = live_score(doc, coeffs, registry, model, random.Random(7), draws=64)
    assert result.c is not None and 0.0 <= result.c <= 1.0
    assert not result.scoreable  # V is still blocked; C is reported regardless
