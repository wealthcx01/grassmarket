"""Voice note → pipeline proposal (GRS-0249 scope 4).

The ticket's non-negotiable is one sentence: **a voice note must never move a prospect stage on its
own.** Everything here exists to make that structural rather than aspirational.

1. Proposing writes nothing. The prospect is untouched until somebody confirms.
2. Confirmation applies **what the advisor confirmed**, not what was suggested. A field they left
   out is not written, however confident the extractor was about it.
3. The write goes through the same choke-point a typed update uses, so the stage-history row is
   written and an illegal move is refused by the same graph.
4. What the machine said and what the human agreed to are both kept, so a corrected field is
   afterwards distinguishable from an accepted one.
"""

from __future__ import annotations

import base64
from datetime import date

import pytest
from bcap_contracts.extraction import ExtractionConfidence
from bcap_contracts.voice_notes import PipelineField
from fastapi import FastAPI

from grassmarket.pathb.pipeline_extraction import (
    FixturePipelineExtractor,
    PipelineExtractionResult,
    ProposedValue,
)
from grassmarket.web.routers import voice_notes as voice_notes_router
from tests.conftest import SeededConsultant, auth_header

# A legal move from `prospect`: the lifecycle graph allows workshop_scheduled, closed or
# nurture and nothing else. Using a legal one here keeps this fixture about the proposal
# mechanism; the graph gets its own test below.
TRANSCRIPT = (
    "Good meeting. They want the workshop, so get it in the diary. "
    "I said we would send the revised fee schedule by the tenth."
)

#: What a working extractor would return for TRANSCRIPT. Spans point at the sentences the values
#: came from, because a proposed stage change the advisor cannot trace to a sentence is not
#: reviewable.
FIXTURE_VALUES = (
    ProposedValue(
        field=PipelineField.STAGE,
        value="workshop_scheduled",
        confidence=ExtractionConfidence.HIGH,
        span_start=39,
        span_end=93,
    ),
    ProposedValue(
        field=PipelineField.NEXT_ACTION,
        value="Send the revised fee schedule",
        confidence=ExtractionConfidence.HIGH,
        span_start=94,
        span_end=155,
    ),
    ProposedValue(
        field=PipelineField.NEXT_ACTION_ON,
        value="2026-09-10",
        confidence=ExtractionConfidence.MEDIUM,
        span_start=94,
        span_end=155,
    ),
)


@pytest.fixture
def extracting_app(app: FastAPI) -> FastAPI:
    """The app with a deterministic extractor standing in for the AI, exactly as Path A's tests
    swap in `FixtureExtractor`. CI makes no model call."""
    app.dependency_overrides[voice_notes_router._extractor] = lambda: FixturePipelineExtractor(
        values=FIXTURE_VALUES, gaps=(PipelineField.COMMS_NOTE.value,)
    )
    return app


def _prospect(client, who: SeededConsultant, name: str = "Kilmarnock Foods") -> str:
    resp = client.post("/prospects", json={"company_name": name}, headers=auth_header(who))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _voice_note(client, who: SeededConsultant, prospect_id: str) -> str:
    resp = client.post(
        "/transcripts/media",
        json={
            "media_base64": base64.b64encode(TRANSCRIPT.encode()).decode(),
            "source_filename": "voice-note.webm",
            "content_type": "audio/webm",
            "source_kind": "audio",
            "prospect_id": prospect_id,
            "recording_kind": "voice_note",
            "keep_recording": True,
        },
        headers=auth_header(who),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _propose(client, who: SeededConsultant, prospect_id: str, transcript_id: str) -> dict:
    resp = client.post(
        "/voice-notes",
        json={"prospect_id": prospect_id, "transcript_id": transcript_id},
        headers=auth_header(who),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestAProposalIsOnlyAProposal:
    def test_proposing_changes_nothing_about_the_prospect(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        """The whole ticket in one assertion. The extractor said 'qualified' with high confidence
        and the prospect did not move."""
        prospect_id = _prospect(client, alice)
        before = client.get(f"/prospects/{prospect_id}", headers=auth_header(alice)).json()
        _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))
        after = client.get(f"/prospects/{prospect_id}", headers=auth_header(alice)).json()

        assert after["stage"] == before["stage"] == "prospect"
        assert after["next_action"] is None
        assert after["next_action_on"] is None

    def test_the_proposal_carries_confidence_and_the_span_it_came_from(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        prospect_id = _prospect(client, alice)
        body = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))

        by_field = {f["field"]: f for f in body["fields"]}
        assert by_field["stage"]["proposed_value"] == "workshop_scheduled"
        assert by_field["stage"]["confidence"] == "high"
        assert by_field["stage"]["span_end"] > by_field["stage"]["span_start"]
        assert by_field["next_action_on"]["confidence"] == "medium"
        # Nothing is accepted before anybody has looked at it.
        assert all(f["accepted"] is False for f in body["fields"])
        assert body["status"] == "proposed"

    def test_it_names_what_it_could_not_find(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        """'I listened for a comms note and heard nothing' is a different statement from silence,
        and only one of them tells the advisor to type it themselves."""
        prospect_id = _prospect(client, alice)
        body = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))
        assert body["gaps"] == ["comms_note"]

    def test_the_offline_default_proposes_nothing_at_all(
        self, client, alice: SeededConsultant
    ) -> None:
        """Without the fixture the real default runs. It must not guess a stage from the words
        'move them to qualified' sitting in the transcript — a keyword match wearing a confidence
        score is the fabrication non-negotiable #3 exists to stop."""
        prospect_id = _prospect(client, alice)
        body = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))
        assert body["fields"] == []
        assert set(body["gaps"]) == {"stage", "next_action", "next_action_on", "comms_note"}


class TestConfirmationAppliesWhatTheAdvisorSaid:
    def test_confirming_moves_the_stage_and_sets_the_next_action(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        prospect_id = _prospect(client, alice)
        proposal = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))

        resp = client.post(
            f"/voice-notes/{proposal['id']}/confirm",
            json={
                "fields": {
                    "stage": "workshop_scheduled",
                    "next_action": "Send the revised fee schedule",
                    "next_action_on": "2026-09-10",
                }
            },
            headers=auth_header(alice),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "confirmed"

        prospect = client.get(f"/prospects/{prospect_id}", headers=auth_header(alice)).json()
        assert prospect["stage"] == "workshop_scheduled"
        assert prospect["next_action"] == "Send the revised fee schedule"
        assert prospect["next_action_on"] == "2026-09-10"

    def test_a_corrected_field_applies_the_correction_and_records_both(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        """The advisor edits one field — the ticket's own acceptance criterion. What lands is
        theirs, and the record still says what the machine had suggested."""
        prospect_id = _prospect(client, alice)
        proposal = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))

        resp = client.post(
            f"/voice-notes/{proposal['id']}/confirm",
            json={
                "fields": {
                    "stage": "workshop_scheduled",
                    "next_action": "Send the revised fee schedule AND the case study",
                }
            },
            headers=auth_header(alice),
        )
        assert resp.status_code == 200, resp.text

        prospect = client.get(f"/prospects/{prospect_id}", headers=auth_header(alice)).json()
        assert prospect["next_action"] == "Send the revised fee schedule AND the case study"

        by_field = {f["field"]: f for f in resp.json()["fields"]}
        # Both facts survive: what was suggested, and what a person actually agreed to.
        assert by_field["next_action"]["proposed_value"] == "Send the revised fee schedule"
        assert (
            by_field["next_action"]["confirmed_value"]
            == "Send the revised fee schedule AND the case study"
        )

    def test_a_field_the_advisor_left_out_is_not_written(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        """Confidence is not consent. The extractor proposed a date with medium confidence; the
        advisor did not confirm it, so it does not exist."""
        prospect_id = _prospect(client, alice)
        proposal = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))

        resp = client.post(
            f"/voice-notes/{proposal['id']}/confirm",
            json={"fields": {"stage": "workshop_scheduled"}},
            headers=auth_header(alice),
        )
        assert resp.status_code == 200, resp.text

        prospect = client.get(f"/prospects/{prospect_id}", headers=auth_header(alice)).json()
        assert prospect["stage"] == "workshop_scheduled"
        assert prospect["next_action"] is None
        assert prospect["next_action_on"] is None

        by_field = {f["field"]: f for f in resp.json()["fields"]}
        # accepted means applied, not merely "the proposal was confirmed".
        assert by_field["stage"]["accepted"] is True
        assert by_field["next_action"]["accepted"] is False
        assert by_field["next_action"]["confirmed_value"] is None

    def test_a_blank_answer_is_not_an_answer(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        """A field sent as an empty string writes nothing AND is not marked accepted. The two have
        to agree: a record saying the advisor accepted something the system never wrote would be
        the audit trail lying about the only thing it exists to record."""
        prospect_id = _prospect(client, alice)
        proposal = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))

        resp = client.post(
            f"/voice-notes/{proposal['id']}/confirm",
            json={"fields": {"stage": "workshop_scheduled", "next_action": "   "}},
            headers=auth_header(alice),
        )
        assert resp.status_code == 200, resp.text

        prospect = client.get(f"/prospects/{prospect_id}", headers=auth_header(alice)).json()
        assert prospect["next_action"] is None

        by_field = {f["field"]: f for f in resp.json()["fields"]}
        assert by_field["next_action"]["accepted"] is False
        assert by_field["next_action"]["confirmed_value"] is None

    def test_confirming_nothing_writes_nothing(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        prospect_id = _prospect(client, alice)
        proposal = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))

        resp = client.post(
            f"/voice-notes/{proposal['id']}/confirm",
            json={"fields": {}},
            headers=auth_header(alice),
        )
        assert resp.status_code == 200, resp.text
        prospect = client.get(f"/prospects/{prospect_id}", headers=auth_header(alice)).json()
        assert prospect["stage"] == "prospect"


class TestItGoesThroughTheSameDoorAsTyping:
    def test_the_stage_move_writes_a_stage_history_row(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        """The convergence that matters: a confirmed voice note is indistinguishable from a typed
        update downstream, because it went through `update_prospect_stage` like everything else."""
        prospect_id = _prospect(client, alice)
        proposal = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))
        client.post(
            f"/voice-notes/{proposal['id']}/confirm",
            json={"fields": {"stage": "workshop_scheduled"}},
            headers=auth_header(alice),
        )
        history = client.get(f"/prospects/{prospect_id}/history", headers=auth_header(alice)).json()
        assert history[-1]["to_stage"] == "workshop_scheduled"
        assert history[-1]["from_stage"] == "prospect"

    def test_an_illegal_stage_move_is_refused_by_the_same_graph(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        """Prospect straight to delivered is illegal by hand, so it is illegal by voice."""
        prospect_id = _prospect(client, alice)
        proposal = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))
        resp = client.post(
            f"/voice-notes/{proposal['id']}/confirm",
            json={"fields": {"stage": "delivered"}},
            headers=auth_header(alice),
        )
        assert resp.status_code == 409, resp.text

    def test_a_nonsense_stage_is_refused_rather_than_dropped(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        prospect_id = _prospect(client, alice)
        proposal = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))
        resp = client.post(
            f"/voice-notes/{proposal['id']}/confirm",
            json={"fields": {"stage": "nearly-there"}},
            headers=auth_header(alice),
        )
        assert resp.status_code in (409, 422), resp.text

    def test_an_unparseable_date_refuses_before_anything_is_written(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        """Parsed before applied, so a bad date cannot leave the stage moved and the action not
        set from one click."""
        prospect_id = _prospect(client, alice)
        proposal = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))
        resp = client.post(
            f"/voice-notes/{proposal['id']}/confirm",
            json={"fields": {"stage": "workshop_scheduled", "next_action_on": "next Tuesday"}},
            headers=auth_header(alice),
        )
        assert resp.status_code == 409, resp.text
        prospect = client.get(f"/prospects/{prospect_id}", headers=auth_header(alice)).json()
        assert prospect["stage"] == "prospect", "the stage moved despite the refusal"

    def test_a_note_with_no_engagement_says_so_instead_of_filing_it_somewhere(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        """The comms log belongs to an engagement, and a car-park prospect has none. Refused in
        words the advisor can act on, never guessed at."""
        prospect_id = _prospect(client, alice)
        proposal = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))
        resp = client.post(
            f"/voice-notes/{proposal['id']}/confirm",
            json={"fields": {"comms_note": "They want the fee schedule."}},
            headers=auth_header(alice),
        )
        assert resp.status_code == 409
        assert "no engagement" in resp.json()["detail"]


class TestAProposalIsAnsweredOnce:
    def test_confirming_twice_is_refused(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        prospect_id = _prospect(client, alice)
        proposal = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))
        first = client.post(
            f"/voice-notes/{proposal['id']}/confirm",
            json={"fields": {"stage": "workshop_scheduled"}},
            headers=auth_header(alice),
        )
        assert first.status_code == 200
        again = client.post(
            f"/voice-notes/{proposal['id']}/confirm",
            json={"fields": {"stage": "nurture"}},
            headers=auth_header(alice),
        )
        assert again.status_code == 409

    def test_a_discarded_proposal_is_recorded_not_deleted(
        self, extracting_app, client, alice: SeededConsultant
    ) -> None:
        """A person saying no is evidence the gate works, and worth as much as a yes."""
        prospect_id = _prospect(client, alice)
        proposal = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))
        resp = client.post(f"/voice-notes/{proposal['id']}/discard", headers=auth_header(alice))
        assert resp.status_code == 200
        assert resp.json()["status"] == "discarded"
        assert resp.json()["discarded_at"] is not None

        still_there = client.get(
            f"/voice-notes/{proposal['id']}", headers=auth_header(alice)
        ).json()
        assert still_there["status"] == "discarded"
        assert still_there["fields"][0]["proposed_value"] == "workshop_scheduled"

        prospect = client.get(f"/prospects/{prospect_id}", headers=auth_header(alice)).json()
        assert prospect["stage"] == "prospect"


class TestScopingHolds:
    def test_a_proposal_cannot_join_another_advisors_prospect(
        self, extracting_app, client, alice: SeededConsultant, bob: SeededConsultant
    ) -> None:
        bobs_prospect = _prospect(client, bob, name="Not Alice's Client")
        alices_prospect = _prospect(client, alice)
        transcript_id = _voice_note(client, alice, alices_prospect)
        resp = client.post(
            "/voice-notes",
            json={"prospect_id": bobs_prospect, "transcript_id": transcript_id},
            headers=auth_header(alice),
        )
        assert resp.status_code == 404

    def test_another_advisor_cannot_read_or_confirm_it(
        self, extracting_app, client, alice: SeededConsultant, bob: SeededConsultant
    ) -> None:
        prospect_id = _prospect(client, alice)
        proposal = _propose(client, alice, prospect_id, _voice_note(client, alice, prospect_id))
        assert (
            client.get(f"/voice-notes/{proposal['id']}", headers=auth_header(bob)).status_code
            == 404
        )
        assert (
            client.post(
                f"/voice-notes/{proposal['id']}/confirm",
                json={"fields": {"stage": "workshop_scheduled"}},
                headers=auth_header(bob),
            ).status_code
            == 404
        )


def test_the_extractor_port_shape_matches_path_b() -> None:
    """A guard on the pattern rather than the code: if the pipeline extractor stops looking like
    the Path B one, the reason should be deliberate."""
    result = FixturePipelineExtractor(values=FIXTURE_VALUES).extract(TRANSCRIPT, company_name="X")
    assert isinstance(result, PipelineExtractionResult)
    assert result.values[0].field is PipelineField.STAGE
    assert date.fromisoformat(FIXTURE_VALUES[2].value) == date(2026, 9, 10)
