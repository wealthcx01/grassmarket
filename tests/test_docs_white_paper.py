"""The engine white paper must stand complete and current (GRS-0237 scope 1).

A structural guard, not a content review: the document exists, covers every section a sceptical
technical reader needs, pins itself to the current methodology version, and does not describe
retired governance as though it were operative — which is exactly how its predecessor
(`ATLAS-Methodology-Guide.md`) went stale without anyone noticing.

The last two tests are the ones that matter most. A white paper whose limitations register
quietly drops the coefficient status would be worse than no white paper, because it would carry
Bruntsfield's name into a diligence conversation while overstating its evidence.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_PAPER = ROOT / "docs" / "ATLAS-White-Paper-v1.md"
_RETIRED_GUIDE = ROOT / "docs" / "ATLAS-Methodology-Guide.md"

_REQUIRED_SECTIONS = (
    "Epistemic stance",
    "Notation",
    "The model, formally",
    "Behavioural properties",
    "Uncertainty",
    "Coefficient provenance",
    "Reliability and validity programme",
    "The value bridge",
    "Validation evidence",
    "Limitations register",
    "Closure roadmap",
    "Document map",
    "Versioning",
)


@pytest.fixture(scope="module")
def text() -> str:
    assert _PAPER.exists(), "the white paper must exist"
    return _PAPER.read_text(encoding="utf-8")


def _section(text: str, number: int) -> str:
    """Everything under `## <number>.` up to the next top-level `## `.

    Anchored on a line start so that `### 10.1` does not terminate section 10 — a plain
    `split("## 10.")` matches inside `### 10.1` and silently returns the two-line preamble instead
    of the section, which is how the first version of this test passed against nothing.
    """
    match = re.search(
        rf"^## {number}\..*?(?=^## (?!{number}\.)|\Z)", text, re.MULTILINE | re.DOTALL
    )
    return match.group(0) if match else ""


@pytest.mark.parametrize("section", _REQUIRED_SECTIONS)
def test_every_required_section_is_present(section: str, text: str) -> None:
    assert re.search(rf"^#+ .*{re.escape(section)}", text, re.MULTILINE | re.IGNORECASE), (
        f"the white paper has no '{section}' section"
    )


def test_it_pins_itself_to_the_current_methodology(text: str) -> None:
    """A paper that names an old normative version is how the last one went stale."""
    assert "ATLAS-Methodology-v1.6.md" in text
    assert "v1.1" not in text.split("## 2. Notation")[0].replace(
        "identical to the same document scored under v1.1", ""
    ), "the header still points at an older normative version"


def test_it_does_not_present_retired_governance_as_current(text: str) -> None:
    """ADR-0041 made the Rating Committee dormant. The Guide never caught up; this must."""
    for match in re.finditer(r"[^.]*Rating Committee[^.]*\.", text):
        sentence = match.group(0).lower()
        assert any(word in sentence for word in ("dormant", "retired", "intended mode")), (
            f"the Rating Committee is described without saying it is dormant: {match.group(0)!r}"
        )


def test_the_limitations_register_names_the_coefficient_status(text: str) -> None:
    """The one limitation a reader must not be able to miss (GRS-0237 scope 1 + D1).

    No expert panel has met. If this paper ever stops saying so while that remains true, it is
    making a claim about evidence that does not exist — the D-class defect the whole codebase is
    built to prevent, printed on Bruntsfield letterhead.
    """
    limitations = _section(text, 10)
    assert limitations, "no limitations register found"
    assert re.search(r"no expert elicitation panel has met", limitations, re.IGNORECASE), (
        "the limitations register no longer states that no elicitation panel has met"
    )
    assert "provisional" in limitations.lower()
    assert "D1" in limitations, "the register must point at the founder decision that closes this"


def test_it_admits_what_it_does_not_establish(text: str) -> None:
    """A white paper that only lists strengths reads as marketing and gets treated as marketing."""
    assert re.search(r"does not establish", text, re.IGNORECASE)
    assert re.search(r"never been measured|no measurements|no resolved forecasts", text, re.I), (
        "the paper must say which machinery has produced no data"
    )


def test_every_validation_claim_names_where_to_check_it(text: str) -> None:
    """The evidence table is the checkable part; a row without a source is an assertion."""
    table = _section(text, 9)
    rows = [r for r in table.splitlines() if r.startswith("|") and "---" not in r][1:]
    assert len(rows) >= 6, "the validation evidence table has lost rows"
    for row in rows:
        assert re.search(r"`[^`]+`", row), f"validation row cites no source: {row!r}"


def test_the_retired_guide_redirects_rather_than_lingering(text: str) -> None:
    """Scope 2's decision, held in place at both ends."""
    guide = _RETIRED_GUIDE.read_text(encoding="utf-8")
    assert guide.lstrip().startswith("# RETIRED"), "the guide must announce its retirement first"
    assert "ATLAS-White-Paper-v1.md" in guide, "the retired guide must point at its replacement"
    # And the paper must own the retirement, so the two cannot disagree about which is current.
    assert "ATLAS-Methodology-Guide.md" in text
    assert re.search(r"RETIRED|retired", text)
