"""Pipeline lifecycle tests (GRS-0011, PRD §4).

The stage machine refuses illegal jumps; time-in-stage flags are computed against an injected
``now`` (deterministic); the deal-volume forecast is probability-weighted and currency-free; the
config is complete or it refuses to load; and every pipeline read is scoped to its owner.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from bcap_contracts.entities import PipelineStage, Prospect
from bcap_contracts.pipeline import (
    IllegalStageTransition,
    PipelineConfig,
    PipelineConfigError,
    PipelineStageParams,
    assert_legal_transition,
    is_legal_transition,
    load_pipeline_config,
)

from grassmarket.data.repository import Repository
from grassmarket.pipeline import build_board, build_forecast, days_in_stage
from tests.conftest import SeededConsultant, auth_header

_NOW = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


def _prospect(stage: PipelineStage, *, entered: datetime) -> Prospect:
    return Prospect(
        id=uuid.uuid4(),
        owner_consultant_id=uuid.uuid4(),
        company_name="Acme",
        stage=stage,
        stage_entered_at=entered,
        created_at=_NOW,
        updated_at=_NOW,
    )


# ------------------------------------------------------------------ transition graph
def test_forward_transition_is_legal() -> None:
    assert is_legal_transition(PipelineStage.PROSPECT, PipelineStage.WORKSHOP_SCHEDULED)
    assert_legal_transition(PipelineStage.CONTRACTED, PipelineStage.ACTIVE)  # no raise


def test_skip_ahead_is_illegal() -> None:
    with pytest.raises(IllegalStageTransition):
        assert_legal_transition(PipelineStage.PROSPECT, PipelineStage.CONTRACTED)


def test_same_stage_is_illegal() -> None:
    # A no-op "transition" is refused so a caller can't mask a bug as a successful move.
    assert not is_legal_transition(PipelineStage.QUALIFIED, PipelineStage.QUALIFIED)
    with pytest.raises(IllegalStageTransition):
        assert_legal_transition(PipelineStage.QUALIFIED, PipelineStage.QUALIFIED)


def test_off_ramps_and_reengagement() -> None:
    assert is_legal_transition(PipelineStage.SCOPED, PipelineStage.CLOSED)
    assert is_legal_transition(PipelineStage.QUALIFIED, PipelineStage.NURTURE)
    assert is_legal_transition(PipelineStage.NURTURE, PipelineStage.PROSPECT)
    # Closed re-opens only into Nurture, never mid-funnel.
    assert is_legal_transition(PipelineStage.CLOSED, PipelineStage.NURTURE)
    assert not is_legal_transition(PipelineStage.CLOSED, PipelineStage.QUALIFIED)


# ------------------------------------------------------------------ config (fail-loud)
def test_config_loads_all_ten_stages() -> None:
    config = load_pipeline_config()
    assert set(config.stages) == set(PipelineStage)
    assert 0.0 <= config.params(PipelineStage.PROSPECT).close_probability <= 1.0


def test_incomplete_config_refuses() -> None:
    with pytest.raises(PipelineConfigError):
        PipelineConfig(
            version="broken",
            stages={
                PipelineStage.PROSPECT: PipelineStageParams(
                    close_probability=0.1, stale_after_days=10
                )
            },
        )


# ------------------------------------------------------------------ time-in-stage flags
def test_days_in_stage_and_stale_flag() -> None:
    config = load_pipeline_config()
    fresh = _prospect(PipelineStage.PROSPECT, entered=_NOW - timedelta(days=3))
    stale = _prospect(PipelineStage.PROSPECT, entered=_NOW - timedelta(days=40))

    assert days_in_stage(fresh, _NOW) == 3
    board = build_board([fresh, stale], config, _NOW)
    by_id = {e.prospect.id: e for e in board.entries}
    assert by_id[fresh.id].stale is False
    assert by_id[stale.id].stale is True  # 40 days > prospect stale_after_days (21)
    assert board.generated_at == _NOW


# ------------------------------------------------------------------ forecast (currency-free)
def test_forecast_is_probability_weighted() -> None:
    config = load_pipeline_config()
    prospects = [
        _prospect(PipelineStage.PROSPECT, entered=_NOW),
        _prospect(PipelineStage.PROSPECT, entered=_NOW),
        _prospect(PipelineStage.CONTRACTED, entered=_NOW),
        _prospect(PipelineStage.CLOSED, entered=_NOW),
    ]
    forecast = build_forecast(prospects, config, _NOW)

    p = config.params(PipelineStage.PROSPECT).close_probability
    c = config.params(PipelineStage.CONTRACTED).close_probability
    assert forecast.total_prospects == 4
    assert forecast.open_prospects == 3  # Closed is terminal
    assert forecast.weighted_expected_deals == pytest.approx(2 * p + c)  # Closed contributes 0
    by_stage = {s.stage: s for s in forecast.stages}
    assert by_stage[PipelineStage.PROSPECT].count == 2
    assert len(forecast.stages) == len(PipelineStage)  # every stage represented


# -------------------------------------------------------------- repository (persistence + reset)
def test_create_sets_stage_entered_at(repo: Repository, alice: SeededConsultant) -> None:
    prospect = repo.create_prospect(alice.principal, company_name="Acme")
    assert prospect.stage is PipelineStage.PROSPECT
    assert prospect.stage_entered_at is not None


def test_legal_transition_resets_stage_clock(repo: Repository, alice: SeededConsultant) -> None:
    prospect = repo.create_prospect(alice.principal, company_name="Acme")
    moved = repo.update_prospect_stage(
        alice.principal, prospect.id, PipelineStage.WORKSHOP_SCHEDULED
    )
    assert moved.stage is PipelineStage.WORKSHOP_SCHEDULED
    assert moved.stage_entered_at >= prospect.stage_entered_at


def test_illegal_transition_refused_in_repository(
    repo: Repository, alice: SeededConsultant
) -> None:
    prospect = repo.create_prospect(alice.principal, company_name="Acme")
    with pytest.raises(IllegalStageTransition):
        repo.update_prospect_stage(alice.principal, prospect.id, PipelineStage.ACTIVE)


# ------------------------------------------------------------------ HTTP surface
def test_http_illegal_transition_is_409(client, alice: SeededConsultant) -> None:
    created = client.post("/prospects", json={"company_name": "Acme"}, headers=auth_header(alice))
    pid = created.json()["id"]
    resp = client.patch(
        f"/prospects/{pid}/stage", json={"stage": "contracted"}, headers=auth_header(alice)
    )
    assert resp.status_code == 409


def test_http_legal_transition_is_200(client, alice: SeededConsultant) -> None:
    created = client.post("/prospects", json={"company_name": "Acme"}, headers=auth_header(alice))
    pid = created.json()["id"]
    resp = client.patch(
        f"/prospects/{pid}/stage", json={"stage": "workshop_scheduled"}, headers=auth_header(alice)
    )
    assert resp.status_code == 200
    assert resp.json()["stage"] == "workshop_scheduled"


def test_http_board_and_forecast_are_scoped(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    client.post("/prospects", json={"company_name": "Alice Co"}, headers=auth_header(alice))
    client.post("/prospects", json={"company_name": "Bob Co 1"}, headers=auth_header(bob))
    client.post("/prospects", json={"company_name": "Bob Co 2"}, headers=auth_header(bob))

    alice_board = client.get("/pipeline/board", headers=auth_header(alice)).json()
    assert [e["prospect"]["company_name"] for e in alice_board["entries"]] == ["Alice Co"]

    bob_forecast = client.get("/pipeline/forecast", headers=auth_header(bob)).json()
    assert bob_forecast["total_prospects"] == 2


def test_http_cross_owner_stage_update_is_404(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    created = client.post(
        "/prospects", json={"company_name": "Alice Co"}, headers=auth_header(alice)
    )
    pid = created.json()["id"]
    # Bob must not even learn it exists — 404, not 403 or 409.
    resp = client.patch(
        f"/prospects/{pid}/stage", json={"stage": "workshop_scheduled"}, headers=auth_header(bob)
    )
    assert resp.status_code == 404


def test_pipeline_endpoints_require_auth(client) -> None:
    assert client.get("/pipeline/board").status_code == 401
    assert client.get("/pipeline/forecast").status_code == 401
