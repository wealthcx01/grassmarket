"""Uploaded documents (GRS-0247).

Before this, the product had no general upload path. The only inbound route was Path B's media
ingest, which accepts audio or video, keeps the transcript and discards the file — so an advisor
with a client's board pack had nowhere to put it, and the founder's own files moved by `scp`.

The rules that matter, in the order they are tested: it stores and returns the file byte-identical;
it is scoped absolutely; it refuses a document with no parent; it enforces the size cap before
decoding; the scanner runs before anything is written; and a re-parent onto an engagement keeps the
original link rather than rewriting history.
"""

from __future__ import annotations

import base64
import hashlib
from uuid import UUID

from bcap_contracts.assessments import RecordProvenance
from bcap_contracts.entities import PipelineStage

from grassmarket.data.models import DocumentORM
from tests.conftest import SeededConsultant, auth_header

_PDF = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n%%EOF\n"

_TO_CONTRACTED = (
    PipelineStage.WORKSHOP_SCHEDULED,
    PipelineStage.WORKSHOP_DELIVERED,
    PipelineStage.QUALIFIED,
    PipelineStage.SCOPED,
    PipelineStage.CONTRACTED,
)


def _prospect(client, who: SeededConsultant, name: str = "Ailsa Bank") -> str:
    resp = client.post("/prospects", json={"company_name": name}, headers=auth_header(who))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _upload(client, who: SeededConsultant, **over):
    payload = {
        "content_base64": base64.b64encode(_PDF).decode(),
        "filename": "board-pack.pdf",
        "content_type": "application/pdf",
    }
    payload.update(over)
    return client.post("/documents", json=payload, headers=auth_header(who))


class TestStoringAndReadingBack:
    def test_a_pdf_round_trips_byte_identical(self, client, alice: SeededConsultant) -> None:
        """The acceptance criterion: what comes back is what went in."""
        resp = _upload(client, alice, prospect_id=_prospect(client, alice))
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["filename"] == "board-pack.pdf"
        assert body["byte_size"] == len(_PDF)
        assert body["sha256"] == hashlib.sha256(_PDF).hexdigest()
        assert body["scanner_ref"], "the scanner that passed it must be recorded"

        got = client.get(f"/documents/{body['id']}/content", headers=auth_header(alice))
        assert got.status_code == 200
        assert got.content == _PDF
        assert "board-pack.pdf" in got.headers["content-disposition"]

    def test_the_bytes_are_encrypted_at_rest(
        self, client, alice: SeededConsultant, session_factory
    ) -> None:
        """A client document is at least as sensitive as a meeting transcript."""
        doc_id = _upload(client, alice, prospect_id=_prospect(client, alice)).json()["id"]
        session = session_factory()
        try:
            row = session.get(DocumentORM, UUID(doc_id))
            assert row is not None
            assert row.content_ciphertext != _PDF
            assert b"%PDF" not in row.content_ciphertext
        finally:
            session.close()

    def test_it_lists_only_the_documents_for_the_parent_asked_for(
        self, client, alice: SeededConsultant
    ) -> None:
        first, second = _prospect(client, alice, "One"), _prospect(client, alice, "Two")
        _upload(client, alice, prospect_id=first, filename="a.pdf")
        _upload(client, alice, prospect_id=second, filename="b.pdf")
        listed = client.get(
            "/documents", params={"prospect_id": first}, headers=auth_header(alice)
        ).json()
        assert [d["filename"] for d in listed] == ["a.pdf"]


class TestScoping:
    """Non-negotiable #9. A cross-owner read is a 404, never a 403 — the existence of another
    advisor's document is never revealed."""

    def test_another_advisor_cannot_read_the_metadata_or_the_bytes(
        self, client, alice: SeededConsultant, bob: SeededConsultant
    ) -> None:
        doc_id = _upload(client, alice, prospect_id=_prospect(client, alice)).json()["id"]
        assert client.get(f"/documents/{doc_id}", headers=auth_header(bob)).status_code == 404
        assert (
            client.get(f"/documents/{doc_id}/content", headers=auth_header(bob)).status_code == 404
        )

    def test_another_advisors_document_is_not_in_my_list(
        self, client, alice: SeededConsultant, bob: SeededConsultant
    ) -> None:
        _upload(client, alice, prospect_id=_prospect(client, alice))
        assert client.get("/documents", headers=auth_header(bob)).json() == []

    def test_uploading_onto_another_advisors_prospect_is_refused(
        self, client, alice: SeededConsultant, bob: SeededConsultant
    ) -> None:
        """404, so the attempt reveals nothing about whether that prospect exists."""
        theirs = _prospect(client, bob, "Bobco")
        assert _upload(client, alice, prospect_id=theirs).status_code == 404


class TestTheRulesItRefuses:
    def test_a_document_with_no_parent_is_refused(self, client, alice: SeededConsultant) -> None:
        """One with no parent could never be found again."""
        resp = _upload(client, alice)
        assert resp.status_code == 422
        assert "prospect" in resp.text.lower()

    def test_an_oversized_upload_is_refused_before_it_is_decoded(
        self, client, alice: SeededConsultant
    ) -> None:
        client.app.state.settings.max_upload_bytes = 16
        resp = _upload(
            client,
            alice,
            prospect_id=_prospect(client, alice),
            content_base64=base64.b64encode(b"x" * 4096).decode(),
        )
        assert resp.status_code == 413

    def test_invalid_base64_is_refused(self, client, alice: SeededConsultant) -> None:
        resp = _upload(
            client, alice, prospect_id=_prospect(client, alice), content_base64="not base64!!"
        )
        assert resp.status_code == 422

    def test_an_empty_file_is_refused(self, client, alice: SeededConsultant) -> None:
        resp = _upload(client, alice, prospect_id=_prospect(client, alice), content_base64="")
        assert resp.status_code == 422


class TestTheScannerRunsFirst:
    """Nothing is stored on a refusal — the same order `ingest_media` uses."""

    def test_an_executable_renamed_as_a_pdf_is_refused_and_not_stored(
        self, client, alice: SeededConsultant
    ) -> None:
        client.app.state.settings.media_scanner_provider = "content-type"
        resp = _upload(
            client,
            alice,
            prospect_id=_prospect(client, alice),
            content_base64=base64.b64encode(b"MZ\x90\x00\x03payload").decode(),
        )
        assert resp.status_code == 422
        assert "executable" in resp.text
        assert client.get("/documents", headers=auth_header(alice)).json() == []

    def test_bytes_contradicting_the_declared_type_are_refused(
        self, client, alice: SeededConsultant
    ) -> None:
        client.app.state.settings.media_scanner_provider = "content-type"
        resp = _upload(
            client,
            alice,
            prospect_id=_prospect(client, alice),
            content_base64=base64.b64encode(b"this is plainly not a pdf").decode(),
        )
        assert resp.status_code == 422


class TestReparenting:
    """Backend Requests R2: a workshop is recorded while the client is still a prospect."""

    def _engagement(self, client, who: SeededConsultant) -> tuple[str, str]:
        prospect_id = _prospect(client, who, "Tantallon Markets")
        for stage in _TO_CONTRACTED:
            resp = client.patch(
                f"/prospects/{prospect_id}/stage",
                json={"stage": stage.value},
                headers=auth_header(who),
            )
            assert resp.status_code == 200, resp.text
        resp = client.post(
            "/engagements",
            json={"prospect_id": prospect_id, "title": "Tantallon — delivery"},
            headers=auth_header(who),
        )
        assert resp.status_code == 201, resp.text
        return prospect_id, resp.json()["id"]

    def test_it_attaches_and_keeps_the_original_prospect_link(
        self, client, alice: SeededConsultant
    ) -> None:
        prospect_id, engagement_id = self._engagement(client, alice)
        doc_id = _upload(client, alice, prospect_id=prospect_id).json()["id"]

        resp = client.post(
            f"/documents/{doc_id}/engagement/{engagement_id}", headers=auth_header(alice)
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["engagement_id"] == engagement_id
        assert body["prospect_id"] == prospect_id, (
            "the document did belong to that prospect; rewriting history to say otherwise is the "
            "quiet edit this codebase refuses elsewhere"
        )

    def test_moving_it_to_a_different_engagement_is_refused(
        self, client, alice: SeededConsultant
    ) -> None:
        prospect_id, first = self._engagement(client, alice)
        doc_id = _upload(client, alice, prospect_id=prospect_id).json()["id"]
        client.post(f"/documents/{doc_id}/engagement/{first}", headers=auth_header(alice))
        _, second = self._engagement(client, alice)
        resp = client.post(f"/documents/{doc_id}/engagement/{second}", headers=auth_header(alice))
        assert resp.status_code == 409

    def test_attaching_to_another_advisors_engagement_is_refused(
        self, client, alice: SeededConsultant, bob: SeededConsultant
    ) -> None:
        doc_id = _upload(client, alice, prospect_id=_prospect(client, alice)).json()["id"]
        _, theirs = self._engagement(client, bob)
        resp = client.post(f"/documents/{doc_id}/engagement/{theirs}", headers=auth_header(alice))
        assert resp.status_code == 404


class TestIntegrity:
    def test_a_tampered_document_is_refused_rather_than_returned(
        self, client, alice: SeededConsultant, session_factory
    ) -> None:
        """The hash is of the plaintext, so it can be checked without the key. A mismatch means
        the stored bytes are not the bytes uploaded; handing them back would be worse."""
        doc_id = _upload(client, alice, prospect_id=_prospect(client, alice)).json()["id"]
        session = session_factory()
        try:
            row = session.get(DocumentORM, UUID(doc_id))
            assert row is not None
            row.sha256 = "0" * 64
            session.commit()
        finally:
            session.close()
        resp = client.get(f"/documents/{doc_id}/content", headers=auth_header(alice))
        assert resp.status_code == 500
        assert "does not match the hash" in resp.text

    def test_provenance_defaults_to_production(self, client, alice: SeededConsultant) -> None:
        body = _upload(client, alice, prospect_id=_prospect(client, alice)).json()
        assert body["provenance"] == RecordProvenance.PRODUCTION.value
