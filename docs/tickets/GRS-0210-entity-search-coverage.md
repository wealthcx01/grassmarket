# GRS-0210 — Smart search has to know the firms an advisor will actually type

**Status:** OPEN (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-26, staging review item 8). **Priority:** HIGH._
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
