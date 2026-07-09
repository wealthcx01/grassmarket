"""Workshop + recovery-fee tests (GRS-0012, PRD §4).

Money enters this ticket; the ADR-0002 boundary is the whole risk. These tests pin: the fee is
`Money` (unconstructible without a currency + assumption ref); rates come from config (change the
config, change the fee — no code edit); the 12-month window is honoured at its exact edge;
attribution records are append-only, immutable, and content-hashed; and every workshop/fee read is
scoped to its owner. The AST guard (`test_money_and_adr0002`) — now scanning the pipeline tree —
keeps Score and Money in separate function signatures.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from bcap_contracts.common import ConsultantTier as Tier
from bcap_contracts.fees import (
    RecoveryFeeConfig,
    RecoveryFeeConfigError,
    load_recovery_fee_config,
)
from bcap_contracts.money import Currency, Money
from pydantic import ValidationError

from grassmarket.data.repository import (
    AttributionWindowExpired,
    ConflictError,
    Repository,
    WorkshopStateError,
)
from grassmarket.pipeline.fees import attribution_content_hash, is_within_attribution_window
from tests.conftest import SeededConsultant, auth_header

_DELIVERED = date(2026, 1, 10)


def _test_config(*, window: int = 365, advisor_minor: int = 750000) -> RecoveryFeeConfig:
    return RecoveryFeeConfig(
        version="test-fees",
        currency=Currency.GBP,
        attribution_window_days=window,
        tier_fees_minor={
            Tier.VENTURE_ASSOCIATE: 500000,
            Tier.ADVISOR: advisor_minor,
            Tier.CONSULTANT: 1000000,
        },
    )


# --------------------------------------------------------------- config (fail-loud, config-driven)
def test_config_loads_all_tiers() -> None:
    config = load_recovery_fee_config()
    assert set(config.tier_fees_minor) == set(Tier)
    assert config.attribution_window_days == 365


def test_incomplete_config_refuses() -> None:
    with pytest.raises(RecoveryFeeConfigError):
        RecoveryFeeConfig(
            version="broken",
            currency=Currency.GBP,
            attribution_window_days=365,
            tier_fees_minor={Tier.ADVISOR: 750000},  # missing other tiers
        )


def test_rates_come_from_config_not_code() -> None:
    # Change the config, change the fee — no code edit, no default.
    cheap = _test_config(advisor_minor=100000).fee_for(Tier.ADVISOR)
    dear = _test_config(advisor_minor=900000).fee_for(Tier.ADVISOR)
    assert cheap.amount_minor == 100000
    assert dear.amount_minor == 900000


# --------------------------------------------------------------- Money boundary (ADR-0002)
def test_fee_is_money_with_currency_and_ref() -> None:
    fee = _test_config().fee_for(Tier.ADVISOR)
    assert isinstance(fee, Money)
    assert fee.currency is Currency.GBP
    assert fee.assumption_register_ref == "test-fees:advisor"  # cites the config it derives from


def test_money_without_ref_refuses() -> None:
    with pytest.raises(ValidationError):
        Money(amount_minor=750000, currency=Currency.GBP, assumption_register_ref="")


# --------------------------------------------------------------- attribution window (boundary)
def test_window_boundary_inclusive() -> None:
    window = 365
    assert is_within_attribution_window(_DELIVERED, _DELIVERED, window) is True
    assert (
        is_within_attribution_window(_DELIVERED, _DELIVERED + timedelta(days=window), window)
        is True
    )
    # One day past the window is NOT eligible.
    assert (
        is_within_attribution_window(_DELIVERED, _DELIVERED + timedelta(days=window + 1), window)
        is False
    )
    # Contracting before delivery is never eligible.
    assert is_within_attribution_window(_DELIVERED, _DELIVERED - timedelta(days=1), window) is False


# --------------------------------------------------------------- immutability + hashing
def test_attribution_hash_is_deterministic_and_field_sensitive() -> None:
    fee = _test_config().fee_for(Tier.ADVISOR)
    import uuid

    wid, pid = uuid.uuid4(), uuid.uuid4()
    kw = dict(
        workshop_id=wid,
        prospect_id=pid,
        delivered_on=_DELIVERED,
        contracted_on=_DELIVERED + timedelta(days=30),
        window_days=365,
        rate_ref="test-fees:advisor",
        fee=fee,
    )
    h1 = attribution_content_hash(**kw)
    assert h1 == attribution_content_hash(**kw)  # deterministic
    # Any changed field changes the hash (tamper-evident).
    assert h1 != attribution_content_hash(
        **{**kw, "contracted_on": _DELIVERED + timedelta(days=31)}
    )


# --------------------------------------------------------------- repository (persistence + rules)
def _scheduled_and_delivered(
    repo: Repository, owner: SeededConsultant, *, delivered_on: date = _DELIVERED
):
    prospect = repo.create_prospect(owner.principal, company_name="Acme")
    workshop = repo.create_workshop(owner.principal, prospect_id=prospect.id)
    return repo.deliver_workshop(owner.principal, workshop.id, delivered_on=delivered_on)


def test_workshop_lifecycle(repo: Repository, alice: SeededConsultant) -> None:
    prospect = repo.create_prospect(alice.principal, company_name="Acme")
    workshop = repo.create_workshop(
        alice.principal, prospect_id=prospect.id, pre_workshop_brief="brief"
    )
    assert workshop.state.value == "scheduled"
    delivered = repo.deliver_workshop(
        alice.principal, workshop.id, delivered_on=_DELIVERED, workshop_output="output"
    )
    assert delivered.state.value == "delivered"
    assert delivered.delivered_on == _DELIVERED


def test_attribution_inside_window_is_recorded_and_immutable(
    repo: Repository, alice: SeededConsultant
) -> None:
    workshop = _scheduled_and_delivered(repo, alice)
    config = _test_config()
    attribution = repo.record_recovery_fee_attribution(
        alice.principal, workshop.id, contracted_on=_DELIVERED + timedelta(days=100), config=config
    )
    assert attribution.fee.amount_minor == config.fee_for(alice.stored.tier).amount_minor
    # The content hash recomputes from the stored fields — the immutability seal.
    assert attribution.content_hash == attribution_content_hash(
        workshop_id=attribution.workshop_id,
        prospect_id=attribution.prospect_id,
        delivered_on=attribution.delivered_on,
        contracted_on=attribution.contracted_on,
        window_days=attribution.window_days,
        rate_ref=attribution.rate_ref,
        fee=attribution.fee,
    )
    # Append-only: a second attribution for the same workshop is refused.
    with pytest.raises(ConflictError):
        repo.record_recovery_fee_attribution(
            alice.principal,
            workshop.id,
            contracted_on=_DELIVERED + timedelta(days=101),
            config=config,
        )


def test_attribution_outside_window_refused(repo: Repository, alice: SeededConsultant) -> None:
    workshop = _scheduled_and_delivered(repo, alice)
    config = _test_config(window=365)
    with pytest.raises(AttributionWindowExpired):
        repo.record_recovery_fee_attribution(
            alice.principal,
            workshop.id,
            contracted_on=_DELIVERED + timedelta(days=366),
            config=config,
        )


def test_attribution_requires_delivered_workshop(repo: Repository, alice: SeededConsultant) -> None:
    prospect = repo.create_prospect(alice.principal, company_name="Acme")
    workshop = repo.create_workshop(
        alice.principal, prospect_id=prospect.id
    )  # scheduled, not delivered
    with pytest.raises(WorkshopStateError):
        repo.record_recovery_fee_attribution(
            alice.principal, workshop.id, contracted_on=_DELIVERED, config=_test_config()
        )


# --------------------------------------------------------------- scoping (404 across owners)
def test_cross_owner_workshop_access_refused_http(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    prospect = client.post(
        "/prospects", json={"company_name": "Alice Co"}, headers=auth_header(alice)
    ).json()
    workshop = client.post(
        "/workshops", json={"prospect_id": prospect["id"]}, headers=auth_header(alice)
    ).json()
    # Bob must not learn the workshop exists.
    assert client.get(f"/workshops/{workshop['id']}", headers=auth_header(bob)).status_code == 404
    resp = client.post(
        f"/workshops/{workshop['id']}/deliver",
        json={"delivered_on": "2026-01-10"},
        headers=auth_header(bob),
    )
    assert resp.status_code == 404


def test_recovery_fee_flow_http_and_scoping(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    prospect = client.post(
        "/prospects", json={"company_name": "Alice Co"}, headers=auth_header(alice)
    ).json()
    workshop = client.post(
        "/workshops", json={"prospect_id": prospect["id"]}, headers=auth_header(alice)
    ).json()
    client.post(
        f"/workshops/{workshop['id']}/deliver",
        json={"delivered_on": "2026-01-10"},
        headers=auth_header(alice),
    )
    # Inside window → 201.
    created = client.post(
        f"/workshops/{workshop['id']}/recovery-fee",
        json={"contracted_on": "2026-06-10"},
        headers=auth_header(alice),
    )
    assert created.status_code == 201
    assert created.json()["fee"]["currency"] == "GBP"

    # Alice sees her fee; Bob sees none (scoped).
    assert len(client.get("/recovery-fees", headers=auth_header(alice)).json()) == 1
    assert client.get("/recovery-fees", headers=auth_header(bob)).json() == []
    # Bob cannot attribute against Alice's workshop — 404.
    assert (
        client.post(
            f"/workshops/{workshop['id']}/recovery-fee",
            json={"contracted_on": "2026-06-10"},
            headers=auth_header(bob),
        ).status_code
        == 404
    )


def test_http_out_of_window_is_409(client, alice: SeededConsultant) -> None:
    prospect = client.post(
        "/prospects", json={"company_name": "Alice Co"}, headers=auth_header(alice)
    ).json()
    workshop = client.post(
        "/workshops", json={"prospect_id": prospect["id"]}, headers=auth_header(alice)
    ).json()
    client.post(
        f"/workshops/{workshop['id']}/deliver",
        json={"delivered_on": "2026-01-10"},
        headers=auth_header(alice),
    )
    # 2028 is well beyond the 365-day config window → 409.
    resp = client.post(
        f"/workshops/{workshop['id']}/recovery-fee",
        json={"contracted_on": "2028-06-10"},
        headers=auth_header(alice),
    )
    assert resp.status_code == 409
