"""GRS-0180 — the 7 Powers adaptation document must stand complete.

A structural guard (not a content review): the normative adaptation document exists, carries the
rights front matter and the attribution line, and has a section for each of the seven powers. This
prevents partial authoring or an accidental deletion; the substantive review is Hamilton Helmer's
(ADR-0046).
"""

from __future__ import annotations

from pathlib import Path

import pytest

_DOC = Path(__file__).resolve().parents[1] / "docs" / "ATLAS-7Powers-Adaptation.md"

_SEVEN_POWERS = (
    "Scale Economies",
    "Network Economies",
    "Counter-Positioning",
    "Switching Costs",
    "Branding",
    "Cornered Resource",
    "Process Power",
)


@pytest.fixture(scope="module")
def text() -> str:
    assert _DOC.exists(), "the adaptation document must exist"
    return _DOC.read_text(encoding="utf-8")


def test_carries_the_rights_front_matter(text: str) -> None:
    # The grant registration (ADR-0046): grantor, grantee, date, scope, and the review condition.
    assert "grantor: Hamilton Helmer" in text
    assert "grantee: John Gallagher" in text
    assert "2026-07-23" in text
    assert "wealth platforms" in text
    assert "adr: ADR-0046" in text


def test_carries_the_attribution_line(text: str) -> None:
    # The attribution line may wrap across lines in prose; collapse whitespace before matching.
    collapsed = " ".join(text.split())
    assert (
        "Adapted from Hamilton Helmer, 7 Powers: The Foundations of Business Strategy, "
        "with the author's permission." in collapsed
    )


def test_has_a_section_for_each_of_the_seven_powers(text: str) -> None:
    for i, power in enumerate(_SEVEN_POWERS, start=1):
        heading = f"### 2.{i} {power}"
        assert heading in text, f"missing section: {power}"


def test_distinguishes_embedded_maths_from_adaptation(text: str) -> None:
    # The document's core discipline (ADR-0046): faithful where it embeds, explicit where it adapts.
    assert "embedded" in text.lower()
    assert "adaptation" in text.lower() or "ATLAS reading" in text


def test_states_scoring_is_unchanged(text: str) -> None:
    # ADR-0046 §4: this document does not move P scoring; the golden master stays byte-identical.
    assert "min(Benefit, Barrier)" in text
    assert "byte-identical" in text


def test_covers_all_three_segments(text: str) -> None:
    for marker in ("RB", "WA", "EX"):
        assert marker in text
