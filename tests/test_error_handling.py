"""GRS-0053: a repository error a route forgot to translate, and a transcript decrypt failure,
become controlled HTTP responses at their proper status — never a bare 500 / uncaught traceback.
"""

from __future__ import annotations

from uuid import UUID

from grassmarket.data.models import MeetingTranscriptORM
from grassmarket.data.repository import ConflictError, Repository, ScopeViolationError
from tests.conftest import SeededConsultant, auth_header


def test_uncaught_scope_error_maps_to_404(client, alice: SeededConsultant, monkeypatch) -> None:
    def boom(self, principal):  # noqa: ANN001, ANN202
        raise ScopeViolationError("nope")

    monkeypatch.setattr(Repository, "list_predictions", boom)
    resp = client.get("/predictions", headers=auth_header(alice))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Not found."  # existence not confirmed


def test_uncaught_conflict_error_maps_to_409(client, alice: SeededConsultant, monkeypatch) -> None:
    def boom(self, principal):  # noqa: ANN001, ANN202
        raise ConflictError("clash")

    monkeypatch.setattr(Repository, "list_predictions", boom)
    resp = client.get("/predictions", headers=auth_header(alice))
    assert resp.status_code == 409


def test_corrupt_transcript_decrypt_is_a_controlled_500(
    client, alice: SeededConsultant, session_factory
) -> None:
    tid = client.post(
        "/transcripts/text",
        json={"text": "secret", "source_filename": "n.txt"},
        headers=auth_header(alice),
    ).json()["id"]

    # Corrupt the ciphertext at rest — a decrypt on read now fails.
    session = session_factory()
    try:
        row = session.get(MeetingTranscriptORM, UUID(tid))
        assert row is not None
        row.text_ciphertext = b"not-a-valid-fernet-token"
        session.add(row)
        session.commit()
    finally:
        session.close()

    resp = client.get(f"/transcripts/{tid}", headers=auth_header(alice))
    assert resp.status_code == 500
    assert "decrypt" in resp.json()["detail"].lower()
    assert "fernet" not in resp.json()["detail"].lower()  # no raw crypto detail leaked
