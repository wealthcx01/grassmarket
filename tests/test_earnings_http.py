"""Earnings over HTTP (GRS-0028). The commission maths is golden-mastered in tests/test_earnings.py;
here we pin the governance (advisor views own earnings; recording + payment are admin/finance only),
the scoping (self-only), the payment lifecycle, and the recovery-fee claim.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from grassmarket.data.models import RecoveryFeeAttributionORM
from tests.conftest import SeededConsultant, auth_header


def _record_payload(advisor_id: str, *, minor: int = 4_000_000) -> dict:
    return {
        "advisor_id": advisor_id,
        "engagement_id": str(uuid4()),
        "base_value_minor": minor,
        "currency": "GBP",
        "base_value_ref": "contract:acme-2026",
        "attribution": "self_sourced",
        "earned_on": "2026-03-01",
    }


def test_admin_records_a_commission_that_the_advisor_can_see(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    # Alice is a venture_associate; self-sourced = 1500 bps (15%). £40,000 → £6,000.
    resp = client.post(
        "/earnings/commissions",
        json=_record_payload(str(alice.stored.id)),
        headers=auth_header(admin),
    )
    assert resp.status_code == 201, resp.text
    line = resp.json()
    assert line["amount"]["amount_minor"] == 600_000
    assert line["payment_status"] == "pending"
    assert line["kind"] == "engagement"
    assert line["content_hash"]

    # Alice sees it in her own earnings and summary.
    mine = client.get("/earnings/commissions", headers=auth_header(alice)).json()
    assert [ln["id"] for ln in mine] == [line["id"]]
    summary = client.get("/earnings/summary", headers=auth_header(alice)).json()
    assert summary["pending"]["amount_minor"] == 600_000
    assert summary["ytd_earned"]["amount_minor"] == 600_000
    assert summary["projected_unpaid"]["amount_minor"] == 600_000


def test_recording_a_commission_is_admin_only(client, alice: SeededConsultant) -> None:
    # An advisor cannot record their own commission (objective money fact, never self-attested).
    resp = client.post(
        "/earnings/commissions",
        json=_record_payload(str(alice.stored.id)),
        headers=auth_header(alice),
    )
    assert resp.status_code == 403


def test_payment_status_advances_forward_only(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    line_id = client.post(
        "/earnings/commissions",
        json=_record_payload(str(alice.stored.id)),
        headers=auth_header(admin),
    ).json()["id"]

    # pending → invoiced → paid, one step at a time.
    for to_status in ("invoiced", "paid"):
        resp = client.post(
            f"/earnings/commissions/{line_id}/payment",
            json={"to_status": to_status},
            headers=auth_header(admin),
        )
        assert resp.status_code == 200
        assert resp.json()["payment_status"] == to_status

    # A backward move is refused.
    back = client.post(
        f"/earnings/commissions/{line_id}/payment",
        json={"to_status": "invoiced"},
        headers=auth_header(admin),
    )
    assert back.status_code == 409

    # And an advisor cannot advance their own payment status.
    forbidden = client.post(
        f"/earnings/commissions/{line_id}/payment",
        json={"to_status": "paid"},
        headers=auth_header(alice),
    )
    assert forbidden.status_code == 403


def test_a_skip_transition_is_refused(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    line_id = client.post(
        "/earnings/commissions",
        json=_record_payload(str(alice.stored.id)),
        headers=auth_header(admin),
    ).json()["id"]
    # pending → paid skips invoiced.
    resp = client.post(
        f"/earnings/commissions/{line_id}/payment",
        json={"to_status": "paid"},
        headers=auth_header(admin),
    )
    assert resp.status_code == 409


def test_commissions_are_self_scoped(
    client, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    client.post(
        "/earnings/commissions",
        json=_record_payload(str(alice.stored.id)),
        headers=auth_header(admin),
    )
    # Bob sees none of Alice's lines; his summary is zero.
    assert client.get("/earnings/commissions", headers=auth_header(bob)).json() == []
    assert (
        client.get("/earnings/summary", headers=auth_header(bob)).json()["pending"]["amount_minor"]
        == 0
    )


def test_an_advisor_downloads_their_statement(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    client.post(
        "/earnings/commissions",
        json=_record_payload(str(alice.stored.id)),
        headers=auth_header(admin),
    )
    resp = client.get("/earnings/statement", headers=auth_header(alice))
    assert resp.status_code == 200
    assert "wordprocessingml" in resp.headers["content-type"]
    assert len(resp.content) > 0


def _seed_recovery_fee(session_factory: sessionmaker[Session], owner_id) -> str:
    session = session_factory()
    try:
        row = RecoveryFeeAttributionORM(
            owner_consultant_id=owner_id,
            workshop_id=uuid4(),
            prospect_id=uuid4(),
            delivered_on=date(2026, 1, 1),
            contracted_on=date(2026, 6, 1),
            window_days=365,
            rate_ref="recovery-fees-v1:venture_associate",
            fee_amount_minor=500_000,
            fee_currency="GBP",
            fee_assumption_ref="recovery-fees-v1:venture_associate",
            content_hash="seed-hash",
        )
        session.add(row)
        session.commit()
        return str(row.id)
    finally:
        session.close()


def test_admin_claims_a_recovery_fee_once(
    client, admin: SeededConsultant, alice: SeededConsultant, session_factory
) -> None:
    attribution_id = _seed_recovery_fee(session_factory, alice.stored.id)

    resp = client.post(
        f"/earnings/recovery-fees/{attribution_id}/claim",
        json={"earned_on": "2026-06-02"},
        headers=auth_header(admin),
    )
    assert resp.status_code == 200, resp.text
    line = resp.json()
    assert line["kind"] == "workshop_recovery_fee"
    assert line["amount"]["amount_minor"] == 500_000

    # It shows up in Alice's earnings…
    assert any(
        ln["kind"] == "workshop_recovery_fee"
        for ln in client.get("/earnings/commissions", headers=auth_header(alice)).json()
    )
    # …and the same fee cannot be claimed twice.
    again = client.post(
        f"/earnings/recovery-fees/{attribution_id}/claim",
        json={"earned_on": "2026-06-02"},
        headers=auth_header(admin),
    )
    assert again.status_code == 409


def test_claiming_a_recovery_fee_is_admin_only(
    client, alice: SeededConsultant, session_factory
) -> None:
    attribution_id = _seed_recovery_fee(session_factory, alice.stored.id)
    resp = client.post(
        f"/earnings/recovery-fees/{attribution_id}/claim",
        json={"earned_on": "2026-06-02"},
        headers=auth_header(alice),
    )
    assert resp.status_code == 403


def test_the_seal_survives_a_payment_advance(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    line = client.post(
        "/earnings/commissions",
        json=_record_payload(str(alice.stored.id)),
        headers=auth_header(admin),
    ).json()
    advanced = client.post(
        f"/earnings/commissions/{line['id']}/payment",
        json={"to_status": "invoiced"},
        headers=auth_header(admin),
    ).json()
    # The financial seal is unchanged by a status change (payment_status is not part of the hash).
    assert advanced["payment_status"] == "invoiced"
    assert advanced["content_hash"] == line["content_hash"]


def test_earnings_endpoints_require_authentication(client, alice: SeededConsultant) -> None:
    assert client.get("/earnings/commissions").status_code == 401
    assert client.get("/earnings/summary").status_code == 401
    assert client.get("/earnings/statement").status_code == 401
    # The admin/finance mutations also require auth.
    assert client.post("/earnings/commissions", json={}).status_code == 401
    assert (
        client.post(
            f"/earnings/commissions/{uuid4()}/payment", json={"to_status": "paid"}
        ).status_code
        == 401
    )
