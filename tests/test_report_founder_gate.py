"""The founder signs off the client report's PROSE, not just the assessment (GRS-0245, ADR-0041).

GRS-0245 measured the gap before this was built (`docs/reviews/GRS-0245-founder-gate-share-links/`):
the founder approves a scored *document*, the advisor then writes the words a client actually reads,
and nothing bound the second to the first. On a production record the PDF downloaded, the link
issued and the public page read — with no sign-off of the report content anywhere in the sequence.

The rule is the same one ADR-0041 already states, bound to the right artefact: an approval is a fact
about a hash, and editing what it names returns the record to the queue.
"""

from __future__ import annotations

import pytest

from grassmarket.deliverables.gate import (
    ReportApprovalPendingError,
    assert_report_founder_approved,
)
from tests.client_report_helpers import (
    deliverable_with_run,
    sandbox_deliverable_with_run,
    written_prose,
)
from tests.conftest import SeededConsultant, auth_header


def _prose(overrides: dict | None = None) -> dict:
    sections = written_prose()
    for kind, body in (overrides or {}).items():
        sections[kind]["body"] = [body]
    return sections


@pytest.fixture
def production_report(client, alice: SeededConsultant, founder: SeededConsultant) -> str:
    """A production deliverable with prose written — the state the gap was measured in."""
    did = deliverable_with_run(client, alice, founder)
    written = client.put(
        f"/deliverables/{did}/report-prose",
        json={"sections": _prose()},
        headers=auth_header(alice),
    )
    assert written.status_code == 200, written.text
    return did


def _issue(client, owner, did):
    return client.post(
        f"/deliverables/{did}/links",
        json={"recipient_label": "CFO"},
        headers=auth_header(owner),
    )


def _pdf(client, owner, did):
    return client.get(f"/deliverables/{did}/client-report.pdf", headers=auth_header(owner))


class TestTheGateItself:
    """Unit-level, so the two refusal messages are pinned independently of the wiring."""

    def test_a_non_production_record_is_exempt(self) -> None:
        """Demo and sandbox records self-approve under ADR-0029 and carry the GRS-0229 watermark on
        every rendition. The watermark IS their gate; founder review would spend attention on work
        that is not going anywhere."""
        assert_report_founder_approved(None, non_production=True)

    def test_an_unapproved_production_report_is_refused_with_the_next_action(self) -> None:
        with pytest.raises(ReportApprovalPendingError) as exc:
            assert_report_founder_approved(None, non_production=False)
        message = str(exc.value)
        assert "has not been signed off" in message
        assert "Send it for review" in message

    def test_an_edited_report_says_so_and_names_the_sections(self) -> None:
        """A different problem from "never submitted", with a different next action — so it gets a
        different sentence rather than one message covering both."""
        with pytest.raises(ReportApprovalPendingError) as exc:
            assert_report_founder_approved(
                None,
                non_production=False,
                changed_sections=("constraint", "value"),
                ever_approved=True,
            )
        message = str(exc.value)
        assert "approved and then edited" in message
        assert "constraint, value" in message

    def test_an_approval_lets_it_through(self) -> None:
        assert_report_founder_approved(object(), non_production=False)


class TestTheProductionPath:
    def test_both_release_paths_refuse_before_approval(
        self, client, alice: SeededConsultant, production_report: str
    ) -> None:
        """The gap, now closed. Both paths, because gating one of two equivalent routes is exactly
        how this happened: the docx pack was gated and the client report was not."""
        assert _pdf(client, alice, production_report).status_code == 409
        assert _issue(client, alice, production_report).status_code == 409

    def test_the_refusal_teaches(
        self, client, alice: SeededConsultant, production_report: str
    ) -> None:
        detail = _issue(client, alice, production_report).json()["detail"]
        assert "founder" in detail.lower()
        assert "review" in detail.lower()
        assert "409" not in detail

    def test_approval_releases_both_paths(
        self,
        client,
        alice: SeededConsultant,
        founder: SeededConsultant,
        production_report: str,
    ) -> None:
        approved = client.post(
            f"/deliverables/{production_report}/report-approval",
            headers=auth_header(founder),
        )
        assert approved.status_code == 201, approved.text
        assert _pdf(client, alice, production_report).status_code == 200
        assert _issue(client, alice, production_report).status_code == 201

    def test_editing_prose_after_approval_refuses_again(
        self,
        client,
        alice: SeededConsultant,
        founder: SeededConsultant,
        production_report: str,
    ) -> None:
        """Hash invalidation — the same rule the Founder-review tab already states for assessments.
        This is the test that matters most: without it the gate is a one-time formality an advisor
        clears and then rewrites behind."""
        client.post(
            f"/deliverables/{production_report}/report-approval", headers=auth_header(founder)
        )
        assert _issue(client, alice, production_report).status_code == 201

        client.put(
            f"/deliverables/{production_report}/report-prose",
            json={"sections": _prose({"constraint": "Rewritten after the founder signed it off."})},
            headers=auth_header(alice),
        )
        refused = _issue(client, alice, production_report)
        assert refused.status_code == 409
        assert "edited" in refused.json()["detail"]

    def test_only_the_founder_may_approve(
        self, client, alice: SeededConsultant, production_report: str
    ) -> None:
        """Not the advisor who owns it. An advisor-approvable gate is self-approval with extra
        steps, which is the thing ADR-0041 exists to prevent."""
        refused = client.post(
            f"/deliverables/{production_report}/report-approval", headers=auth_header(alice)
        )
        assert refused.status_code == 403


class TestNonProductionRecordsAreUnaffected:
    def test_a_sandbox_report_still_issues_without_review(
        self, client, alice: SeededConsultant
    ) -> None:
        """The advisor's preview path must keep working — it is how they see what a client sees,
        and GRS-0229 marks it on every screen."""
        did = sandbox_deliverable_with_run(client, alice)
        client.put(
            f"/deliverables/{did}/report-prose",
            json={"sections": _prose()},
            headers=auth_header(alice),
        )
        created = _issue(client, alice, did)
        assert created.status_code == 201, created.text
        payload = client.get(f"/shared/report/{created.json()['token']}").json()
        assert payload["non_production"] is True


class TestTheQueue:
    def test_a_submitted_report_appears_beside_assessments(
        self,
        client,
        alice: SeededConsultant,
        founder: SeededConsultant,
        production_report: str,
    ) -> None:
        submitted = client.post(
            f"/deliverables/{production_report}/submit-report-for-review",
            headers=auth_header(alice),
        )
        assert submitted.status_code == 204, submitted.text
        queue = client.get("/founder-review/queue", headers=auth_header(founder)).json()
        mine = [e for e in queue if e["deliverable_id"] == production_report]
        assert len(mine) == 1
        assert mine[0]["changed_sections"] == []  # first review: nothing to diff against

    def test_a_re_review_names_the_sections_that_changed(
        self,
        client,
        alice: SeededConsultant,
        founder: SeededConsultant,
        production_report: str,
    ) -> None:
        """Scope 4's diff. A hash can say "this differs"; it cannot say which of the six sections
        the founder needs to re-read, which is the difference between a queue entry that helps and
        one that just reopens the work."""
        client.post(
            f"/deliverables/{production_report}/report-approval", headers=auth_header(founder)
        )
        client.put(
            f"/deliverables/{production_report}/report-prose",
            json={"sections": _prose({"value": "A different account of what it is worth."})},
            headers=auth_header(alice),
        )
        client.post(
            f"/deliverables/{production_report}/submit-report-for-review",
            headers=auth_header(alice),
        )
        queue = client.get("/founder-review/queue", headers=auth_header(founder)).json()
        entry = next(e for e in queue if e["deliverable_id"] == production_report)
        assert entry["changed_sections"] == ["value"]
        assert entry["previously_approved"] is True

    def test_an_approved_report_leaves_the_queue(
        self,
        client,
        alice: SeededConsultant,
        founder: SeededConsultant,
        production_report: str,
    ) -> None:
        client.post(
            f"/deliverables/{production_report}/submit-report-for-review",
            headers=auth_header(alice),
        )
        client.post(
            f"/deliverables/{production_report}/report-approval", headers=auth_header(founder)
        )
        queue = client.get("/founder-review/queue", headers=auth_header(founder)).json()
        assert [e for e in queue if e["deliverable_id"] == production_report] == []

    def test_a_sandbox_report_never_enters_the_queue(
        self, client, alice: SeededConsultant, founder: SeededConsultant
    ) -> None:
        did = sandbox_deliverable_with_run(client, alice)
        client.put(
            f"/deliverables/{did}/report-prose",
            json={"sections": _prose()},
            headers=auth_header(alice),
        )
        client.post(f"/deliverables/{did}/submit-report-for-review", headers=auth_header(alice))
        queue = client.get("/founder-review/queue", headers=auth_header(founder)).json()
        assert [e for e in queue if e["deliverable_id"] == did] == []
