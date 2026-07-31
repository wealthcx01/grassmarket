# GRS-0183 — Remove ConnectTrade from the catalogue

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: In review (2026-07-24) — removed from catalogue, WeBull deal reassigned to OpenBB, tests/docs updated, PR open._
sell recommendation is a product with no agreement.
**Loop:** founder-feedback remediation, Wave 1. ADR-0026 amendment note (config change).

## Why

There is no agreement with ConnectTrade. Verified on staging: the Revolut demo's
"Recommended to sell" panel leads with ConnectTrade at 15% Yr-1. The founder: remove it
entirely.

## Scope (blast radius mapped)

ConnectTrade is a catalogue product with no signed agreement, so it must leave the catalogue and
every place the loaders derive from it. The two YAMLs are validated in lockstep by
`load_product_fit()` (`packages/bcap_contracts/src/bcap_contracts/product_fit.py`, lines 79-91: it
refuses if `product_fit.yaml` names a product not in `commissions.yaml`, AND refuses if a catalogue
product has no authored fit) — so the two stanzas must be removed in the SAME commit or the loader
fails loud. No production commission lines reference ConnectTrade (confirmed: it exists only in demo
seed data), so removal is non-retroactive with no data migration.

1. **Config — remove both stanzas (lockstep).**
   - `packages/bcap_contracts/src/bcap_contracts/registry_data/commissions.yaml`: delete the
     `connecttrade` product block (lines 13-17: `name: ConnectTrade`, `yr1_bps: 1500`, `yr2_bps:
     1000`, `window_months: 24`).
   - `packages/bcap_contracts/src/bcap_contracts/registry_data/product_fit.yaml`: delete the
     `connecttrade` fit block (lines 35-43: `profiles: [retail]`, `modules: [OEMS, EMS_GATEWAY]`,
     `c_modules: [CUST_TRADING_EXPERIENCE]`, `powers: []`, its pitch).
   Both in one change; the loader lockstep check is the proof they stay consistent.

2. **Demo seed — reassign WeBull's illustrative deal.** In
   `src/grassmarket/demo/brokerage_showcase.py` the WeBull spec (around line 234) carries
   `product_id="connecttrade", deal_value_minor=8_000_000` (the £80,000 Year-1 deal). Reassign to
   **`openbb`**. Decision: OpenBB, not Benzinga, because OpenBB's rate schedule is identical to the
   removed ConnectTrade one (`yr1_bps 1500 / yr2_bps 1000 / window_months 24`,
   `commissions.yaml:18-22`), so the illustrative £80k deal and every earnings figure derived from it
   keep the same magnitude — the demo's numbers do not move, only the product name changes.
   OpenBB is an agreed product and a legitimate fit for a trading-experience/execution gap, so the
   sell narrative still reads sensibly.

3. **Tests — drop or re-point every ConnectTrade assertion.**
   - `tests/test_sell_opportunities.py`: the test
     `test_hl_report_recommends_connecttrade_against_its_basic_gaps` (line 164) and its assertions at
     lines 166, 171, 180, 300, 333, plus the ordered-recommendation assertion at line 271
     (`== ["benzinga", "openbb", "connecttrade"]`). Re-point each to the reassigned/remaining agreed
     products (rename the test to its new lead product; update the expected ordered id lists to drop
     `connecttrade`). Where a case existed only to prove ConnectTrade was recommended, retarget it to
     OpenBB against the same gaps rather than deleting the coverage.
   - `tests/test_product_course.py`: line 83 (`("openbb", "brandfetch_distribution", "connecttrade")`),
     line 100 (`product_commission_carrot("connecttrade", ...)`), line 118
     (`{"openbb", "connecttrade"} <= ids`). Drop `connecttrade` from the tuples/sets; where a carrot
     was fetched for it, use an agreed product id.
   - `tests/test_earnings.py`: the `connecttrade` rate fixtures/expectations at lines 46-48, 106,
     112, the inline `ProductRate` at lines 124-125, `product_ref("connecttrade")` at line 174, and
     the hash fixture at line 210. Because the WeBull deal moves to OpenBB (identical rates), retarget
     these to `openbb`/`OpenBB` with the same numeric expectations, so the earnings maths is proven
     unchanged in magnitude.
   - `tests/test_course_certs.py`: lines 32 and 35 (`course_cert_subjects(["openbb", "connecttrade"])`,
     `"product:connecttrade" in keys`). Drop the `connecttrade` subject/key.
   - `frontend/components/SellOpportunitiesPanel.test.tsx`: the mock opportunity at lines 32-33 and
     40-41 (`product_id: "connecttrade"`, `name: "ConnectTrade"`) and the assertion at line 63
     (`findByText("ConnectTrade")`). Re-point the mock to an agreed product (e.g. OpenBB) so the panel
     test still proves a recommendation renders, without naming a product with no agreement.

4. **Docs.**
   - **ADR-0026 amendment note** (`docs/adr/ADR-0026-commission-schedule-v7-two-stream.md`, seed-
     products line ~20): add a dated amendment recording that ConnectTrade is removed from the
     catalogue (no signed agreement). State that non-retroactivity holds trivially — no production
     commission line ever referenced it, so no recorded line's content hash changes. Do not rewrite
     history; append the amendment.
   - `docs/ESTATE-RECONCILIATION.md`: remove the ConnectTrade Stream-A rate row (line 9) and drop
     ConnectTrade from the client/product list (line 22), noting "removed until an agreement exists".
   - `docs/adr/ADR-0028-bruntsfield-academy-workbench.md:26` ("(ConnectTrade pending)"): strike the
     pending reference — there is no ConnectTrade course and none is planned.
   - `reports/brokerage-e2e-staging-2026-07-21.md:25` is a dated point-in-time staging report; leave
     it as a historical record (it describes what staging showed on that date), but the PR notes the
     post-merge re-seed supersedes it.
   - No ConnectTrade course exists in `src/grassmarket/workbench/content/`, so the Academy needs no
     code change.

5. **Staging re-seed.** After merge, re-run `scripts/seed_demo.py` on staging so the sell panel and
   earnings stop showing ConnectTrade and show the reassigned OpenBB deal instead. Record the run in
   the PR description.

## Test plan

Backend pytest, frontend vitest per file; `pyright`, `ruff`, `tsc`, `ESLint` the standing gate.

1. **Loader lockstep / fail-loud** — `uv run pytest tests/test_product_course.py tests/test_earnings.py`:
   - `load_product_fit()` and `load_commission_config()` both succeed after removal (the catalogue
     and the fit map still match exactly — proving the two stanzas were removed in lockstep).
   - Add a negative assertion: `"connecttrade" not in load_commission_config().products` and
     `"connecttrade" not in load_product_fit().products`.
2. **Sell opportunities** — `uv run pytest tests/test_sell_opportunities.py`:
   - No sell-opportunity result for any assessment lists `connecttrade` (assert it never appears in
     any `opportunities[*].product_id`).
   - The retargeted HL/Revolut case recommends only agreed products, correctly ordered.
   - The GRS-0169 empty-state note path is unaffected (unchanged assertion).
3. **Earnings magnitude unchanged** — `uv run pytest tests/test_earnings.py`:
   - The reassigned OpenBB deal produces the same Year-1/Year-2 commission figures the ConnectTrade
     deal did (identical rate schedule), so the demo earnings totals are byte-stable except the
     product name.
4. **Demo seed** — `uv run pytest tests/test_demo_seed.py` (if it asserts product ids): the WeBull
   showcase deal carries `product_id="openbb"`; no seeded line references `connecttrade`.
5. **Course certs** — `uv run pytest tests/test_course_certs.py`: no `product:connecttrade` cert
   subject/key exists.
6. **Frontend** — `bunx vitest run frontend/components/SellOpportunitiesPanel.test.tsx`: the panel
   renders the retargeted agreed product; "ConnectTrade" appears nowhere.
7. **Repo-wide guard** — `rg -i connecttrade` finds only historical ADR/ticket/report prose (this
   ticket, GRS-0075/0076/0162, the dated staging report), never config, seed, live docs, code, or a
   green test. Record the grep output in the PR.
8. **Golden master untouched** — `uv run pytest tests/test_atlas_engine_golden_master.py`
   (ConnectTrade is not a scoring input; the catalogue change cannot move a score).

## Out of scope

- Adding OpenBB (or any) new fit targets beyond reusing the reassigned deal — the demo deal moves
  product id; product_fit for OpenBB is not re-authored here (one-ticket-one-PR).
- Any change to the commission engine, rate maths, or the two-stream model (ADR-0026 stays; only the
  catalogue contents change).
- Re-signing or adding any real product agreement.
- Editing the dated staging report's historical content.

## Acceptance

`rg -i connecttrade` finds only historical ADR/ticket/report prose; `load_product_fit()` and
`load_commission_config()` load without error (lockstep intact); the demo sell panel recommends only
agreed products and the WeBull deal shows as OpenBB with unchanged earnings magnitude; every test
that named ConnectTrade is retargeted and green; staging re-seeded; golden master byte-identical.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `53364ce` (GRS-0183: remove ConnectTrade from the catalogue).

This ticket carried no *What shipped* record; the commits above are that record.
