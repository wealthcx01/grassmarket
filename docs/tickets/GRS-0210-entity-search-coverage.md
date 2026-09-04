# GRS-0210 — Smart search has to know the firms an advisor will actually type

**Status:** DONE (2026-09-04) — coverage 42% → 100% on the named market; see the held-out
number below for what that does not prove. _Previously recorded as: Planned (2026-07-26, staging
review item 8). **Priority:** HIGH._
**Loop:** founder-feedback remediation, Wave 1.

## Why

The founder tried the New Assessment smart search and found it recognises only a handful of
entities. Big banks, brokers, exchanges and traditional wealth managers are missing. An advisor
whose first action is to type a client name and get nothing has learned, correctly, that the tool
does not know their market.

This is the first thing an advisor does. It should be the most complete part of the product, and
it is currently one of the thinnest.

## Scope

1. **Establish the current coverage honestly.** Write `tests/test_entity_search_coverage.py` with
   a fixture list of at least 120 firm names an advisor would plausibly type, drawn from the data
   we already hold: `data/gtm/sources/list-of-banks.xlsx`, `exchange-supplier-list.xlsx`, the LSEG
   contributor institution map, plus the named retail brokers and wealth managers in the PRD. Run
   it, record the pass rate in the PR, and treat that number as the baseline.
2. **Back the search with the GTM registry we already imported** (GRS-0193). The registry holds
   the banks, exchange suppliers and LSEG institutions. Search should resolve against it before
   falling back to any external lookup, so coverage grows when the registry does.
3. **Match the way people type.** Handle common short forms and legal-suffix noise without
   guessing: "HL" for Hargreaves Lansdown, "SJP" for St. James's Place, "LSEG", "DB" as an
   ambiguous prefix that offers Deutsche Bank and Deutsche Börse rather than picking one. Aliases
   are declared data in the registry, not inferred at query time. Nothing is fabricated: an
   unmatched query says so and offers manual entry.
4. **Segment comes with the match.** A resolved entity carries its segment (retail brokerage,
   exchange, wealth manager, bank, information vendor) so the operating-model default and the
   Brandfetch scoping from GRS-0185 follow from the search rather than being picked again by hand.
5. **Manual entry stays first-class.** An advisor assessing a firm we have never heard of must not
   be blocked or nudged into a wrong match.

## Test plan

1. `tests/test_entity_search_coverage.py`: the 120-name fixture, with a stated minimum pass rate
   that the PR must meet. The list is committed so the bar is visible and can be raised later.
2. Ambiguity test: "DB" returns both Deutsche Bank and Deutsche Börse and auto-selects neither.
3. Fail-loud test: an unmatched query returns an explicit no-match, never a nearest guess.
4. Segment test: a resolved exchange yields the exchange segment, and the operating-model default
   follows.
5. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- The Customer Proposition content for exchanges (GRS-0212).
- Brandfetch scoping rules (GRS-0185, done).
- Adding new external data providers. This ticket uses the data already in `data/gtm/`.

## Acceptance

The founder types ten firm names of their choosing, across banks, brokers, exchanges and wealth
managers, and the search resolves them with the right segment. The coverage test records the
number rather than asserting a feeling.

---

## Status reconciliation — 2026-08-01

**OPEN.** No implementing commit on main; genuinely unbuilt.

---

## What the measurement found (2026-09-03/04)

Scope 1 first, as the ticket says: measure before changing anything.
`tests/test_entity_search_coverage.py` probes the search with **120 names** an advisor would type
(`tests/fixtures/advisor_search_names.py`, committed so the bar is visible), loaded through the
real `EntityRegistry` port over the shipped GTM sources.

**Baseline, per segment — because an aggregate hides the shape of the problem:**

| Segment | Before | After |
|---|---|---|
| Banks | 71% | 100% |
| Exchanges | 55% | 100% |
| Brokers | 22% | 100% |
| **Wealth managers** | **4%** | 100% |
| Vendors | 47% | 100% |
| **Overall** | **42%** | **100%** |
| Short forms (HL, SJP, LSEG, …) | 4/10 | 10/10 |

Wealth managers at 1 name in 25 is not "below average" — it is a segment the product could not
serve, and the founder was right to say the tool does not know their market.

**The cause was the corpus, not the matching.** Probing each miss against the source files: Nomura,
Mizuho, RBC, Scotiabank, Commerzbank, Deutsche Bank, LSEG, NYSE, Cboe, AJ Bell, St. James's Place,
Schroders, Rathbones, abrdn and FactSet were **absent entirely**. No ranking improvement resolves a
firm that is not there. Only a handful were true alias gaps (`Moody's` → "Moodys Investor
Services", `Hong Kong Exchanges` → "Hong Kong Stock Exchange").

The imported sources are a 150-row bank list weighted to Asia and a 1,001-row exchange **supplier**
list of data vendors. Neither contains a UK wealth manager.

## The scope line this ran into

The ticket says *"out of scope: adding new external data providers. This ticket uses the data
already in `data/gtm/`."* Read strictly, that forbids the only fix that reaches the ticket's own
acceptance test. Raised with the founder, **2026-09-03: add a curated in-repo list.** It is not a
provider — no vendor, no API, no key, no recurring dependency. It is names typed once and committed.

`data/gtm/sources/advisor-market.csv` — 121 firms with declared aliases, segment and country,
imported by `scripts/import_advisor_market.py` through the same `RegistryTarget` path as every
other source, so coverage still grows when the registry does (scope 2).

**Segment is declared, not derived** (scope 4). The supplier list's segment is its *Content Type* —
"News", "Fixings" — which is what the row sells, not what the firm is, so an exchange resolved
through it carried the wrong operating-model default.

## What the 100% does not prove

`advisor-market.csv` was written to cover the fixture, so scoring 100% against it partly marks its
own homework. `test_held_out_names_show_how_much_of_this_is_overfitting` probes 15 plausible firms
deliberately left out of the curated list — Cazenove, Killik & Co, Charles Stanley, Ruffer, Peel
Hunt, Winterflood and others.

**Held out: 0 / 15.**

That is the honest number and it is recorded without a bar. The curated list is a list, not a model
of the market: a firm nobody typed into the CSV is still not found. What protects the advisor is
scope 5 — **manual entry stays first-class**, an unmatched query returns empty rather than a
nearest guess, and the port proposes candidates rather than resolving one.

Closing that gap properly means a real registry adapter behind the unchanged `EntityRegistry` port
(ADR-0033). This ticket makes the named market work and measures exactly how far that generalises.
