"""Prediction register + validation loop + anonymised benchmark (GRS-0031).

Golden-master the Brier/hit-miss scorer, prove a due follow-up round-trips to a scored outcome, and
prove the benchmark rows are de-identified — no client identity, owner, or run link survives.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from bcap_contracts.money import Currency, Money
from bcap_contracts.predictions import BenchmarkRow, BenchmarkSector, PredictionOutcome
from bcap_contracts.value import LeverKind, LeverValuation

from grassmarket.data.repository import ConflictError, Repository, ScopeViolationError
from grassmarket.predictions.logic import predictions_from_levers, score_prediction
from tests.conftest import SeededConsultant
from tests.test_scoring_run_persistence import _create

_NOW = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)


def _gbp(minor: int, ref: str = "lever:test") -> Money:
    return Money(amount_minor=minor, currency=Currency.GBP, assumption_register_ref=ref)


def _levers() -> list[LeverValuation]:
    return [
        LeverValuation(
            lever=LeverKind.COST_TO_SERVE, npv=_gbp(10_000_000), assumption_refs=("a1",)
        ),
        LeverValuation(
            lever=LeverKind.REVENUE_ENABLEMENT, npv=_gbp(5_000_000), assumption_refs=("a2",)
        ),
    ]


# --- Extraction + scoring (pure) -----------------------------------------------------------


def test_predictions_are_extracted_one_per_lever() -> None:
    specs = predictions_from_levers(_levers())
    assert [s.lever for s in specs] == [LeverKind.COST_TO_SERVE, LeverKind.REVENUE_ENABLEMENT]
    assert specs[0].predicted_delta.amount_minor == 10_000_000


@pytest.mark.parametrize(
    ("predicted", "realised", "prob", "outcome", "brier"),
    [
        # predicted +£100k, realised +£120k, p=0.8 → HIT, (0.8-1)² = 0.04
        (10_000_000, 12_000_000, 0.8, PredictionOutcome.HIT, 0.04),
        # predicted +£100k, realised −£50k, p=0.8 → MISS, (0.8-0)² = 0.64
        (10_000_000, -5_000_000, 0.8, PredictionOutcome.MISS, 0.64),
        # predicted −£100k (a reduction) realised −£80k, p=0.6 → HIT, (0.6-1)² = 0.16
        (-10_000_000, -8_000_000, 0.6, PredictionOutcome.HIT, 0.16),
        # realised exactly zero → no directional move → MISS
        (10_000_000, 0, 0.5, PredictionOutcome.MISS, 0.25),
    ],
)
def test_score_prediction_golden(predicted, realised, prob, outcome, brier) -> None:
    got_outcome, got_brier = score_prediction(
        predicted_delta=_gbp(predicted), realised_delta=_gbp(realised), probability=prob
    )
    assert got_outcome is outcome
    assert got_brier == pytest.approx(brier)


def test_score_prediction_refuses_cross_currency() -> None:
    usd = Money(amount_minor=1, currency=Currency.USD, assumption_register_ref="x")
    with pytest.raises(ValueError, match="no silent FX"):
        score_prediction(predicted_delta=_gbp(1), realised_delta=usd, probability=0.5)


# --- Register → due follow-up → scored outcome (round trip) --------------------------------


def test_a_due_follow_up_round_trips_to_a_scored_outcome(
    repo: Repository, alice: SeededConsultant
) -> None:
    run = _create(repo, alice)
    predictions = repo.register_predictions(
        alice.principal,
        scoring_run_id=run.id,
        specs=predictions_from_levers(_levers()),
        horizon_months=12,
        probability=0.8,
        follow_up_due=date(2026, 1, 1),  # in the past → due
    )
    assert len(predictions) == 2
    assert all(p.outcome is PredictionOutcome.PENDING for p in predictions)

    # The follow-up is due (past date, still pending).
    due = repo.list_due_follow_ups(alice.principal, now=_NOW)
    assert {p.id for p in due} == {p.id for p in predictions}

    # Record the realised value on the first — it scores and leaves the due queue.
    scored = repo.record_realised_value(
        alice.principal, predictions[0].id, realised_delta=_gbp(12_000_000), now=_NOW
    )
    assert scored.outcome is PredictionOutcome.HIT
    assert scored.brier_score == pytest.approx(0.04)
    assert scored.scored_at == _NOW
    remaining = repo.list_due_follow_ups(alice.principal, now=_NOW)
    assert predictions[0].id not in {p.id for p in remaining}


def test_recording_a_realised_value_is_single_shot(
    repo: Repository, alice: SeededConsultant
) -> None:
    run = _create(repo, alice)
    pred = repo.register_predictions(
        alice.principal,
        scoring_run_id=run.id,
        specs=predictions_from_levers(_levers()[:1]),
        horizon_months=12,
        probability=0.5,
        follow_up_due=date(2026, 1, 1),
    )[0]
    repo.record_realised_value(alice.principal, pred.id, realised_delta=_gbp(1), now=_NOW)
    with pytest.raises(ConflictError, match="already been scored"):
        repo.record_realised_value(alice.principal, pred.id, realised_delta=_gbp(1), now=_NOW)


def test_predictions_are_owner_scoped(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    run = _create(repo, alice)
    pred = repo.register_predictions(
        alice.principal,
        scoring_run_id=run.id,
        specs=predictions_from_levers(_levers()[:1]),
        horizon_months=12,
        probability=0.5,
        follow_up_due=date(2026, 1, 1),
    )[0]
    with pytest.raises(ScopeViolationError):
        repo.get_prediction(bob.principal, pred.id)
    assert repo.list_predictions(bob.principal) == []


# --- Anonymised benchmark ingestion --------------------------------------------------------

_IDENTIFYING_FIELDS = {
    "owner_consultant_id",
    "assessment_id",
    "scoring_run_id",
    "content_hash",
    "company_name",
    "name",
    "entity_id",
    "primary_contact_name",
    "primary_contact_email",
}


def test_benchmark_row_contract_carries_no_identifier() -> None:
    # Structural guarantee: the anonymised row simply has no field that could re-identify anyone.
    assert _IDENTIFYING_FIELDS.isdisjoint(set(BenchmarkRow.model_fields))


def test_ingesting_a_finalised_run_is_anonymised(repo: Repository, alice: SeededConsultant) -> None:
    run = _create(repo, alice)
    repo.finalise_scoring_run(alice.principal, run.id)
    row = repo.ingest_benchmark(alice.principal, run.id, sector=BenchmarkSector.BROKERAGE, now=_NOW)

    assert row.v_index == run.v_index
    assert row.methodology_version == run.methodology_version
    assert row.sector is BenchmarkSector.BROKERAGE
    # Provable de-identification: no identifying key, and none of the run's identifiers, appear.
    dumped = row.model_dump()
    assert _IDENTIFYING_FIELDS.isdisjoint(set(dumped))
    for identifier in (str(alice.principal.consultant_id), str(run.assessment_id), str(run.id)):
        assert identifier not in str(dumped)

    # And it is readable as part of the org-wide anonymised population.
    assert row.id in {r.id for r in repo.list_benchmark_rows()}


def test_only_a_finalised_run_may_enter_the_benchmark(
    repo: Repository, alice: SeededConsultant
) -> None:
    run = _create(repo, alice)  # not finalised
    with pytest.raises(ConflictError, match="finalised"):
        repo.ingest_benchmark(alice.principal, run.id, sector=None, now=_NOW)
