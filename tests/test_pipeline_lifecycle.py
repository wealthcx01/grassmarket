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
    WinProbabilityBand,
    WinProbabilityConfig,
    WinProbabilitySignals,
    assert_legal_transition,
    is_legal_transition,
    load_pipeline_config,
)

from grassmarket.data.repository import NotFoundError, Repository, ScopeViolationError
from grassmarket.pipeline import build_board, build_forecast, days_in_stage
from tests.conftest import SeededConsultant, auth_header

_NOW = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)

# A minimal-but-valid win-probability config for inline PipelineConfig construction (the loaded
# one is what production uses; this just satisfies the required field in unit tests).
_WIN_PROB = WinProbabilityConfig(
    version="test",
    signals=WinProbabilitySignals(
        has_primary_contact=0.05,
        has_contact_email=0.05,
        has_sector=0.03,
        has_notes=0.02,
        stale_penalty=-0.10,
    ),
    bands=(
        WinProbabilityBand(min_probability=0.5, label="High"),
        WinProbabilityBand(min_probability=0.0, label="Low"),
    ),
)


def _prospect(
    stage: PipelineStage,
    *,
    entered: datetime,
    sector: str | None = None,
    primary_contact_name: str | None = None,
    primary_contact_email: str | None = None,
    notes: str | None = None,
) -> Prospect:
    return Prospect(
        id=uuid.uuid4(),
        owner_consultant_id=uuid.uuid4(),
        company_name="Acme",
        stage=stage,
        stage_entered_at=entered,
        sector=sector,
        primary_contact_name=primary_contact_name,
        primary_contact_email=primary_contact_email,
        notes=notes,
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
            win_probability=_WIN_PROB,
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


# ------------------------------------------------------------------ win-probability (GRS-0111)
def _config() -> PipelineConfig:
    return load_pipeline_config()


def test_win_probability_config_loads() -> None:
    wp = _config().win_probability
    assert wp.signals.stale_penalty < 0  # a stale prospect is penalised
    assert min(b.min_probability for b in wp.bands) == 0.0  # a 0-anchored floor (fail-loud)
    assert wp.band_for(0.0) == "Cold"
    assert wp.band_for(0.95) == "Strong"


def test_win_probability_starts_from_stage_base() -> None:
    from grassmarket.pipeline.win_probability import score_win_probability

    config = _config()
    bare = _prospect(PipelineStage.PROSPECT, entered=_NOW)  # no contact/sector/notes
    wp = score_win_probability(bare, stale=False, config=config)
    # 10% base, nothing to add → 10.
    assert wp.score == 10
    assert wp.label == "Cold"
    # Everything is missing, so it is all surfaced as fillable gaps.
    assert len(wp.missing_info) == 4


def test_win_probability_completeness_raises_score() -> None:
    from grassmarket.pipeline.win_probability import score_win_probability

    config = _config()
    full = _prospect(
        PipelineStage.QUALIFIED,  # 55% base
        entered=_NOW,
        sector="Wealth",
        primary_contact_name="Jo",
        primary_contact_email="jo@x.com",
        notes="Keen.",
    )
    wp = score_win_probability(full, stale=False, config=config)
    # 55 + 5 + 5 + 3 + 2 = 70.
    assert wp.score == 70
    assert wp.missing_info == ()
    assert wp.label == "Likely"


def test_win_probability_stale_penalty_applies() -> None:
    from grassmarket.pipeline.win_probability import score_win_probability

    config = _config()
    p = _prospect(PipelineStage.QUALIFIED, entered=_NOW)  # 55% base, no signals
    fresh = score_win_probability(p, stale=False, config=config)
    stale = score_win_probability(p, stale=True, config=config)
    assert stale.score == fresh.score - 10  # −10pp stale penalty
    assert any("Stale" in r for r in stale.reasons)


def test_win_probability_settled_stages_ignore_signals() -> None:
    from grassmarket.pipeline.win_probability import score_win_probability

    config = _config()
    # A closed deal is 0 regardless of how complete the record is; a won (active) deal is 100.
    closed = _prospect(
        PipelineStage.CLOSED, entered=_NOW, sector="X", primary_contact_name="Y", notes="Z"
    )
    won = _prospect(PipelineStage.ACTIVE, entered=_NOW)
    assert score_win_probability(closed, stale=True, config=config).score == 0
    assert score_win_probability(closed, stale=True, config=config).missing_info == ()
    assert score_win_probability(won, stale=False, config=config).score == 100


def test_board_entries_carry_win_probability() -> None:
    config = _config()
    board = build_board([_prospect(PipelineStage.PROSPECT, entered=_NOW)], config, _NOW)
    assert board.entries[0].win_probability.score == 10


# ------------------------------------------------------------------ stage history (GRS-0111)
def test_creation_writes_a_history_row(repo: Repository, alice: SeededConsultant) -> None:
    prospect = repo.create_prospect(alice.principal, company_name="Acme")
    history = repo.list_stage_history(alice.principal, prospect.id)
    assert len(history) == 1
    assert history[0].from_stage is None  # the creation row
    assert history[0].to_stage is PipelineStage.PROSPECT


def test_transition_appends_history_in_order(repo: Repository, alice: SeededConsultant) -> None:
    prospect = repo.create_prospect(alice.principal, company_name="Acme")
    repo.update_prospect_stage(alice.principal, prospect.id, PipelineStage.WORKSHOP_SCHEDULED)
    repo.update_prospect_stage(alice.principal, prospect.id, PipelineStage.WORKSHOP_DELIVERED)
    history = repo.list_stage_history(alice.principal, prospect.id)
    assert [(h.from_stage, h.to_stage) for h in history] == [
        (None, PipelineStage.PROSPECT),
        (PipelineStage.PROSPECT, PipelineStage.WORKSHOP_SCHEDULED),
        (PipelineStage.WORKSHOP_SCHEDULED, PipelineStage.WORKSHOP_DELIVERED),
    ]


def test_stage_history_is_owner_scoped(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    prospect = repo.create_prospect(alice.principal, company_name="Alice Co")
    with pytest.raises((NotFoundError, ScopeViolationError)):
        repo.list_stage_history(bob.principal, prospect.id)


def test_http_stage_history_is_scoped(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    created = client.post(
        "/prospects", json={"company_name": "Alice Co"}, headers=auth_header(alice)
    )
    pid = created.json()["id"]
    client.patch(
        f"/prospects/{pid}/stage", json={"stage": "workshop_scheduled"}, headers=auth_header(alice)
    )
    owner_view = client.get(f"/prospects/{pid}/history", headers=auth_header(alice))
    assert owner_view.status_code == 200
    assert len(owner_view.json()) == 2  # creation + one move
    # Bob can't see it exists.
    assert client.get(f"/prospects/{pid}/history", headers=auth_header(bob)).status_code == 404


def test_pipeline_endpoints_require_auth(client) -> None:
    assert client.get("/pipeline/board").status_code == 401
    assert client.get("/pipeline/forecast").status_code == 401
