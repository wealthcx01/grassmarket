"""Shared client-report links and disclosed read tracking (GRS-0220).

The link is the credential, so most of this file is about what the public surface must NOT do:
resolve a revoked link, reveal that a link once existed, be guessable, or be readable from a
database backup. The ticket's own wording — "revoking a link makes it stop working immediately, and
that is tested" — is the test named `test_revocation_is_immediate`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from bcap_contracts.client_report import SECTION_ORDER, ReportSectionKind
from sqlalchemy import text

from grassmarket.deliverables.report_links import (
    MAX_EXPIRY,
    ExpiryTooLongError,
    LinkNotUsableError,
    assert_usable,
    generate_token,
    hash_token,
    resolve_expiry,
)
from tests.client_report_helpers import deliverable_with_run, written_prose
from tests.conftest import SeededConsultant, auth_header


@pytest.fixture
def deliverable_id(client, alice: SeededConsultant, founder: SeededConsultant) -> str:
    """A deliverable bound to a REAL finalised run.

    Issuing a link assembles the report server-side, so a bare deliverable row is no longer enough:
    there has to be a run to quote. The prose is written too, because a report with unwritten
    sections refuses to assemble — which is itself tested, in `test_client_report_wiring.py`.
    """
    did = deliverable_with_run(client, alice, founder)
    response = client.put(
        f"/deliverables/{did}/report-prose",
        json={"sections": written_prose()},
        headers=auth_header(alice),
    )
    assert response.status_code == 200, response.text
    return did


def _instant(stamp: str) -> datetime:
    """Parse an API timestamp to an aware instant, so two spellings of one moment compare equal."""
    parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _create_link(client, advisor: SeededConsultant, deliverable_id: str, **extra) -> dict:
    body = {"recipient_label": "cfo@example.com", **extra}
    response = client.post(
        f"/deliverables/{deliverable_id}/links", json=body, headers=auth_header(advisor)
    )
    assert response.status_code == 201, response.text
    return response.json()


class TestTheTokenIsTheCredential:
    def test_only_a_hash_is_stored(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        # A leaked backup must yield no working links, the same reason a password column hashes.
        created = _create_link(client, alice, deliverable_id)
        token = created["token"]
        assert created["link"]["token_hash"] == hash_token(token)
        assert token not in created["link"]["token_hash"]
        assert len(created["link"]["token_hash"]) == 64

    def test_tokens_are_unguessable_and_unique(self) -> None:
        tokens = {generate_token() for _ in range(200)}
        assert len(tokens) == 200
        assert all(len(t) >= 40 for t in tokens)

    def test_a_token_survives_being_pasted_anywhere(self) -> None:
        """The first link ever sent for review arrived broken, and this is why.

        `secrets.token_urlsafe` emits `-` and `_`. A link is something a human pastes — into an
        email, a chat message, a markdown note — and a renderer that treats `_word_` as emphasis
        eats the underscores. The client then gets a URL that resolves to "this report is not
        available", which is indistinguishable (by design) from a revoked link. Hex cannot be
        mangled by any formatter.
        """
        for token in (generate_token() for _ in range(50)):
            assert token.isalnum(), f"{token} contains punctuation a formatter can eat"
            assert (
                token.islower() or token.isdigit() or all(c in "0123456789abcdef" for c in token)
            ), f"{token} is not plain hex"

    def test_the_plaintext_is_returned_exactly_once(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        _create_link(client, alice, deliverable_id)
        listed = client.get(
            f"/deliverables/{deliverable_id}/links", headers=auth_header(alice)
        ).json()
        assert listed, "the link should be listed"
        assert "token" not in listed[0], "listing a link must never re-reveal its token"


class TestThePublicSurfaceRevealsNothing:
    def test_an_unknown_token_is_a_plain_404(self, client) -> None:
        response = client.get("/shared/report/not-a-real-token")
        assert response.status_code == 404

    def test_revoked_and_unknown_are_indistinguishable(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        # Otherwise the endpoint tells a prober that a link existed and was withdrawn.
        created = _create_link(client, alice, deliverable_id)
        client.post(f"/report-links/{created['link']['id']}/revoke", headers=auth_header(alice))
        revoked = client.get(f"/shared/report/{created['token']}")
        unknown = client.get("/shared/report/definitely-not-a-token")
        assert revoked.status_code == unknown.status_code == 404
        assert revoked.json() == unknown.json()

    def test_the_shared_report_needs_no_login(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        created = _create_link(client, alice, deliverable_id)
        response = client.get(f"/shared/report/{created['token']}")  # no auth header at all
        assert response.status_code == 200
        assert response.json()["report"]["subject"] == "Meridian"


class TestRevocationAndExpiry:
    def test_revocation_is_immediate(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        """The ticket's wording: revoking makes it stop working immediately, and that is tested."""
        created = _create_link(client, alice, deliverable_id)
        token = created["token"]
        assert client.get(f"/shared/report/{token}").status_code == 200

        client.post(f"/report-links/{created['link']['id']}/revoke", headers=auth_header(alice))

        assert client.get(f"/shared/report/{token}").status_code == 404
        assert (
            client.post(
                f"/shared/report/{token}/events", json={"section": "business", "dwell_ms": 10}
            ).status_code
            == 404
        )

    def test_revoking_twice_keeps_the_first_timestamp(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        created = _create_link(client, alice, deliverable_id)
        link_id = created["link"]["id"]
        first = client.post(f"/report-links/{link_id}/revoke", headers=auth_header(alice)).json()
        second = client.post(f"/report-links/{link_id}/revoke", headers=auth_header(alice)).json()
        # Compared as instants, not strings: the first response serialises the aware datetime it
        # just wrote ("...Z"), the second serialises what SQLite read back (naive). Same moment,
        # different spelling — a local-store artifact, not a behaviour difference.
        assert _instant(first["revoked_at"]) == _instant(second["revoked_at"])

    def test_an_expired_link_stops_resolving(
        self, client, alice: SeededConsultant, deliverable_id: str, session_factory
    ) -> None:
        created = _create_link(client, alice, deliverable_id)
        # Wind the clock forward by moving the expiry into the past — what time doing its job
        # looks like from the database's side.
        session = session_factory()
        try:
            session.execute(
                text("UPDATE client_report_links SET expires_at = :past"),
                {"past": datetime.now(UTC) - timedelta(days=1)},
            )
            session.commit()
        finally:
            session.close()
        assert client.get(f"/shared/report/{created['token']}").status_code == 404

    def test_an_over_long_expiry_is_refused_not_clamped(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        # Silently clamping would leave the advisor believing the wrong thing about client access.
        response = client.post(
            f"/deliverables/{deliverable_id}/links",
            json={
                "recipient_label": "cfo@example.com",
                "expires_in_days": MAX_EXPIRY.days + 1,
            },
            headers=auth_header(alice),
        )
        assert response.status_code == 422
        assert "at most" in response.json()["detail"]

    def test_resolve_expiry_refuses_a_non_positive_lifetime(self) -> None:
        with pytest.raises(ExpiryTooLongError):
            resolve_expiry(now=datetime.now(UTC), requested=timedelta(0))

    def test_assert_usable_names_the_state(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        from bcap_contracts.report_links import ClientReportLink

        link = ClientReportLink.model_validate(_create_link(client, alice, deliverable_id)["link"])
        assert_usable(link)  # active — no raise
        revoked = link.model_copy(update={"revoked_at": datetime.now(UTC)})
        with pytest.raises(LinkNotUsableError) as excinfo:
            assert_usable(revoked)
        assert excinfo.value.state.value == "revoked"


class TestScoping:
    def test_another_advisor_cannot_share_your_deliverable(
        self, client, alice: SeededConsultant, bob: SeededConsultant, deliverable_id: str
    ) -> None:
        response = client.post(
            f"/deliverables/{deliverable_id}/links",
            json={"recipient_label": "x@example.com"},
            headers=auth_header(bob),
        )
        assert response.status_code == 404

    def test_another_advisor_cannot_revoke_or_read_your_link(
        self, client, alice: SeededConsultant, bob: SeededConsultant, deliverable_id: str
    ) -> None:
        created = _create_link(client, alice, deliverable_id)
        link_id = created["link"]["id"]
        assert (
            client.post(f"/report-links/{link_id}/revoke", headers=auth_header(bob)).status_code
            == 404
        )
        assert (
            client.get(f"/report-links/{link_id}/reads", headers=auth_header(bob)).status_code
            == 404
        )

    def test_link_listing_is_self_scoped(
        self, client, alice: SeededConsultant, bob: SeededConsultant, deliverable_id: str
    ) -> None:
        _create_link(client, alice, deliverable_id)
        assert (
            client.get(
                f"/deliverables/{deliverable_id}/links", headers=auth_header(bob)
            ).status_code
            == 404
        )


class TestReadTracking:
    def test_events_record_against_the_link_and_reach_the_advisor(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        created = _create_link(client, alice, deliverable_id)
        token, link_id = created["token"], created["link"]["id"]

        for section, dwell in [("business", 4000), ("business", 2500), ("value", 9000)]:
            assert (
                client.post(
                    f"/shared/report/{token}/events", json={"section": section, "dwell_ms": dwell}
                ).status_code
                == 204
            )

        summary = client.get(f"/report-links/{link_id}/reads", headers=auth_header(alice)).json()
        by_section = {s["section"]: s for s in summary["sections"]}
        assert by_section["business"]["views"] == 2
        assert by_section["business"]["total_dwell_ms"] == 6500
        assert by_section["value"]["views"] == 1
        # A section nobody opened reads as zero, not as absent — "they skipped it" is information.
        assert by_section["appendix"]["views"] == 0
        assert by_section["appendix"]["first_viewed_at"] is None

    def test_every_section_appears_in_the_summary(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        created = _create_link(client, alice, deliverable_id)
        summary = client.get(
            f"/report-links/{created['link']['id']}/reads", headers=auth_header(alice)
        ).json()
        assert [s["section"] for s in summary["sections"]] == [k.value for k in SECTION_ORDER]

    def test_an_implausible_dwell_is_refused(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        # A tab left open overnight is not reading; it must not tell the advisor a client studied
        # the appendix for nine hours.
        created = _create_link(client, alice, deliverable_id)
        response = client.post(
            f"/shared/report/{created['token']}/events",
            json={"section": "appendix", "dwell_ms": 9 * 60 * 60 * 1000},
        )
        assert response.status_code == 422

    def test_an_unknown_section_is_refused(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        created = _create_link(client, alice, deliverable_id)
        response = client.post(
            f"/shared/report/{created['token']}/events",
            json={"section": "not-a-section", "dwell_ms": 100},
        )
        assert response.status_code == 422

    def test_opening_the_report_stamps_last_viewed(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        created = _create_link(client, alice, deliverable_id)
        assert created["link"]["last_viewed_at"] is None
        client.get(f"/shared/report/{created['token']}")
        listed = client.get(
            f"/deliverables/{deliverable_id}/links", headers=auth_header(alice)
        ).json()
        assert listed[0]["last_viewed_at"] is not None


class TestTheSnapshot:
    def test_the_shared_page_serves_what_was_shared(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        # A client who read this last week and quotes it back must be quoting something that still
        # exists — so the link serves the snapshot taken at issue, not a fresh render.
        created = _create_link(client, alice, deliverable_id)
        served = client.get(f"/shared/report/{created['token']}").json()
        assert [s["kind"] for s in served["report"]["sections"]] == [k.value for k in SECTION_ORDER]
        assert served["figures"]["maturity"]["labels"], "the radar series should be populated"

    def test_the_page_carries_its_tracking_notice(
        self, client, alice: SeededConsultant, deliverable_id: str
    ) -> None:
        # Disclosure is a product requirement: no covert tracking.
        created = _create_link(client, alice, deliverable_id)
        served = client.get(f"/shared/report/{created['token']}").json()
        assert "which sections of this report you open" in served["tracking_notice"]

    def test_a_report_with_unwritten_sections_cannot_be_shared(
        self, client, alice: SeededConsultant, founder: SeededConsultant
    ) -> None:
        # The report is assembled SERVER-side, so a half-written one cannot be shared by posting a
        # hand-made payload — there is no payload to post.
        bare = deliverable_with_run(client, alice, founder)
        response = client.post(
            f"/deliverables/{bare}/links",
            json={"recipient_label": "cfo@example.com"},
            headers=auth_header(alice),
        )
        assert response.status_code == 409
        assert "has no prose yet" in response.json()["detail"]


def test_report_section_kinds_round_trip() -> None:
    """The tracking API speaks the content model's section vocabulary, not a parallel one."""
    assert {k.value for k in SECTION_ORDER} == {k.value for k in ReportSectionKind}
