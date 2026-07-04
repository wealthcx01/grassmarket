# GRS-0003 — Golden-master fixture

- **Loop:** 1 (see PRD §9)
- **Branch:** `grs-0003-golden-master` (stacked on `grs-0002-registry-content`)
- **Status:** ⏸ **PAUSED FOR JOHN'S RATIFICATION** — GRS-0004 (the engine) does not start until the
  fixture is approved.
- **Normative sources:** `docs/ATLAS-Methodology-v1.md` §3, §5; ADR-0001, ADR-0002.

## Goal

One complete assessment computed **end-to-end** per Methodology §5 for a composite mid-tier
retail brokerage (**"Meridian Securities"**), as the golden-master oracle the engine (GRS-0004)
must reproduce **exactly**. Delivered two ways: a live-formula workbook for you to audit/adjust,
and the JSON the engine tests against.

## Deliverables

- **`fixtures/golden-master.xlsx`** — live formulas. Editing a subcomponent Level (or setting a
  State) recomputes q_m → L, and the metric/power inputs recompute B/P → **V**. Sheets: Overview,
  Subcomponents, Modules, Business, Powers, Composite.
- **`tests/fixtures/golden_master.json`** — inputs + every intermediate + finals (authoritative).
- **`scripts/build_golden_master.py`** — the reference generator (Methodology §5).
- **`scripts/regen_golden_master_json.py`** — after you edit the workbook in Excel and save, this
  reads your inputs back and regenerates the JSON via the same compute path (one oracle, no drift).
- **`tests/test_golden_master_fixture.py`** — 10 tests asserting the fixture is internally
  consistent (q_m = blend+min; N/A & Not-Assessed excluded; L, B, P, V recompose; no Frontier over
  a Basic part; display = V×100).

## Computed headline (Meridian Securities)

| | B | P | L | **V** |
|---|---|---|---|---|
| index [0,1] | 0.679 | 0.271 | 0.484 | **0.479** |
| display 0–100 | | | | **47.86** |

Module ratings (two-track — continuous q_m for priority, rule-based gate for the word):

| Module | q_m | Gate | Bottleneck |
|---|---|---|---|
| FRONTEND | 0.445 | Developing | ACCESSIBILITY_LOCALISATION (Basic) |
| APP_SERVER | 0.620 | Advanced | RESILIENCE_DR (Developing) |
| MARKET_DATA | 0.480 | Developing | VENDOR_REDUNDANCY (Basic) |
| ORCHESTRATION | 0.368 | Developing | EVENT_DRIVEN (Basic) |
| CMS | 0.480 | Developing | CONTENT_SEARCH_PERSONALISATION (Basic) |
| BACKOFFICE | 0.640 | Advanced | PORTFOLIO_MGMT (Developing) |
| OEMS | 0.410 | Developing | EXEC_ALGOS (Basic) |
| EMS_GATEWAY | 0.552 | Advanced | EMS_CONNECTIVITY (Developing) |
| LIQ_CONNECT | 0.640 | Advanced | FOREIGN_BROKERS (Developing) |

Non-score states exercised: `OEMS_APIS_COLOCATION` = Not Applicable (dropped from its denominator);
`VALUE_ADD_SERVICES` and `FUND_HOUSES` = Not Assessed (never scored, coverage < 1.0, excluded from
q_m). No module is Frontier — each has a Developing/Basic bottleneck, so the headline stays honest.

## ⚠️ Judgement calls to ratify (these are yours)

1. **Subcomponent levels + evidence grades** — the 51 ratings for Meridian. Realistic composite;
   adjust any in the workbook. *(These are the "scores" the loop prompt means.)*
2. **Draft coefficients** (all uniform pending the elicitation panel): α_module = 0.7, α_L = 0.7,
   θ = (B 0.30, P 0.30, L 0.40), critical-modules-for-L = {APP_SERVER, BACKOFFICE, OEMS}, and
   λ/δ/w uniform. These are placeholders; the panel replaces them in GRS-0004.
3. **Power-strength encoding** (feeds the continuous P index only): None = 0, Emerging = 0.4,
   Established = 0.7, Wide = 1.0. Methodology §5.4 uses `strength_j` numerically but doesn't fix
   the encoding — **this likely needs an ADR.** The triad ratings themselves stay ordinal.
4. **The rating-gate rule** (§5.2 is not fully algorithmic). Draft interpretation:
   `band = min(critical-rule ceiling, overall-bottleneck floor)` — so a module is never rated
   above its weakest assessed part, and Frontier additionally needs all critical subcomponents
   Advanced+ at E3+. Confirm this reading or adjust.

## To ratify

Open the workbook, adjust anything, save, then run
`uv run python scripts/regen_golden_master_json.py`. Re-run `uv run pytest -q` (the consistency
tests must stay green). When you're happy, approve and GRS-0004 (the engine) begins — its
golden-master test will pin these exact numbers.
