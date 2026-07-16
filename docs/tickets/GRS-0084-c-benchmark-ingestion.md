# GRS-0084 — C benchmark ingestion (7 scored reviews)

**Status:** Planned
**Loop:** Loop 7 — C-index (Customer Proposition)
**Depends on:** ADR-0023 (Accepted), ATLAS-Methodology-v1.3

## Why

A customer-proposition index is far more useful launched *with* peer context than as an isolated
score. Seven brokerage reviews have already been scored against the C rubric; ingesting them as
benchmark rows means C ships with peer-relative benchmarking already populated — a consultant sees
where a subject sits versus Saxo / IBKR / Revolut on day one. AI-derived scores must not enter the
benchmark set unapproved, so ingestion is approval-gated per ADR-0009.

## What to build

Files:
- `src/grassmarket/atlas/` benchmark ingestion path — a loader that converts each scored review
  into a benchmark row keyed to the C registry (modules, subcomponents, widgets + rarity).
- Approval gate — ingestion routes through the ADR-0009 approval policy; no benchmark row becomes
  live without a recorded consultant/committee approval (AI proposes, humans approve).
- Benchmark store / repository entries for the C peer set (through the repository layer — no
  scattered queries).

Refs / source (read-only authoring input):
- The 7 completed, scored reviews under
  `…/Business/Briefing/Content-Bank/Projects/Brokerage-App-Reviews/*/`:
  Saxo, IBKR, Lightyear, Revolut, Trading212, WeBull, Hargreaves Lansdown.

Reuse:
- The existing benchmark/peer machinery and the ADR-0009 approval-gate pattern already used for
  other AI-derived artifacts.
- The C registry keys from GRS-0080 (rows validate against them; unknown key fails loud).

New:
- The 7 C benchmark rows and the review→row ingestion mapping.

Next content batch (documented here, NOT built in this ticket): the 9 currently-unscored apps —
Capital, Charles Schwab, EFG Hermes, EasyEquities, Futu, Hapi, Robinhood, Trii, eToro.

## Acceptance / verification

- All 7 reviews ingest into benchmark rows that validate against the C registry; an unknown module /
  subcomponent / widget key fails loud (no silent drop).
- No row goes live without a recorded approval (ADR-0009 gate test).
- Rows are readable only through the repository layer; data scoping honoured.
- C benchmarking surfaces peer positions for a subject assessment (smoke test with one subject vs.
  the 7 peers).
- Golden master unchanged.

## Not in scope

- Scoring the 9 unscored apps (next content batch).
- The wizard step — GRS-0083; deliverable rendering of benchmarks — GRS-0085.
- Any V composition change — GRS-0086.
