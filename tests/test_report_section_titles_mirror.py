"""The frontend's section-title registry must not drift from the contract (GRS-0235).

`SECTION_TITLES` is authoritative in `bcap_contracts.client_report` — schemas win on conflict
(CLAUDE.md non-negotiable #4). The browser cannot import Python, so `frontend/lib/reportSections.ts`
mirrors it by hand, and a hand-mirror with nothing checking it is a silent-fallback waiting to
happen: the PDF would say "What that is worth" while the web page said something else, and both
would look right in isolation.

The check lives here rather than in vitest deliberately. A TypeScript test can only compare the
mirror against another TypeScript copy of the same values — a copy against a copy, which goes on
passing after both drift from the contract. Only the Python side knows what the titles actually are.

This is the same failure GRS-0231 shipped to staging: a test asserting the right property against an
invented fixture passed while the page was wrong.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from bcap_contracts.client_report import SECTION_TITLES
from bcap_contracts.report_links import ReportSectionKind

ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / "frontend" / "lib" / "reportSections.ts"

#: `  business: "The business",` — the key, then the title, inside the exported record.
_ENTRY = re.compile(r'^\s*(\w+):\s*"([^"]+)",\s*$', re.MULTILINE)


def _mirror_titles() -> dict[str, str]:
    """The titles as the TypeScript file declares them, parsed from the source.

    Parsed rather than executed: running a bundler from pytest would make this test depend on the
    node toolchain being present, and the file is a flat literal by design so that it does not have
    to be.
    """
    source = MIRROR.read_text(encoding="utf-8")
    block = re.search(
        r"export const SECTION_TITLES: Record<string, string> = \{(.*?)\};", source, re.DOTALL
    )
    assert block is not None, f"SECTION_TITLES literal not found in {MIRROR}"
    return {key: title for key, title in _ENTRY.findall(block.group(1))}


def _mirror_order() -> list[str]:
    source = MIRROR.read_text(encoding="utf-8")
    block = re.search(r"export const SECTION_ORDER = \[(.*?)\] as const;", source, re.DOTALL)
    assert block is not None, f"SECTION_ORDER literal not found in {MIRROR}"
    return re.findall(r'"(\w+)"', block.group(1))


def test_the_frontend_mirror_matches_the_contract_exactly() -> None:
    expected = {kind.value: title for kind, title in SECTION_TITLES.items()}
    assert _mirror_titles() == expected, (
        "frontend/lib/reportSections.ts has drifted from bcap_contracts.client_report."
        "SECTION_TITLES. The contract is authoritative — update the TypeScript mirror."
    )


def test_the_mirror_covers_every_section_kind() -> None:
    """A kind added to the enum without a title would render as a raw key in the browser."""
    assert set(_mirror_titles()) == {kind.value for kind in ReportSectionKind}


def test_the_mirrored_reading_order_matches_the_contract() -> None:
    """Order is meaning here: it is the order a client reads, and the order gaps are scanned in."""
    assert _mirror_order() == [kind.value for kind in SECTION_TITLES]


@pytest.mark.parametrize("path", ["components/SharedReport.tsx", "app/deliverables"])
def test_no_second_copy_of_the_titles_survives(path: str) -> None:
    """The point of the registry is that there is one of it.

    Before GRS-0235 the same six pairs were hand-copied into three files. Catching a reintroduced
    copy here is cheaper than discovering it when two surfaces disagree in front of a client.
    """
    target = ROOT / "frontend" / path
    files = [target] if target.is_file() else sorted(target.rglob("*.tsx"))
    offenders = [
        f.relative_to(ROOT)
        for f in files
        if re.search(r"SECTION_TITLES(: Record<string, string>)? = \{", f.read_text("utf-8"))
    ]
    assert not offenders, f"A second SECTION_TITLES literal reappeared in: {offenders}"
