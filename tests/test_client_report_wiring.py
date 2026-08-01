"""The client report, reachable from the app (GRS-0219/0220 wiring).

GRS-0211/0219/0220 each shipped something that could not be opened: the content model takes prose as
an input, nothing stored prose, so nothing could assemble a report to render or share. These tests
are the proof that the loop is closed — an advisor writes six sections, downloads a branded PDF, and
issues a link a client can open.

The refusals matter as much as the happy path. A report with unwritten sections must not render as
blanks that look finished, and an internal draft must not download unmarked.
"""

from __future__ import annotations

import io

import pypdf
import pytest
from bcap_contracts.client_report import SECTION_ORDER

from grassmarket.deliverables.gate import DRAFT_WATERMARK
from tests.client_report_helpers import deliverable_with_run, written_prose
from tests.conftest import SeededConsultant, auth_header


@pytest.fixture
def deliverable(client, alice: SeededConsultant, founder: SeededConsultant) -> str:
    return deliverable_with_run(client, alice, founder)


def _write_prose(client, alice: SeededConsultant, deliverable: str, sections: dict | None = None):
    return client.put(
        f"/deliverables/{deliverable}/report-prose",
        json={"sections": sections if sections is not None else written_prose()},
        headers=auth_header(alice),
    )


def _approve_report(client, founder: SeededConsultant, deliverable: str):
    """Since GRS-0245 a production report is not releasable until the founder signs off its PROSE,
    so every test here that expects a PDF or a link has to clear that gate first. Tests that assert
    the gate itself live in `test_report_founder_gate.py`."""
    response = client.post(
        f"/deliverables/{deliverable}/report-approval", headers=auth_header(founder)
    )
    assert response.status_code == 201, response.text
    return response


class TestTheProseTheAdvisorWrites:
    def test_an_unstarted_report_offers_the_shape_not_a_blank_page(
        self, client, alice: SeededConsultant, deliverable: str
    ) -> None:
        body = client.get(
            f"/deliverables/{deliverable}/report-prose", headers=auth_header(alice)
        ).json()
        assert body["written"] is False
        # The six sections in order, so the advisor sees the argument they are asked to make.
        assert list(body["sections"].keys()) == [k.value for k in SECTION_ORDER]
        assert body["sections"]["business"]["heading"] == "The business"
        assert body["sections"]["business"]["body"] == []

    def test_saving_then_reading_round_trips(
        self, client, alice: SeededConsultant, deliverable: str
    ) -> None:
        assert _write_prose(client, alice, deliverable).status_code == 200
        body = client.get(
            f"/deliverables/{deliverable}/report-prose", headers=auth_header(alice)
        ).json()
        assert body["written"] is True
        assert body["sections"]["value"]["body"] == ["What a consultant wrote about value."]

    def test_saving_twice_replaces_rather_than_appends(
        self, client, alice: SeededConsultant, deliverable: str
    ) -> None:
        _write_prose(client, alice, deliverable)
        revised = written_prose()
        revised["business"]["body"] = ["A second draft."]
        _write_prose(client, alice, deliverable, revised)
        body = client.get(
            f"/deliverables/{deliverable}/report-prose", headers=auth_header(alice)
        ).json()
        assert body["sections"]["business"]["body"] == ["A second draft."]

    def test_prose_is_self_scoped(
        self, client, alice: SeededConsultant, bob: SeededConsultant, deliverable: str
    ) -> None:
        assert (
            client.get(
                f"/deliverables/{deliverable}/report-prose", headers=auth_header(bob)
            ).status_code
            == 404
        )
        assert _write_prose(client, bob, deliverable).status_code == 404


class TestTheDownloadableReport:
    def test_a_written_report_downloads_as_a_pdf(
        self, client, alice: SeededConsultant, deliverable: str, founder: SeededConsultant
    ) -> None:
        _write_prose(client, alice, deliverable)
        _approve_report(client, founder, deliverable)
        response = client.get(
            f"/deliverables/{deliverable}/client-report.pdf", headers=auth_header(alice)
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF-")
        assert "attachment" in response.headers["content-disposition"]

    def test_the_pdf_carries_the_advisors_words(
        self, client, alice: SeededConsultant, deliverable: str, founder: SeededConsultant
    ) -> None:
        _write_prose(client, alice, deliverable)
        _approve_report(client, founder, deliverable)
        pdf = client.get(
            f"/deliverables/{deliverable}/client-report.pdf", headers=auth_header(alice)
        ).content
        text = " ".join(
            (page.extract_text() or "") for page in pypdf.PdfReader(io.BytesIO(pdf)).pages
        )
        assert "What a consultant wrote about business" in " ".join(text.split())

    def test_an_unwritten_report_refuses_and_says_so(
        self, client, alice: SeededConsultant, deliverable: str
    ) -> None:
        # Blanks that look finished are the failure mode; a 409 naming the problem is the fix.
        response = client.get(
            f"/deliverables/{deliverable}/client-report.pdf", headers=auth_header(alice)
        )
        assert response.status_code == 409
        assert "no prose yet" in response.json()["detail"]

    def test_a_partly_written_report_names_the_missing_sections(
        self, client, alice: SeededConsultant, deliverable: str
    ) -> None:
        partial = written_prose()
        partial["constraint"]["body"] = []
        partial["value"]["body"] = ["   "]  # whitespace is not writing
        _write_prose(client, alice, deliverable, partial)
        response = client.get(
            f"/deliverables/{deliverable}/client-report.pdf", headers=auth_header(alice)
        )
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert "constraint" in detail and "value" in detail

    def test_an_undeclared_number_explains_itself_instead_of_500ing(
        self, client, alice: SeededConsultant, deliverable: str
    ) -> None:
        # The content model refusing prose is NORMAL and useful. Surfacing it as a 500 made a
        # working guardrail look like a broken app — found by driving the real page in a browser.
        sections = written_prose()
        sections["business"]["body"] = ["We found 3 issues worth fixing."]
        _write_prose(client, alice, deliverable, sections)
        response = client.get(
            f"/deliverables/{deliverable}/client-report.pdf", headers=auth_header(alice)
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "without declaring it" in detail
        assert "Value error" not in detail, "pydantic's wrapping should not reach the advisor"

    def test_an_internal_draft_downloads_watermarked(
        self, client, alice: SeededConsultant, deliverable: str, founder: SeededConsultant
    ) -> None:
        # The generated deliverable is DRAFT_INTERNAL (client_facing=False), and the watermark
        # follows the deliverable's own mode rather than anything the caller chooses (ADR-0029).
        _write_prose(client, alice, deliverable)
        _approve_report(client, founder, deliverable)
        pdf = client.get(
            f"/deliverables/{deliverable}/client-report.pdf", headers=auth_header(alice)
        ).content
        first_page = pypdf.PdfReader(io.BytesIO(pdf)).pages[0].extract_text() or ""
        assert DRAFT_WATERMARK in " ".join(first_page.split())

    def test_the_pdf_is_self_scoped(
        self, client, alice: SeededConsultant, bob: SeededConsultant, deliverable: str
    ) -> None:
        _write_prose(client, alice, deliverable)
        assert (
            client.get(
                f"/deliverables/{deliverable}/client-report.pdf", headers=auth_header(bob)
            ).status_code
            == 404
        )


class TestTheApprovalGateIsActuallyWired:
    """Non-negotiable #8 on the path that reaches a client, not only in the model's own tests.

    Every section is consultant-written today, so the gate passes trivially — which is exactly why
    it needed wiring NOW. GRS-0222 will start drafting sections, and a gate added at that point is
    a gate that was missing in between.
    """

    def test_the_download_path_calls_the_gate(
        self,
        client,
        alice: SeededConsultant,
        deliverable: str,
        founder: SeededConsultant,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        called: list[set] = []
        import grassmarket.web.routers.client_report as module

        real = module.assert_client_ready

        def spy(report, *, approved_narrative_ids):
            called.append(approved_narrative_ids)
            return real(report, approved_narrative_ids=approved_narrative_ids)

        monkeypatch.setattr(module, "assert_client_ready", spy)
        _write_prose(client, alice, deliverable)
        _approve_report(client, founder, deliverable)
        response = client.get(
            f"/deliverables/{deliverable}/client-report.pdf", headers=auth_header(alice)
        )
        assert response.status_code == 200
        assert called, "the client-facing download did not consult the approval gate"

    def test_both_release_paths_call_the_founder_gate(
        self,
        client,
        alice: SeededConsultant,
        founder: SeededConsultant,
        deliverable: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """GRS-0245 test-plan item 2: the same spy discipline, extended to the founder gate.

        A gate is only a gate while something fails when it is removed. This one is spied on BOTH
        release paths rather than one, because gating a single route of two equivalent ones is
        precisely how the gap this closes came about — the docx pack consulted founder approval and
        the client report did not.
        """
        import grassmarket.web.routers.client_report as module

        called: list[str] = []
        real = module.assert_report_releasable

        def spy(repo, principal, deliverable_id, provenance):
            called.append(str(deliverable_id))
            return real(repo, principal, deliverable_id, provenance)

        monkeypatch.setattr(module, "assert_report_releasable", spy)
        import grassmarket.web.routers.report_links as links_module

        monkeypatch.setattr(links_module, "assert_report_releasable", spy)

        _write_prose(client, alice, deliverable)
        _approve_report(client, founder, deliverable)

        assert (
            client.get(
                f"/deliverables/{deliverable}/client-report.pdf", headers=auth_header(alice)
            ).status_code
            == 200
        )
        assert called, "the PDF download did not consult the founder gate"

        called.clear()
        assert (
            client.post(
                f"/deliverables/{deliverable}/links",
                json={"recipient_label": "CFO"},
                headers=auth_header(alice),
            ).status_code
            == 201
        )
        assert called, "issuing a share link did not consult the founder gate"

    def test_an_unapproved_ai_section_is_refused(
        self, client, alice: SeededConsultant, deliverable: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Simulate what GRS-0222 will produce: a section marked AI-drafted whose narrative nobody
        # approved. It must not reach a client.
        from uuid import uuid4

        import grassmarket.web.routers.client_report as module
        from grassmarket.deliverables.client_report import SectionProse

        real_assemble = module.assemble

        def taint(context, *, scoring_run_id, sections_json):
            assembled = real_assemble(
                context, scoring_run_id=scoring_run_id, sections_json=sections_json
            )
            tainted = assembled.report.model_copy(
                update={
                    "sections": [
                        s.model_copy(update={"ai_drafted": True, "narrative_id": uuid4()})
                        if s.kind.value == "business"
                        else s
                        for s in assembled.report.sections
                    ]
                }
            )
            return type(assembled)(report=tainted, figures=assembled.figures)

        monkeypatch.setattr(module, "assemble", taint)
        _write_prose(client, alice, deliverable)
        response = client.get(
            f"/deliverables/{deliverable}/client-report.pdf", headers=auth_header(alice)
        )
        assert response.status_code == 409
        assert "unapproved AI-drafted" in response.json()["detail"]
        assert SectionProse  # keeps the import meaningful to a reader


class TestTheLoopIsClosed:
    def test_write_share_and_read_end_to_end(
        self, client, alice: SeededConsultant, deliverable: str, founder: SeededConsultant
    ) -> None:
        """The founder's acceptance test, as far as an API can carry it."""
        _write_prose(client, alice, deliverable)
        _approve_report(client, founder, deliverable)

        created = client.post(
            f"/deliverables/{deliverable}/links",
            json={"recipient_label": "cfo@client.example"},
            headers=auth_header(alice),
        )
        assert created.status_code == 201, created.text
        token = created.json()["token"]

        # The client opens it — no login, no session.
        page = client.get(f"/shared/report/{token}")
        assert page.status_code == 200
        served = page.json()
        assert [s["kind"] for s in served["report"]["sections"]] == [k.value for k in SECTION_ORDER]
        assert "What a consultant wrote about business." in served["report"]["sections"][0]["body"]

        # ...reads two sections...
        for section in ("business", "value"):
            assert (
                client.post(
                    f"/shared/report/{token}/events", json={"section": section, "dwell_ms": 3000}
                ).status_code
                == 204
            )

        # ...and the advisor can see what they read before the follow-up call.
        summary = client.get(
            f"/report-links/{created.json()['link']['id']}/reads", headers=auth_header(alice)
        ).json()
        opened = {s["section"] for s in summary["sections"] if s["views"] > 0}
        assert opened == {"business", "value"}

    def test_the_pdf_and_the_web_page_say_the_same_thing(
        self, client, alice: SeededConsultant, deliverable: str, founder: SeededConsultant
    ) -> None:
        """Content parity: one model, two renditions, or they disagree in front of a client."""
        _write_prose(client, alice, deliverable)
        _approve_report(client, founder, deliverable)
        created = client.post(
            f"/deliverables/{deliverable}/links",
            json={"recipient_label": "cfo@client.example"},
            headers=auth_header(alice),
        )
        served = client.get(f"/shared/report/{created.json()['token']}").json()
        pdf = client.get(
            f"/deliverables/{deliverable}/client-report.pdf", headers=auth_header(alice)
        ).content
        pdf_text = " ".join(
            " ".join((page.extract_text() or "").split())
            for page in pypdf.PdfReader(io.BytesIO(pdf)).pages
        )
        for section in served["report"]["sections"]:
            for paragraph in section["body"]:
                assert paragraph in pdf_text, (
                    f"the web page says something the PDF does not: {paragraph}"
                )

    def test_the_snapshot_does_not_move_when_the_prose_is_edited_later(
        self, client, alice: SeededConsultant, deliverable: str, founder: SeededConsultant
    ) -> None:
        # A client who read this last week and quotes it back must be quoting something that still
        # exists. Editing the prose changes the NEXT link, not one already sent.
        _write_prose(client, alice, deliverable)
        _approve_report(client, founder, deliverable)
        created = client.post(
            f"/deliverables/{deliverable}/links",
            json={"recipient_label": "cfo@client.example"},
            headers=auth_header(alice),
        )
        token = created.json()["token"]

        revised = written_prose()
        revised["business"]["body"] = ["Completely rewritten after the fact."]
        _write_prose(client, alice, deliverable, revised)

        served = client.get(f"/shared/report/{token}").json()
        assert served["report"]["sections"][0]["body"] == [
            "What a consultant wrote about business."
        ]
