"""Path B ingestion over HTTP (GRS-0029). A pasted transcript and an uploaded audio fixture both
yield stored, scoped transcripts; the text is encrypted at rest; a cross-owner read is a 404.
"""

from __future__ import annotations

import base64

from sqlalchemy.orm import Session, sessionmaker

from grassmarket.data.models import MeetingTranscriptORM
from tests.conftest import SeededConsultant, auth_header


def test_a_pasted_transcript_is_stored_and_read_back(client, alice: SeededConsultant) -> None:
    resp = client.post(
        "/transcripts/text",
        json={"text": "Client said their moat is switching costs.", "source_filename": "notes.txt"},
        headers=auth_header(alice),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["source_kind"] == "transcript_text"
    assert body["transcriber_ref"] == "pasted"
    assert body["text"] == "Client said their moat is switching costs."

    fetched = client.get(f"/transcripts/{body['id']}", headers=auth_header(alice)).json()
    assert fetched["text"] == "Client said their moat is switching costs."


def test_an_uploaded_audio_fixture_is_transcribed_and_stored(
    client, alice: SeededConsultant
) -> None:
    media = base64.b64encode(b"the whole discovery conversation").decode()
    resp = client.post(
        "/transcripts/media",
        json={
            "media_base64": media,
            "source_filename": "call.wav",
            "content_type": "audio/wav",
            "source_kind": "audio",
        },
        headers=auth_header(alice),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["source_kind"] == "audio"
    # The offline echo transcriber returns the decoded text.
    assert body["text"] == "the whole discovery conversation"
    assert body["transcriber_ref"] == "echo-transcriber-v1"


def test_the_transcript_is_encrypted_at_rest(
    client, alice: SeededConsultant, session_factory: sessionmaker[Session]
) -> None:
    secret = "Highly confidential board discussion."
    tid = client.post(
        "/transcripts/text",
        json={"text": secret, "source_filename": "board.txt"},
        headers=auth_header(alice),
    ).json()["id"]

    # Straight from the database: the stored bytes are ciphertext, not the plaintext.
    session = session_factory()
    try:
        from uuid import UUID

        row = session.get(MeetingTranscriptORM, UUID(tid))
        assert row is not None
        assert secret.encode("utf-8") not in row.text_ciphertext
        assert row.text_ciphertext != secret.encode("utf-8")
    finally:
        session.close()


def test_a_transcript_is_owner_scoped(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    tid = client.post(
        "/transcripts/text",
        json={"text": "alice's private meeting", "source_filename": "a.txt"},
        headers=auth_header(alice),
    ).json()["id"]
    # Bob cannot read Alice's transcript, and it is not in his list.
    assert client.get(f"/transcripts/{tid}", headers=auth_header(bob)).status_code == 404
    assert client.get("/transcripts", headers=auth_header(bob)).json() == []


def _own_engagement_id(client, owner: SeededConsultant) -> str:
    """A contracted prospect → an engagement owned by `owner`, over HTTP."""
    from tests.test_engagement_detail import _contracted_prospect_http

    pid = _contracted_prospect_http(client, owner)
    return client.post(
        "/engagements", json={"prospect_id": pid, "title": "Eng"}, headers=auth_header(owner)
    ).json()["id"]


def test_transcript_engagement_link_is_scoped(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    """GRS-0052: a transcript may be attached only to the caller's own engagement. A missing or
    cross-owner engagement_id is refused (404), never stored as a dangling/foreign reference."""
    from uuid import uuid4

    # Alice's own engagement links fine and is recorded.
    eid = _own_engagement_id(client, alice)
    ok = client.post(
        "/transcripts/text",
        json={"text": "note", "source_filename": "n.txt", "engagement_id": eid},
        headers=auth_header(alice),
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()["engagement_id"] == eid

    # A non-existent engagement → 404.
    ghost = client.post(
        "/transcripts/text",
        json={"text": "n", "source_filename": "n.txt", "engagement_id": str(uuid4())},
        headers=auth_header(alice),
    )
    assert ghost.status_code == 404

    # Bob's engagement used by Alice → 404 (cross-owner), and nothing is stored.
    beid = _own_engagement_id(client, bob)
    cross = client.post(
        "/transcripts/text",
        json={"text": "n", "source_filename": "n.txt", "engagement_id": beid},
        headers=auth_header(alice),
    )
    assert cross.status_code == 404


def test_media_upload_rejects_oversize(client, alice: SeededConsultant) -> None:
    # Shrink the limit on the running app, then post one byte over it.
    client.app.state.settings.max_upload_bytes = 8
    media = base64.b64encode(b"123456789").decode()  # 9 bytes
    resp = client.post(
        "/transcripts/media",
        json={
            "media_base64": media,
            "source_filename": "big.wav",
            "content_type": "audio/wav",
            "source_kind": "audio",
        },
        headers=auth_header(alice),
    )
    assert resp.status_code == 413


def test_media_upload_rejects_a_text_source_kind(client, alice: SeededConsultant) -> None:
    media = base64.b64encode(b"hi").decode()
    resp = client.post(
        "/transcripts/media",
        json={
            "media_base64": media,
            "source_filename": "x.txt",
            "content_type": "text/plain",
            "source_kind": "transcript_text",  # must use /text, not /media
        },
        headers=auth_header(alice),
    )
    assert resp.status_code == 422


def test_media_upload_rejects_invalid_base64(client, alice: SeededConsultant) -> None:
    resp = client.post(
        "/transcripts/media",
        json={
            "media_base64": "not base64!!!",
            "source_filename": "x.wav",
            "content_type": "audio/wav",
            "source_kind": "audio",
        },
        headers=auth_header(alice),
    )
    assert resp.status_code == 422


def test_transcript_endpoints_require_authentication(client) -> None:
    assert client.get("/transcripts").status_code == 401
    assert client.post("/transcripts/text", json={}).status_code == 401
