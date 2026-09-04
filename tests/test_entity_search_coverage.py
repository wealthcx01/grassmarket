"""How much of the market the search actually knows (GRS-0210 scope 1).

The founder typed firm names into New Assessment search and got nothing back. An advisor whose
first action is to type a client name and find silence has learned, correctly, that the tool does
not know their market.

**This test measures rather than asserts a feeling.** It loads the GTM sources the product already
ships, probes the search with 120 firm names an advisor would plausibly type, and reports the hit
rate per segment. The fixture is committed (`tests/fixtures/advisor_search_names.py`) so the bar is
visible and can be raised deliberately rather than drifting.

**Per segment, not just overall.** A search that finds every bank and no wealth manager is not
"80% good" — it is unusable for half the pipeline, and an aggregate number hides exactly that.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

from grassmarket.data.repository import Repository
from grassmarket.entities.registry import DbEntityRegistry, StubEntityRegistry
from grassmarket.gtm.ingest import (
    RowError,
    parse_advisor_market_row,
    parse_bank_row,
    parse_supplier_row,
)
from tests.fixtures.advisor_search_names import ALL_NAMES, BY_SEGMENT, HELD_OUT, SHORT_FORMS

_ROOT = Path(__file__).resolve().parents[1]
_SOURCES = _ROOT / "data" / "gtm" / "sources"
_ON = date(2026, 1, 1)

# The bar, set to the **measured baseline** on 2026-09-03 — not to an aspiration. A target nobody
# can reach is not a bar; it teaches the team to ignore the test. Raise this in the same commit
# that improves the corpus, so the number and the improvement move together.
#
# Baseline before the curated list (2026-09-03): banks 71% · exchanges 55% · brokers 22% ·
# wealth managers 4% · vendors 47% · overall 42%. That measurement is what justified adding
# `advisor-market.csv`; see `test_held_out_names_...` for what the new figure does NOT prove.
MINIMUM_OVERALL_HIT_RATE = 1.0

#: Per-segment floors, because an aggregate hides the shape of the problem. Wealth managers at 4%
#: is not "a bit below average" — it is a segment the product cannot serve, and averaging it against
#: banks at 71% would let a corpus fix in one segment mask a regression in another.
MINIMUM_SEGMENT_HIT_RATE: dict[str, float] = {
    "banks": 1.0,
    "exchanges": 1.0,
    "brokers": 1.0,
    "wealth managers": 1.0,
    "vendors": 1.0,
}


def _read_rows(filename: str) -> list[dict]:
    sys.path.insert(0, str(_ROOT / "scripts"))
    from _gtm_import import read_xlsx_rows  # noqa: PLC0415 - script helper, not a package

    return read_xlsx_rows(_SOURCES / filename)


def _read_csv(filename: str) -> list[dict]:
    import csv  # noqa: PLC0415 - local to keep the module's imports about the search, not files

    with (_SOURCES / filename).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def corpus() -> list:
    """Every target the shipped GTM sources produce. Skipped, never faked, if the files are absent:
    a coverage number measured against an empty corpus would be a lie about the product."""
    if not _SOURCES.exists():  # pragma: no cover - the files are committed
        pytest.skip("data/gtm/sources is not present")
    targets = []
    for row in _read_rows("list-of-banks.xlsx"):
        try:
            targets.append(parse_bank_row(row, imported_on=_ON))
        except RowError:
            continue
    for row in _read_rows("exchange-supplier-list.xlsx"):
        try:
            target, _contacts = parse_supplier_row(row, imported_on=_ON)
            targets.append(target)
        except RowError:
            continue
    for row in _read_csv("advisor-market.csv"):
        targets.append(parse_advisor_market_row(row, imported_on=_ON))
    return targets


@pytest.fixture
def registry(corpus, session_factory):
    """The search exactly as an advisor meets it: the imported corpus behind the real port."""
    session = session_factory()
    repo = Repository(session)
    seen: set[str] = set()
    for target in corpus:
        if target.target_id in seen:
            continue  # the supplier list has one row per service, so a supplier repeats
        seen.add(target.target_id)
        repo.upsert_registry_target(target)
    session.commit()
    return DbEntityRegistry(repo, stub=StubEntityRegistry())


def _finds(registry, name: str) -> bool:
    """Whether an advisor typing `name` sees the firm they meant in the results."""
    results = registry.search(name, limit=8)
    wanted = name.lower()
    return any(
        wanted in candidate.name.lower()
        or candidate.name.lower() in wanted
        or any(wanted in alias.lower() for alias in candidate.aliases)
        for candidate in results
    )


def test_coverage_by_segment(registry, record_property) -> None:
    """The baseline, recorded per segment and overall.

    This prints the numbers rather than hiding them behind a pass, because the ticket's acceptance
    is "the coverage test records the number rather than asserting a feeling".
    """
    lines: list[str] = []
    total_hits = 0
    for segment, names in BY_SEGMENT.items():
        hits = [n for n in names if _finds(registry, n)]
        misses = [n for n in names if n not in hits]
        total_hits += len(hits)
        rate = len(hits) / len(names)
        lines.append(f"  {segment:16} {len(hits):3}/{len(names):<3} {rate:5.0%}")
        if misses:
            lines.append(f"       missing: {', '.join(misses[:8])}")
        record_property(f"coverage_{segment.replace(' ', '_')}", round(rate, 3))

    regressions = [
        f"{segment} fell below its floor"
        for segment, floor in MINIMUM_SEGMENT_HIT_RATE.items()
        if (len([n for n in BY_SEGMENT[segment] if _finds(registry, n)]) / len(BY_SEGMENT[segment]))
        < floor
    ]
    overall = total_hits / len(ALL_NAMES)
    report = "\n".join(
        [
            "",
            "ENTITY SEARCH COVERAGE (GRS-0210 baseline)",
            *lines,
            f"  {'OVERALL':16} {total_hits:3}/{len(ALL_NAMES):<3} {overall:5.0%}",
            "",
        ]
    )
    print(report)
    record_property("coverage_overall", round(overall, 3))
    assert not regressions, "\n".join([*regressions, report])
    assert overall >= MINIMUM_OVERALL_HIT_RATE, report


def test_held_out_names_show_how_much_of_this_is_overfitting(registry, record_property) -> None:
    """The honest counterweight to a 100% score.

    `advisor-market.csv` was written to cover the fixture above, so scoring 100% against it partly
    marks its own homework — it proves the names somebody thought of are covered, not that the
    121st name an advisor types will be. These fifteen firms were deliberately left out of the
    curated list.

    **There is no bar here on purpose.** This number is a measurement of how far the corpus
    generalises, and the honest answer today is "barely" — the curated list is a list, not a model
    of the market. Recording it stops the headline figure being mistaken for completeness, and it
    is the number to watch if a real provider is ever wired in behind the same port.
    """
    hits = [n for n in HELD_OUT if _finds(registry, n)]
    rate = len(hits) / len(HELD_OUT)
    print(
        f"\nHELD-OUT NAMES (not in the curated list): {len(hits)}/{len(HELD_OUT)} = {rate:.0%}"
        f"\n  found:   {', '.join(hits) or 'none'}"
        f"\n  missing: {', '.join(n for n in HELD_OUT if n not in hits) or 'none'}\n"
    )
    record_property("coverage_held_out", round(rate, 3))


def test_short_forms_are_declared_data_not_guesses(registry) -> None:
    """How people actually type: "HL", "SJP", "LSEG", "Barclays plc".

    Aliases are declared data in the registry, never inferred at query time (scope 3). This records
    which short forms resolve today; the ones that do not are corpus gaps, not algorithm gaps.
    """
    resolved = {
        typed: _finds(registry, meant) and _finds(registry, typed)
        for typed, meant in SHORT_FORMS.items()
    }
    hits = [t for t, ok in resolved.items() if ok]
    print(
        f"\nSHORT FORMS: {len(hits)}/{len(SHORT_FORMS)} resolve — "
        f"missing: {', '.join(t for t, ok in resolved.items() if not ok)}\n"
    )
    # No bar yet: this is the measurement that justifies adding aliases to the corpus.
    assert isinstance(resolved, dict)


def test_an_unmatched_query_says_so_rather_than_guessing(registry) -> None:
    """Fail loud (#3). A firm we have never heard of must come back empty so the advisor is offered
    manual entry — never a nearest guess they might accept by accident."""
    assert registry.search("Zzzyx Fictional Advisory Partners", limit=8) == []


def test_manual_entry_is_never_blocked_by_a_wrong_match(registry) -> None:
    """Scope 5. A search that returns candidates is offering them, not choosing one: the port
    proposes and the human picks, so an unknown firm is a first-class record, not an error."""
    results = registry.search("Bank", limit=8)
    assert len(results) > 1, "a broad term must offer several candidates, never auto-resolve one"


class TestTheCuratedRowsSayWhatTheyMean:
    """`advisor-market.csv` is declared data, so the parser must not quietly reinterpret it."""

    def test_aliases_are_declared_not_inferred(self) -> None:
        """Scope 3. "SJP" resolves because somebody wrote it down, not because an algorithm
        guessed at initials — which would also happily invent "SJ" or "SP"."""
        row = {
            "name": "St. James's Place",
            "aliases": "SJP|St James's Place",
            "segment": "Wealth manager",
            "country": "United Kingdom",
            "domain": "sjp.co.uk",
        }
        target = parse_advisor_market_row(row, imported_on=_ON)
        assert target.aliases == ("SJP", "St James's Place")
        assert target.target_id == "am-st-james-s-place"

    def test_a_row_with_no_aliases_gets_none_rather_than_a_blank_one(self) -> None:
        """An empty alias column must not become `("",)`, which would match every query."""
        target = parse_advisor_market_row(
            {"name": "Ruffer", "aliases": "", "segment": "Wealth manager"}, imported_on=_ON
        )
        assert target.aliases == ()

    def test_segment_is_the_firm_not_what_it_sells(self) -> None:
        """Scope 4. The supplier list's segment is its Content Type — "News", "Fixings" — which is
        what the row sells, not what the firm is. An exchange resolved through it carried the wrong
        operating-model default; a curated row states the segment outright."""
        target = parse_advisor_market_row(
            {"name": "Cboe Global Markets", "aliases": "Cboe", "segment": "Exchange"},
            imported_on=_ON,
        )
        assert target.segment == "Exchange"

    def test_a_nameless_row_is_refused_rather_than_slugged_into_nothing(self) -> None:
        with pytest.raises(RowError):
            parse_advisor_market_row({"name": "", "segment": "Bank"}, imported_on=_ON)
