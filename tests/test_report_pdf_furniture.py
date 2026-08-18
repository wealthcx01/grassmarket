"""The furniture around the client report (GRS-0234).

The report body is something Bruntsfield could put its name on; the things around it were not. An
advisor forwards this file to a CFO — the filename, the cover, the footer and the precision of the
headline number are all read by that CFO before a word of the analysis is.
"""

from __future__ import annotations

from datetime import date

import pypdf
import pytest
from bcap_contracts.client_report import (
    COEFFICIENT_STATUS_SENTENCES,
    coefficient_status_sentence,
)

from grassmarket.deliverables.client_report import format_v_display
from grassmarket.deliverables.report_pdf.render import client_report_filename
from tests.client_report_helpers import written_prose
from tests.conftest import SeededConsultant, auth_header


class TestTheFilename:
    """It arrived as `f6312cfe-4310-4dba-8a25-0c2c3bd77a57.pdf` — a database identifier in a CFO's
    inbox. The cause was NOT this string: the browser could not read `Content-Disposition` because
    it was never exposed to it, so the client fell back to the deliverable id."""

    def test_it_names_the_client_and_the_month(self) -> None:
        assert client_report_filename(subject="WeBull", generated_on=date(2026, 8, 4)) == (
            "Bruntsfield — Platform assessment — WeBull — 2026-08.pdf"
        )

    def test_filesystem_hostile_characters_are_stripped(self) -> None:
        """The name crosses a filesystem, an email client and whatever the recipient uses. A slash
        or a colon in it is a broken attachment somewhere."""
        name = client_report_filename(subject="Acme / Co: Ltd", generated_on=date(2026, 8, 4))
        assert "/" not in name.replace(".pdf", "")
        assert ":" not in name
        assert "Acme Co Ltd" in name

    def test_an_empty_subject_still_produces_a_usable_name(self) -> None:
        assert "Client" in client_report_filename(subject="   ", generated_on=date(2026, 8, 4))

    def test_the_download_sends_it_and_never_a_uuid(
        self, client, alice: SeededConsultant, founder: SeededConsultant
    ) -> None:
        from tests.client_report_helpers import deliverable_with_run

        did = deliverable_with_run(client, alice, founder)
        client.put(
            f"/deliverables/{did}/report-prose",
            json={"sections": written_prose()},
            headers=auth_header(alice),
        )
        client.post(f"/deliverables/{did}/report-approval", headers=auth_header(founder))
        response = client.get(f"/deliverables/{did}/client-report.pdf", headers=auth_header(alice))
        assert response.status_code == 200
        disposition = response.headers["content-disposition"]
        assert "Bruntsfield" in disposition
        assert did not in disposition, "the deliverable id must not reach the filename"
        # Both spellings: RFC 5987 for the real name, a plain ASCII fallback for anything that
        # cannot read it. A bare filename= carrying em-dashes is not a valid header.
        assert "filename*=UTF-8''" in disposition
        assert 'filename="' in disposition


class TestTheFooterSaysItInEnglish:
    """`coefficients v1-draft-pending-elicitation` on every page. The provenance honesty is the
    point and it stays; the internal config identifier is not something to put in front of a
    client, and it keeps its place in the appendix's version table."""

    def test_a_draft_set_says_so_plainly(self) -> None:
        assert (
            coefficient_status_sentence(version="v1-draft-pending-elicitation", client_usable=False)
            == COEFFICIENT_STATUS_SENTENCES["draft"]
        )

    def test_an_elicited_set_says_ratification_is_pending(self) -> None:
        assert (
            coefficient_status_sentence(version="v1-elicited", client_usable=True)
            == (COEFFICIENT_STATUS_SENTENCES["elicited"])
        )

    def test_a_ratified_set_says_ratified(self) -> None:
        assert (
            coefficient_status_sentence(version="v1-elicited-ratified", client_usable=True)
            == COEFFICIENT_STATUS_SENTENCES["ratified"]
        )

    def test_a_contradiction_resolves_to_the_weaker_claim(self) -> None:
        """A set that is client-usable and still names itself draft is a contradiction. Resolving
        it upward would let a labelling mistake produce a stronger claim than the evidence."""
        assert (
            coefficient_status_sentence(version="v1-draft", client_usable=True)
            == (COEFFICIENT_STATUS_SENTENCES["draft"])
        )

    def test_no_sentence_leaks_an_identifier(self) -> None:
        """Hyphens are fine — "Expert-elicited" is English. What must not appear is a config
        identifier: a version token, or the underscore/slug shape one is written in."""
        for sentence in COEFFICIENT_STATUS_SENTENCES.values():
            assert "v1" not in sentence.lower()
            assert "_" not in sentence
            assert "pending-elicitation" not in sentence


class TestOneDisplayPrecisionForV:
    """The portfolio quoted 54.7 where the appendix quoted 55 — the same number at two precisions.
    An advisor saying "54.7" to a client holding a page saying "55" is the friction ADR-0040's
    one-number rule exists to prevent, and the rule is about the DISPLAYED number: a reader cannot
    tell rounding from disagreement."""

    @pytest.mark.parametrize(
        ("value", "expected"), [(54.7, "54.7"), (55.0, "55.0"), (54.65, "54.6"), (0.0, "0.0")]
    )
    def test_v_always_shows_one_decimal(self, value: float, expected: str) -> None:
        assert format_v_display(value) == expected

    def test_it_matches_the_precision_the_wizard_already_uses(self) -> None:
        """One decimal rather than zero, because the wizard and the portfolio already use it.
        Rounding the two surfaces an advisor reads daily to match a document they send occasionally
        would be the wrong way round."""
        assert format_v_display(54.7).count(".") == 1
        assert len(format_v_display(54.7).split(".")[1]) == 1


class TestNoInteriorPageIsBlank:
    """GRS-0234 scope 4's regression check.

    It guards the failure that WOULD be catastrophic — an interior page with neither text nor a
    figure, which is a rendering fault rather than a layout preference. It does NOT catch the sparse
    page the ticket reports (~300 characters beside a chart): that page is thin, not empty, and the
    layout fix for it was attempted and measured not to work. See the note in `render.py`.
    """

    def _pages(self, path: str) -> list[tuple[int, int]]:
        reader = pypdf.PdfReader(path)
        return [
            (len((page.extract_text() or "").strip()), len(page.images)) for page in reader.pages
        ]

    @pytest.mark.parametrize(
        "sample",
        [
            "docs/reviews/GRS-0236-demo-example-reports/revolut-platform-assessment.pdf",
            "docs/reviews/GRS-0236-demo-example-reports/hargreaves-lansdown-platform-assessment.pdf",
            "docs/reviews/GRS-0236-demo-example-reports/webull-platform-assessment.pdf",
        ],
    )
    def test_every_interior_page_carries_something(self, sample: str) -> None:
        pages = self._pages(sample)
        assert len(pages) >= 3, "a sample with no interior pages proves nothing"
        for index, (chars, images) in enumerate(pages[1:-1], start=2):
            assert chars > 100 or images > 0, (
                f"{sample} page {index} is effectively blank ({chars} chars, {images} images)"
            )
