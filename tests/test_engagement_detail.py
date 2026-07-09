"""Engagement detail tests (GRS-0013, PRD §4).

An engagement ties one of the consultant's OWN contracted prospects to its finalised assessment(s),
a deliverables progress shell, and a communication log. These tests pin: it links only the owner's
own contracted prospect (cross-owner and not-contracted refused); comms entries round-trip in
chronological order; cross-owner access is refused everywhere (404); and the deliverable-slot
placeholder validates against a closed status set (forward-compatible for the Loop 4 builder).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from bcap_contracts.engagements import CommsChannel, DeliverableSlot, DeliverableStatus
from bcap_contracts.entities import PipelineStage
from pydantic import ValidationError

from grassmarket.data.repository import EngagementLinkError, Repository
from tests.conftest import SeededConsultant, auth_header
from tests.test_assessment_lifecycle import _body, _scoreable_partial_doc

# The legal stage path from Prospect to Contracted (GRS-0011 transition graph).
_TO_CONTRACTED = (
    PipelineStage.WORKSHOP_SCHEDULED,
    PipelineStage.WORKSHOP_DELIVERED,
    PipelineStage.QUALIFIED,
    PipelineStage.SCOPED,
    PipelineStage.CONTRACTED,
)


def _contracted_prospect_repo(repo: Repository, owner: SeededConsultant):
    prospect = repo.create_prospect(owner.principal, company_name="Acme")
    for stage in _TO_CONTRACTED:
        prospect = repo.update_prospect_stage(owner.principal, prospect.id, stage)
    return prospect


def _contracted_prospect_http(client, owner: SeededConsultant) -> str:
    pid = client.post(
        "/prospects", json={"company_name": "Acme"}, headers=auth_header(owner)
    ).json()["id"]
    for stage in _TO_CONTRACTED:
        client.patch(
            f"/prospects/{pid}/stage", json={"stage": stage.value}, headers=auth_header(owner)
        )
    return pid


def _finalised_assessment_http(client, owner: SeededConsultant) -> str:
    aid = client.post("/assessments", json={"subject": "S"}, headers=auth_header(owner)).json()[
        "id"
    ]
    client.put(
        f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(owner)
    )
    client.post(f"/assessments/{aid}/finalise", headers=auth_header(owner))
    return aid


# --------------------------------------- deliverable-slot placeholder (forward-compatible)
def test_deliverable_slot_validates_and_status_is_closed() -> None:
    slot = DeliverableSlot(key="diagnostic_pack", label="Diagnostic Pack")
    assert slot.status is DeliverableStatus.NOT_STARTED  # default; no content invented
    assert DeliverableSlot(key="k", status=DeliverableStatus.DRAFTED).status.value == "drafted"
    with pytest.raises(ValidationError):
        DeliverableSlot(key="k", status="teleported")  # unknown status refused (closed set)
    with pytest.raises(ValidationError):
        DeliverableSlot(key="")  # empty key refused


# ----------------------------------------------------- repository (link rules + comms ordering)
def test_engagement_links_contracted_prospect(repo: Repository, alice: SeededConsultant) -> None:
    prospect = _contracted_prospect_repo(repo, alice)
    engagement = repo.create_engagement(
        alice.principal,
        prospect_id=prospect.id,
        title="Modernisation",
        deliverables=(DeliverableSlot(key="roadmap"),),
    )
    assert engagement.prospect_id == prospect.id
    assert engagement.status.value == "contracted"
    assert engagement.deliverables[0].key == "roadmap"


def test_engagement_refuses_non_contracted_prospect(
    repo: Repository, alice: SeededConsultant
) -> None:
    prospect = repo.create_prospect(alice.principal, company_name="Acme")  # still at Prospect
    with pytest.raises(EngagementLinkError):
        repo.create_engagement(alice.principal, prospect_id=prospect.id, title="Too early")


def test_comms_log_round_trips_in_chronological_order(
    repo: Repository, alice: SeededConsultant
) -> None:
    prospect = _contracted_prospect_repo(repo, alice)
    engagement = repo.create_engagement(alice.principal, prospect_id=prospect.id, title="E")
    base = datetime(2026, 5, 1, 9, 0, tzinfo=UTC)
    # Append OUT of order; the log must come back sorted by `at`.
    repo.append_comms_entry(
        alice.principal,
        engagement.id,
        channel=CommsChannel.EMAIL,
        body="second",
        at=base + timedelta(hours=2),
    )
    repo.append_comms_entry(
        alice.principal, engagement.id, channel=CommsChannel.CALL, body="first", at=base
    )
    repo.append_comms_entry(
        alice.principal,
        engagement.id,
        channel=CommsChannel.NOTE,
        body="third",
        at=base + timedelta(hours=5),
    )
    detail = repo.get_engagement(alice.principal, engagement.id)
    assert [e.body for e in detail.comms_log] == ["first", "second", "third"]


# ----------------------------------------------------- HTTP surface + scoping
def test_http_create_links_finalised_assessment(client, alice: SeededConsultant) -> None:
    pid = _contracted_prospect_http(client, alice)
    aid = _finalised_assessment_http(client, alice)
    resp = client.post(
        "/engagements",
        json={"prospect_id": pid, "title": "Delivery", "assessment_ids": [aid]},
        headers=auth_header(alice),
    )
    assert resp.status_code == 201
    assert resp.json()["assessment_ids"] == [aid]


def test_http_refuses_unfinalised_assessment(client, alice: SeededConsultant) -> None:
    pid = _contracted_prospect_http(client, alice)
    draft = client.post("/assessments", json={"subject": "D"}, headers=auth_header(alice)).json()[
        "id"
    ]
    resp = client.post(
        "/engagements",
        json={"prospect_id": pid, "title": "Delivery", "assessment_ids": [draft]},
        headers=auth_header(alice),
    )
    assert resp.status_code == 409


def test_http_refuses_cross_owner_prospect(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    pid = _contracted_prospect_http(client, alice)
    # Bob cannot open an engagement against Alice's prospect — 404, no existence leak.
    resp = client.post(
        "/engagements", json={"prospect_id": pid, "title": "Nope"}, headers=auth_header(bob)
    )
    assert resp.status_code == 404


def test_http_comms_append_and_detail(client, alice: SeededConsultant) -> None:
    pid = _contracted_prospect_http(client, alice)
    eid = client.post(
        "/engagements", json={"prospect_id": pid, "title": "E"}, headers=auth_header(alice)
    ).json()["id"]
    for body in ("kickoff", "follow-up"):
        r = client.post(
            f"/engagements/{eid}/comms",
            json={"channel": "meeting", "body": body},
            headers=auth_header(alice),
        )
        assert r.status_code == 201
    detail = client.get(f"/engagements/{eid}", headers=auth_header(alice)).json()
    assert [e["body"] for e in detail["comms_log"]] == ["kickoff", "follow-up"]


def test_http_cross_owner_engagement_access_refused(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    pid = _contracted_prospect_http(client, alice)
    eid = client.post(
        "/engagements", json={"prospect_id": pid, "title": "E"}, headers=auth_header(alice)
    ).json()["id"]
    assert client.get(f"/engagements/{eid}", headers=auth_header(bob)).status_code == 404
    resp = client.post(
        f"/engagements/{eid}/comms",
        json={"channel": "note", "body": "sneaky"},
        headers=auth_header(bob),
    )
    assert resp.status_code == 404


def test_http_list_is_scoped(client, alice: SeededConsultant, bob: SeededConsultant) -> None:
    pid = _contracted_prospect_http(client, alice)
    client.post(
        "/engagements", json={"prospect_id": pid, "title": "Alice E"}, headers=auth_header(alice)
    )
    assert [e["title"] for e in client.get("/engagements", headers=auth_header(alice)).json()] == [
        "Alice E"
    ]
    assert client.get("/engagements", headers=auth_header(bob)).json() == []


def test_engagements_require_auth(client) -> None:
    assert client.get("/engagements").status_code == 401
