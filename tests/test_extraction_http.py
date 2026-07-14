"""Path B extraction over HTTP (GRS-0030). The identical-scores crux is proven at the repository
level in tests/test_extraction.py; here we pin the wiring (propose → provenance → confirm) and the
owner-scoping (a foreign extraction is a 404). The HTTP propose uses the offline EmptyExtractor.
"""

from __future__ import annotations

from tests.conftest import SeededConsultant, auth_header


def _assessment_and_transcript(client, owner: SeededConsultant) -> tuple[str, str]:
    aid = client.post(
        "/assessments", json={"subject": "Meridian"}, headers=auth_header(owner)
    ).json()["id"]
    tid = client.post(
        "/transcripts/text",
        json={"text": "a discovery conversation", "source_filename": "call.txt"},
        headers=auth_header(owner),
    ).json()["id"]
    return aid, tid


def test_propose_then_confirm_round_trips(client, alice: SeededConsultant) -> None:
    aid, tid = _assessment_and_transcript(client, alice)
    proposed = client.post(
        "/extractions",
        json={"assessment_id": aid, "transcript_id": tid},
        headers=auth_header(alice),
    )
    assert proposed.status_code == 201, proposed.text
    ext = proposed.json()
    assert ext["status"] == "proposed"
    assert ext["transcript_id"] == tid
    # The offline extractor proposes nothing (real extraction is AI) — everything is a gap.
    assert ext["gaps"] == ["all"]

    confirmed = client.post(
        f"/extractions/{ext['id']}/confirm", json={}, headers=auth_header(alice)
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"

    # A second confirm is refused.
    assert (
        client.post(
            f"/extractions/{ext['id']}/confirm", json={}, headers=auth_header(alice)
        ).status_code
        == 409
    )


def test_provenance_endpoint_returns_the_audit_trail(client, alice: SeededConsultant) -> None:
    aid, tid = _assessment_and_transcript(client, alice)
    ext_id = client.post(
        "/extractions",
        json={"assessment_id": aid, "transcript_id": tid},
        headers=auth_header(alice),
    ).json()["id"]
    prov = client.get(f"/extractions/{ext_id}/provenance", headers=auth_header(alice))
    assert prov.status_code == 200
    assert prov.json() == []  # EmptyExtractor emits no fields


def test_extraction_is_owner_scoped_over_http(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    aid, tid = _assessment_and_transcript(client, alice)
    ext_id = client.post(
        "/extractions",
        json={"assessment_id": aid, "transcript_id": tid},
        headers=auth_header(alice),
    ).json()["id"]
    assert client.get(f"/extractions/{ext_id}", headers=auth_header(bob)).status_code == 404
    assert (
        client.post(f"/extractions/{ext_id}/confirm", json={}, headers=auth_header(bob)).status_code
        == 404
    )


def test_extraction_endpoints_require_authentication(client) -> None:
    from uuid import uuid4

    assert client.post("/extractions", json={}).status_code == 401
    assert client.get(f"/extractions/{uuid4()}").status_code == 401
    assert client.post(f"/extractions/{uuid4()}/confirm", json={}).status_code == 401
