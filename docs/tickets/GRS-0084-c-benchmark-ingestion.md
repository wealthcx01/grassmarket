# GRS-0084 — C benchmark ingestion (7 scored reviews)

**Status:** Shipped
**Loop:** Loop 7 — C-index (Customer Proposition)
**Depends on:** GRS-0080/0082, ADR-0023, ADR-0009, ATLAS-Methodology-v1.3
**Branch:** `grs-0084-c-benchmark-ingestion`

## What shipped

The C benchmark **ingestion machinery** — a NAMED public-app peer set, approval-gated — so a subject's
C index ships with peer context. Two honest boundaries held:

- **No client data committed.** The seven scored reviews are the founder's IP (read reference-only,
  never committed). This ticket ships the *machinery*; the operator feeds each review's C ratings in
  and the real scores never live in the repo. Tests use synthetic ratings.
- **AI proposes, humans approve (ADR-0009 / CLAUDE.md #8).** Ingestion only *proposes* a row; a
  consultant records the approval that makes it live.

Files:
- **`CBenchmarkRow`** (`predictions.py`) — a named peer's C score: `peer_name` (public app),
  `profile_key`, `c_index`, per-C-module `module_scores`, versions, `source_ref` (a non-committed
  provenance pointer), and `approved`/`approved_by`/`approved_at`. Contract invariant: `approved` ⟺
  both approval stamps present (ADR-0009).
- **`CBenchmarkRowORM`** + migration `0022_c_benchmark_rows` (JSON `module_scores`, FK approver,
  profile index).
- **Repository** — `propose_c_benchmark_row` (creates UNAPPROVED), `approve_c_benchmark_row`
  (records the sign-off; keeps the original approver on re-approve), `list_c_benchmark_rows`
  (`approved_only` default True; optional `profile_key` filter; a shared org-wide reference, not
  owner-scoped — peers are public).
- **`atlas/c_benchmark.py`** — `c_benchmark_proposal` scores a peer's C ratings via `score_customer`
  (fail-loud: unknown/missing C key aborts, never a silent drop); `c_peer_comparison` positions a
  subject (percentile = share of peers beaten; None on an empty set); `C_BENCHMARK_PEER_ROSTER` (the
  7 public peers). The 9 unscored apps are documented as the next content batch, not built here.

## Acceptance / verification

`tests/test_c_benchmark.py` — ingestion scores a peer + validates keys fail-loud; incomplete C
coverage refuses; the roster lists 7; a proposed row is not live until approved and the approval is
recorded; approving a missing row fails loud; the contract refuses an unstamped `approved=True`; the
peer set is a shared org-wide reference; peer comparison positions a subject. Golden master unchanged;
schema parity green; pyright + ruff clean.

## Original plan

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
