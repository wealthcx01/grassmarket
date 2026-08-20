"""The Guide must not contradict the product (GRS-0244 scope 4).

A contradiction tripwire, **not** a prose freeze. The Guide is copy and will be reworded; what these
tests hold is that it cannot go back to describing governance the product no longer has, and cannot
lose the walkthrough for its newest client-facing surface.

Why a test at all, for a page of copy: the Guide told a new advisor that finalising needed a second
independent rater and Rating Committee sign-off — machinery ADR-0041 made dormant — and then, two
sections later, correctly described the founder gate. A page that contradicts itself about who
approves your work makes every other claim on it suspect, and nothing in CI noticed for weeks.

**These were verified to fail against the Guide as it stood before GRS-0244** (the GRS-0221 lesson:
a guard nobody has watched bite is not yet a guard).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_GUIDE = ROOT / "frontend" / "app" / "guide" / "page.tsx"


@pytest.fixture(scope="module")
def guide() -> str:
    assert _GUIDE.exists(), "the Guide page must exist"
    return _GUIDE.read_text(encoding="utf-8")


def _prose(text: str) -> str:
    """The Guide's copy with `//` comment lines removed.

    The comments explain *why* the copy says what it says, and they legitimately name the retired
    governance. Only what an advisor can read is under test.
    """
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith("//"))


class TestOneGovernanceStory:
    def test_peer_governance_is_only_ever_mentioned_as_dormant(self, guide: str) -> None:
        """It may be named — readers find references elsewhere — but never as a live gate."""
        for match in re.finditer(r"[^.]*Rating Committee[^.]*\.", _prose(guide)):
            sentence = match.group(0).lower()
            assert "dormant" in sentence, (
                f"the Guide describes the Rating Committee without saying it is dormant: "
                f"{match.group(0)!r}"
            )

    def test_it_does_not_claim_finalising_needs_a_second_rater(self, guide: str) -> None:
        """The specific false instruction. An advisor following it would wait for a gate that
        does not exist and conclude the product is broken."""
        prose = _prose(guide)
        for phrase in ("needs a second independent rater", "requires a second independent rater"):
            assert phrase not in prose, f"the Guide still claims finalising {phrase}"

    def test_the_founder_gate_is_described(self, guide: str) -> None:
        """Removing the wrong story is only half the job; the right one has to be present."""
        assert re.search(r"signed off|sign-off|Send to John", _prose(guide), re.IGNORECASE)


class TestTheClientReportIsWalkedThrough:
    def test_the_section_exists(self, guide: str) -> None:
        assert 'id: "client-report"' in guide, (
            "the Guide has no client-report walkthrough — the flagship surface a new advisor most "
            "needs walking through (GRS-0219/0220/0211)"
        )

    @pytest.mark.parametrize(
        "landmark",
        [
            "six sections",  # what the advisor writes
            "share link",  # how a client reads it without a login
            "PDF",  # the other rendition
        ],
    )
    def test_it_covers_the_route_end_to_end(self, landmark: str, guide: str) -> None:
        assert landmark.lower() in _prose(guide).lower(), (
            f"the client-report walkthrough never mentions {landmark!r}"
        )

    def test_it_discloses_read_tracking_to_the_advisor(self, guide: str) -> None:
        """An advisor should learn what the client is told from the Guide, not by surprise."""
        prose = _prose(guide).lower()
        assert "opened" in prose and ("soft evidence" in prose or "tells the reader" in prose)


class TestTheCountsMatchTheProduct:
    """Scope 3. Both numerals were checked against the shipped UI and both were already right —
    so these pin them rather than fix them, which is the useful outcome either way."""

    def test_the_pipeline_stage_count_matches_the_enum(self, guide: str) -> None:
        from bcap_contracts.entities import PipelineStage

        stated = re.search(r"board holds (\w+) stages", _prose(guide))
        assert stated is not None, "the Guide no longer states a stage count"
        words = {"seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11}
        assert words.get(stated.group(1)) == len(list(PipelineStage)), (
            f"the Guide says {stated.group(1)} stages; PipelineStage has {len(list(PipelineStage))}"
        )

    def test_the_wizard_step_count_matches_the_stepper(self, guide: str) -> None:
        """Counted from `WIZARD_STEPS` in the shipped component, not from a second copy."""
        steps_file = (ROOT / "frontend" / "components" / "steps.tsx").read_text("utf-8")
        block = re.search(r"export const WIZARD_STEPS.*?^\];", steps_file, re.MULTILINE | re.DOTALL)
        assert block is not None
        # `{ title: "` — the quote matters. Without it this also counts the declaration's own
        # TYPE annotation (`{ title: string; component: ... }[]`), which made the first version
        # of this test report 8 steps and accuse a correct Guide of being wrong.
        actual = len(re.findall(r'\{ title: "', block.group(0)))
        stated = re.search(r"The (\w+)-step wizard", _prose(guide))
        assert stated is not None, "the Guide no longer states a wizard step count"
        words = {"five": 5, "six": 6, "seven": 7, "eight": 8}
        assert words.get(stated.group(1)) == actual, (
            f"the Guide says a {stated.group(1)}-step wizard; WIZARD_STEPS has {actual}"
        )
