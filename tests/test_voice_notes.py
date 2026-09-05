"""Voice notes and the consent gate (GRS-0249, GRS-0255).

Four things are asserted here, and each of them is a rule somebody could otherwise quietly relax.

1. **No consent, no recording kept.** A recorded session without consent is refused and *nothing*
   is stored — not the transcript, not the audio, not a flagged row for someone to look at later.
2. **No consent claimed where none was asked.** A voice note dictated alone cannot carry a consent
   timestamp. This is the quieter failure of the two: a record saying somebody agreed when nobody
   was there is worse than a missing record.
3. **The stored wording is the founder-approved wording.** Byte for byte, checked against the
   ticket file itself, so a well-meaning rewrite of the string fails the suite rather than
   silently changing what clients are told they agreed to.
4. **The audio is kept.** Media used to be transcribed and discarded, which left a disputed
   correction with nothing to check against.
"""

from __future__ import annotations

import base64
import re
from pathlib import Path
from uuid import UUID

import pytest
from bcap_contracts.meetings import FOUNDER_APPROVED_CONSENT_WORDING
from sqlalchemy.orm import Session, sessionmaker

from grassmarket.data.models import DocumentORM, MeetingTranscriptORM
from tests.conftest import SeededConsultant, auth_header

CONSENT_TICKET = (
    Path(__file__).resolve().parents[1] / "docs/tickets/GRS-0255-recorder-consent-and-streaming.md"
)


def _prospect(client, who: SeededConsultant, name: str = "Kilmarnock Foods") -> str:
    resp = client.post("/prospects", json={"company_name": name}, headers=auth_header(who))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _upload(client, who: SeededConsultant, **overrides):
    payload = {
        "media_base64": base64.b64encode(b"moving them to proposal next week").decode(),
        "source_filename": "voice-note.webm",
        "content_type": "audio/webm",
        "source_kind": "audio",
    }
    payload.update(overrides)
    return client.post("/transcripts/media", json=payload, headers=auth_header(who))


class TestTheConsentWordingIsTheFounderApprovedWording:
    def test_the_constant_matches_the_ticket_word_for_word(self) -> None:
        """The ticket is where the founder approved it, so the ticket is what we check against.

        If this fails, someone edited the wording in code. That is a founder decision (GRS-0255),
        so the fix is to get it approved and update the ticket — not to update this test.
        """
        quoted = re.search(r'> \*"(.+?)"\*', CONSENT_TICKET.read_text(), re.DOTALL)
        assert quoted, "The founder-approved wording is no longer quoted in GRS-0255."
        from_ticket = " ".join(quoted.group(1).replace("\n>", " ").split())
        assert FOUNDER_APPROVED_CONSENT_WORDING == from_ticket

    def test_the_api_serves_it_so_the_recorder_never_holds_its_own_copy(
        self, client, alice: SeededConsultant
    ) -> None:
        resp = client.get("/transcripts/consent-line", headers=auth_header(alice))
        assert resp.status_code == 200, resp.text
        assert resp.json()["wording"] == FOUNDER_APPROVED_CONSENT_WORDING


class TestChangingTheWordingDoesNotRewriteHistory:
    """The founder revised the wording on 2026-09-04 to name OpenAI. That must not touch consents
    already given.

    A stored `consent_wording` is the text that was actually read to *that* client. Migrating it to
    match a newer promise would destroy the only thing the field exists for — the record could no
    longer say what was agreed, only what we would say today. This is the difference between a
    record and a setting.
    """

    def test_a_transcript_stored_under_the_old_wording_still_reads_back(
        self, client, alice: SeededConsultant, session_factory: sessionmaker[Session]
    ) -> None:
        prospect_id = _prospect(client, alice)
        created = _upload(
            client,
            alice,
            prospect_id=prospect_id,
            recording_kind="recorded_session",
            consent_confirmed_at="2026-09-03T14:00:00Z",
            consent_wording=FOUNDER_APPROVED_CONSENT_WORDING,
        ).json()

        # Rewrite the row to a superseded wording, as a record taken before the revision would be.
        superseded = (
            "I'd like to record this session so I can write it up accurately. The recording stays "
            "in the Bruntsfield advisor system, is transcribed for my notes, and isn't shared "
            "outside the engagement team. Are you happy for me to record?"
        )
        with session_factory() as session:
            row = session.get(MeetingTranscriptORM, UUID(created["id"]))
            assert row is not None
            row.consent_wording = superseded
            session.add(row)
            session.commit()

        # It reads back unchanged. Validation happens at the gate, on the way in — never again on
        # the way out, or every past consent would be rewritten by the next revision.
        fetched = client.get(f"/transcripts/{created['id']}", headers=auth_header(alice)).json()
        assert fetched["consent_wording"] == superseded
        assert fetched["consent_wording"] != FOUNDER_APPROVED_CONSENT_WORDING

    def test_the_superseded_wording_can_no_longer_be_used_for_a_new_recording(
        self, client, alice: SeededConsultant
    ) -> None:
        """Old consents are honoured; they are not accepted again. A recorder still showing the
        superseded text would be telling a client something we now know to be untrue."""
        prospect_id = _prospect(client, alice)
        resp = _upload(
            client,
            alice,
            prospect_id=prospect_id,
            recording_kind="recorded_session",
            consent_confirmed_at="2026-09-04T14:00:00Z",
            consent_wording=(
                "I'd like to record this session so I can write it up accurately. The recording "
                "stays in the Bruntsfield advisor system, is transcribed for my notes, and isn't "
                "shared outside the engagement team. Are you happy for me to record?"
            ),
        )
        assert resp.status_code == 422
        assert "founder-approved" in resp.json()["detail"]


class TestTheWordingIsTrueAboutWhereTheAudioGoes:
    def test_it_names_the_third_party_the_audio_is_sent_to(self) -> None:
        """The revision's whole point. The transcriber is hosted OpenAI Whisper, so the audio
        leaves our infrastructure; the previous wording told the client the opposite."""
        assert "OpenAI" in FOUNDER_APPROVED_CONSENT_WORDING

    def test_it_no_longer_claims_the_recording_stays_with_us(self) -> None:
        """Guards the specific false promise rather than the whole sentence, so a future rewrite
        is free to change the phrasing but not to reinstate the untruth."""
        assert "stays in the Bruntsfield advisor system" not in FOUNDER_APPROVED_CONSENT_WORDING


class TestNoConsentNoRecordingKept:
    @pytest.mark.parametrize(
        ("missing", "consent"),
        [
            ("both", {}),
            ("the timestamp", {"consent_wording": FOUNDER_APPROVED_CONSENT_WORDING}),
            ("the wording", {"consent_confirmed_at": "2026-09-03T14:00:00Z"}),
        ],
    )
    def test_a_recorded_session_without_consent_is_refused(
        self, client, alice: SeededConsultant, missing: str, consent: dict
    ) -> None:
        prospect_id = _prospect(client, alice)
        resp = _upload(
            client,
            alice,
            prospect_id=prospect_id,
            recording_kind="recorded_session",
            keep_recording=True,
            **consent,
        )
        assert resp.status_code == 422, f"missing {missing}: {resp.text}"

    def test_the_refusal_stores_nothing_at_all(
        self, client, alice: SeededConsultant, session_factory: sessionmaker[Session]
    ) -> None:
        """Refused means refused. Not stored-and-flagged: a flagged recording is still a recording
        that nobody agreed to, sitting in the database."""
        prospect_id = _prospect(client, alice)
        _upload(
            client,
            alice,
            prospect_id=prospect_id,
            recording_kind="recorded_session",
            keep_recording=True,
        )
        with session_factory() as session:
            assert session.query(MeetingTranscriptORM).count() == 0
            assert session.query(DocumentORM).count() == 0

    def test_wording_that_is_not_the_approved_wording_is_refused(
        self, client, alice: SeededConsultant
    ) -> None:
        """Otherwise `consent_wording` is a field the caller controls, and the stored record no
        longer proves what was actually shown to the client."""
        prospect_id = _prospect(client, alice)
        resp = _upload(
            client,
            alice,
            prospect_id=prospect_id,
            recording_kind="recorded_session",
            consent_confirmed_at="2026-09-03T14:00:00Z",
            consent_wording="Mind if I record this?",
            keep_recording=True,
        )
        assert resp.status_code == 422
        assert "founder-approved" in resp.json()["detail"]

    def test_a_recorded_session_with_consent_is_kept_with_the_exact_wording(
        self, client, alice: SeededConsultant
    ) -> None:
        prospect_id = _prospect(client, alice)
        resp = _upload(
            client,
            alice,
            prospect_id=prospect_id,
            recording_kind="recorded_session",
            consent_confirmed_at="2026-09-03T14:00:00Z",
            consent_wording=FOUNDER_APPROVED_CONSENT_WORDING,
            keep_recording=True,
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["recording_kind"] == "recorded_session"
        assert body["consent_wording"] == FOUNDER_APPROVED_CONSENT_WORDING
        assert body["consent_confirmed_at"] is not None


class TestAVoiceNoteClaimsNoConsent:
    def test_a_voice_note_carrying_consent_is_refused(
        self, client, alice: SeededConsultant
    ) -> None:
        """The advisor was alone. A consent record would be a claim that somebody agreed."""
        prospect_id = _prospect(client, alice)
        resp = _upload(
            client,
            alice,
            prospect_id=prospect_id,
            recording_kind="voice_note",
            consent_confirmed_at="2026-09-03T14:00:00Z",
            consent_wording=FOUNDER_APPROVED_CONSENT_WORDING,
            keep_recording=True,
        )
        assert resp.status_code == 422
        assert "nobody to agree" in resp.json()["detail"]

    def test_a_plain_voice_note_is_stored_with_no_consent_fields(
        self, client, alice: SeededConsultant
    ) -> None:
        prospect_id = _prospect(client, alice)
        resp = _upload(
            client, alice, prospect_id=prospect_id, recording_kind="voice_note", keep_recording=True
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["recording_kind"] == "voice_note"
        assert body["consent_confirmed_at"] is None
        assert body["consent_wording"] is None


class TestTheRecordingIsKept:
    def test_the_audio_is_stored_and_linked_to_the_transcript(
        self, client, alice: SeededConsultant
    ) -> None:
        """A corrected transcript whose recording was thrown away cannot be re-checked when the
        extraction is disputed, and disputes are the whole reason to keep provenance."""
        prospect_id = _prospect(client, alice)
        body = _upload(
            client, alice, prospect_id=prospect_id, recording_kind="voice_note", keep_recording=True
        ).json()

        document_id = body["recording_document_id"]
        assert document_id is not None, "the recording was discarded"
        content = client.get(f"/documents/{document_id}/content", headers=auth_header(alice))
        assert content.status_code == 200
        assert content.content == b"moving them to proposal next week"

    def test_keeping_the_recording_needs_somewhere_to_file_it(
        self, client, alice: SeededConsultant
    ) -> None:
        resp = _upload(client, alice, recording_kind="voice_note", keep_recording=True)
        assert resp.status_code == 422
        assert "could never be found again" in resp.json()["detail"]

    def test_a_note_can_be_filed_against_a_prospect_with_no_engagement_anywhere(
        self, client, alice: SeededConsultant
    ) -> None:
        """The car park moment: the client is a prospect, no engagement exists, and this is the one
        time the recorder is for (GRS-0254)."""
        prospect_id = _prospect(client, alice)
        body = _upload(client, alice, prospect_id=prospect_id, recording_kind="voice_note").json()
        assert body["prospect_id"] == prospect_id
        assert body["engagement_id"] is None


class TestScopingHolds:
    def test_a_note_cannot_be_filed_against_another_advisors_prospect(
        self, client, alice: SeededConsultant, bob: SeededConsultant
    ) -> None:
        """Non-negotiable #9. A cross-owner parent is a 404, so Bob's pipeline is never revealed."""
        bobs_prospect = _prospect(client, bob, name="Not Alice's Client")
        resp = _upload(client, alice, prospect_id=bobs_prospect, recording_kind="voice_note")
        assert resp.status_code == 404
