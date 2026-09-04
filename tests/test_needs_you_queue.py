"""The one needs-you queue (GRS-0253).

`GET /queue` answers *what is waiting on me?* for the caller. Four surfaces used to compose the
same merge themselves, so the rail badge could show a number the page it linked to disagreed with.

What these tests hold in place:

1. **One count.** The badge and the page read the same list, because there is only one list.
2. **A source the caller has no role in contributes nothing — it does not 403 the whole queue.**
   Everyone may ask what is waiting on them; for most advisors the honest answer is just short.
3. **Sent means gone.** A signed-off report that has been shared leaves the queue; revoking the
   link puts it back, because the advisor has un-sent it.
4. **Dormant sources are named.** Peer rating is retired under ADR-0041. A queue that omitted it
   silently would make "that source is off" look identical to "you are up to date".
"""

from __future__ import annotations

from tests.client_report_helpers import deliverable_with_run, written_prose
from tests.conftest import SeededConsultant, auth_header


def _queue(client, who: SeededConsultant) -> dict:
    resp = client.get("/queue", headers=auth_header(who))
    assert resp.status_code == 200, resp.text
    return resp.json()


def _write_prose(client, who: SeededConsultant, deliverable: str) -> None:
    resp = client.put(
        f"/deliverables/{deliverable}/report-prose",
        json={"sections": written_prose()},
        headers=auth_header(who),
    )
    assert resp.status_code in (200, 201), resp.text


def _approve_report(client, founder: SeededConsultant, deliverable: str) -> dict:
    resp = client.post(f"/deliverables/{deliverable}/report-approval", headers=auth_header(founder))
    assert resp.status_code == 201, resp.text
    return resp.json()


def _share(client, who: SeededConsultant, deliverable: str) -> str:
    resp = client.post(
        f"/deliverables/{deliverable}/links",
        json={"recipient_label": "The client"},
        headers=auth_header(who),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["link"]["id"]


class TestEveryoneMayAskWhatIsWaitingOnThem:
    def test_a_plain_advisor_gets_a_queue_not_a_403(self, client, alice: SeededConsultant) -> None:
        """The founder-review source refuses anyone but the founder. Letting that refusal escape
        would make the queue unusable for every advisor in the network."""
        body = _queue(client, alice)
        assert body["items"] == []
        assert body["generated_at"]

    def test_an_advisor_sees_nothing_of_another_advisors_work(
        self, client, alice: SeededConsultant, bob: SeededConsultant, founder: SeededConsultant
    ) -> None:
        """Non-negotiable #9. Alice's sendable report is Alice's business."""
        deliverable = deliverable_with_run(client, alice, founder)
        _write_prose(client, alice, deliverable)
        _approve_report(client, founder, deliverable)

        assert len(_queue(client, alice)["items"]) == 1
        assert _queue(client, bob)["items"] == []


class TestTheSendKind:
    def test_a_signed_off_report_that_has_not_been_sent_is_waiting_on_the_advisor(
        self, client, alice: SeededConsultant, founder: SeededConsultant
    ) -> None:
        """The kind nothing covered before this ticket, and the quietest way for work to stall: it
        looks finished everywhere, because it is — it just never left."""
        deliverable = deliverable_with_run(client, alice, founder)
        _write_prose(client, alice, deliverable)
        assert _queue(client, alice)["items"] == [], "not signed off yet — waiting on the founder"

        _approve_report(client, founder, deliverable)
        items = _queue(client, alice)["items"]
        assert len(items) == 1
        assert items[0]["kind"] == "send"
        assert items[0]["target"] == "client_report"
        assert items[0]["target_id"] == deliverable
        assert "has not been sent" in items[0]["reason"]

    def test_the_clock_starts_when_it_became_sendable(
        self, client, alice: SeededConsultant, founder: SeededConsultant
    ) -> None:
        """Waited-time is how long it has been *sendable*, not how long the record has existed. A
        clock started at creation would overstate every row on the screen."""
        deliverable = deliverable_with_run(client, alice, founder)
        _write_prose(client, alice, deliverable)
        approval = _approve_report(client, founder, deliverable)

        item = _queue(client, alice)["items"][0]
        assert item["became_actionable_at"][:19] == approval["approved_at"][:19]

    def test_sending_it_takes_it_off_the_queue(
        self, client, alice: SeededConsultant, founder: SeededConsultant
    ) -> None:
        deliverable = deliverable_with_run(client, alice, founder)
        _write_prose(client, alice, deliverable)
        _approve_report(client, founder, deliverable)
        assert len(_queue(client, alice)["items"]) == 1

        _share(client, alice, deliverable)
        assert _queue(client, alice)["items"] == []

    def test_revoking_the_link_puts_it_back(
        self, client, alice: SeededConsultant, founder: SeededConsultant
    ) -> None:
        """An advisor who revoked a link has un-sent the report. The queue agrees with them."""
        deliverable = deliverable_with_run(client, alice, founder)
        _write_prose(client, alice, deliverable)
        _approve_report(client, founder, deliverable)
        link_id = _share(client, alice, deliverable)
        assert _queue(client, alice)["items"] == []

        revoked = client.post(f"/report-links/{link_id}/revoke", headers=auth_header(alice))
        assert revoked.status_code == 200, revoked.text
        assert len(_queue(client, alice)["items"]) == 1

    def test_an_edit_after_sign_off_moves_it_back_to_the_founder(
        self, client, alice: SeededConsultant, founder: SeededConsultant
    ) -> None:
        """An approval is a fact about a hash. Editing the prose breaks the match, so the report is
        waiting on the founder again — not sitting in the advisor's outbox looking ready."""
        deliverable = deliverable_with_run(client, alice, founder)
        _write_prose(client, alice, deliverable)
        _approve_report(client, founder, deliverable)
        assert len(_queue(client, alice)["items"]) == 1

        sections = written_prose()
        sections["business"]["body"] = ["A materially different opening paragraph."]
        edited = client.put(
            f"/deliverables/{deliverable}/report-prose",
            json={"sections": sections},
            headers=auth_header(alice),
        )
        assert edited.status_code in (200, 201), edited.text
        assert _queue(client, alice)["items"] == []


class TestTheApproveKind:
    def test_the_founder_sees_what_is_waiting_on_them(
        self, client, alice: SeededConsultant, founder: SeededConsultant
    ) -> None:
        deliverable = deliverable_with_run(client, alice, founder)
        _write_prose(client, alice, deliverable)
        submitted = client.post(
            f"/deliverables/{deliverable}/submit-report-for-review", headers=auth_header(alice)
        )
        assert submitted.status_code == 204, submitted.text

        items = _queue(client, founder)["items"]
        approvals = [i for i in items if i["kind"] == "approve"]
        assert approvals, f"nothing awaiting the founder: {items}"
        assert approvals[0]["target"] == "client_report"
        assert "signed off" in approvals[0]["reason"]

    def test_the_queue_is_oldest_first(
        self, client, alice: SeededConsultant, founder: SeededConsultant
    ) -> None:
        """The longest-waiting thing is the one most likely to have been forgotten."""
        first = deliverable_with_run(client, alice, founder)
        _write_prose(client, alice, first)
        _approve_report(client, founder, first)
        second = deliverable_with_run(client, alice, founder)
        _write_prose(client, alice, second)
        _approve_report(client, founder, second)

        stamps = [i["became_actionable_at"] for i in _queue(client, alice)["items"]]
        assert stamps == sorted(stamps), stamps


class TestDormantSourcesSaySo:
    def test_peer_rating_is_named_as_dormant_rather_than_silently_missing(
        self, client, alice: SeededConsultant
    ) -> None:
        """An empty queue and a queue whose sources are switched off look the same on screen, and
        only one of them means the advisor can stop looking."""
        body = _queue(client, alice)
        dormant = {d["kind"]: d["reason"] for d in body["dormant"]}
        assert "rate" in dormant
        assert "ADR-0041" in dormant["rate"]

    def test_the_retired_sources_really_are_retired(self, client, alice: SeededConsultant) -> None:
        """The premise of this ticket, pinned. GRS-0253 was written against three endpoints; two of
        them answer 410 Gone, so the queue cannot merge them and says so instead."""
        for path in ("/assessments/rating-requests", "/committee/queue"):
            assert client.get(path, headers=auth_header(alice)).status_code == 410, path
        assert client.get("/founder-review/queue", headers=auth_header(alice)).status_code != 410
