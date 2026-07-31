# GRS-0185 — Brandfetch variant segment scoping

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: In review (2026-07-26) — profiles split, stanzas differentiated, Academy note._
added; PR open. (2026-07-23, founder feedback item 13.) **Priority:** MED-HIGH.
**Loop:** founder-feedback remediation, Wave 1. Amends the ADR-0039 fit map (config).

## Why

Both Brandfetch variants currently carry identical fit stanzas and `profiles: [retail]`, so a
retail report can be recommended either. The founder's correction: distribution suits retail
brokerages; redistribution suits exchanges and information vendors. The sell panel should never
offer the wrong variant to a segment.

## Scope

A config-only re-scoping of the two Brandfetch variants in the ADR-0039 fit map, plus the tests
that lock the segment separation and a one-line Academy note. No engine change; the sell-opportunity
join (`src/grassmarket/earnings/opportunities.py`) already filters product fits by the assessment's
operating-model profile, so correcting the profiles is sufficient to fix which variant each segment
sees. The two YAMLs are validated in lockstep by `load_product_fit()`
(`packages/bcap_contracts/src/bcap_contracts/product_fit.py`), which also refuses any unknown
operating-model profile (lines 97-103) and unknown registry keys (106-116) — so a profile typo fails
loud at load.

1. **`product_fit.yaml` — split the profiles**
   (`packages/bcap_contracts/src/bcap_contracts/registry_data/product_fit.yaml`):
   - `brandfetch_distribution` (line 44) stays `profiles: [retail]`.
   - `brandfetch_redistribution` (line 53) moves from `profiles: [retail]` to `profiles: [exchange]`.
     Decision: `[exchange]` only for now, not an information-vendor profile, because no information-
     vendor profile key exists in the registry yet (`load_profiles()` would reject it — fail loud);
     when one is added it joins this list. The comment records the intended future
     `[exchange, information_vendor]`.
   - `commissions.yaml` is unchanged — both products keep their existing rate stanzas (lines 23-32);
     only the FIT profiles move, and the lockstep loader still sees both products in both files, so
     the pairing stays consistent.

2. **Differentiate the two stanzas' pitches and fit targets** so each explains its own segment's
   motive rather than sharing near-identical copy:
   - `brandfetch_distribution` (retail): keep `modules: [CMS, FRONTEND]`, `c_modules:
     [CUST_UI_NAVIGATION]`, `powers: [BRANDING]`. Pitch (STYLE-VOICE register): brand assets rendered
     inside the client's OWN app — keeping every instrument and merchant surface on-brand, a fix for
     content-management and front-end consistency gaps that cheapen a retail UI.
   - `brandfetch_redistribution` (exchange/vendor): the motive is licensed REDISTRIBUTION of brand
     data downstream to the client's own customers, not the client's app chrome. Adjust the targets
     to that motive: this is a data-licensing/distribution capability, so drop `c_modules:
     [CUST_UI_NAVIGATION]` (a retail customer-navigation module that does not describe a venue's
     redistribution use) and keep `modules: [CMS, FRONTEND]` + `powers: [BRANDING]` as the brand-asset
     coverage. Decision: differentiate the fit targets, not just the prose, so the redistribution
     variant is matched against a venue's actual gaps and never surfaces on a retail-only C-module.
     (Only registry keys legal for the `exchange` profile view may be used; the loader enforces this.)
   - Both pitches are rewritten so a reader can tell the two apart at a glance: distribution = "your
     app on-brand"; redistribution = "license brand data to serve your customers".

3. **Academy note** (`src/grassmarket/workbench/content/brandfetch_course.py`): the course already
   carries both commission tiers (`BRANDFETCH_PRODUCT_ID = "brandfetch_distribution"`,
   `BRANDFETCH_REDIST_ID = "brandfetch_redistribution"`, the two-tier lesson `_two_tier_commission_lesson`
   ~lines 363-386). Add a single-line segment note to each tier's lesson copy: distribution → retail
   brokerages; redistribution → exchanges and information vendors. Decision: a one-line note only; the
   full per-segment course split lands with GRS-0191, so this ticket does not restructure the course
   modules — it just stops the two tiers reading as interchangeable.

4. **No new empty-state work** — the GRS-0169 empty-state note (the "segment not covered yet"
   message when the catalogue has no applicable product) already fires from the sell-opportunity join
   when a segment matches nothing; re-scoping the profiles means an exchange report that has no other
   applicable product but does match redistribution now shows redistribution, and a retail report
   that matched only redistribution before now correctly shows nothing from that variant. The note
   path is unchanged; this ticket only asserts it still fires.

## Test plan

Backend pytest (offline); frontend vitest per file; `pyright`, `ruff`, `tsc`, `ESLint`, and the
schema-validate/loader gate the standing checks.

1. **Loader fail-loud** — `uv run pytest tests/test_product_course.py`:
   - `load_product_fit()` succeeds after the profile split (both products present in both YAMLs;
     `exchange` is a known profile; all fit keys legal for their profile view).
   - Negative: a deliberately wrong profile (e.g. a nonexistent `informationvendor`) makes
     `load_product_fit()` raise `ProductFitError` — proving fail-loud on key drift (this can be a
     parametrised/monkeypatched case, not a committed bad YAML).
2. **Segment separation** — `uv run pytest tests/test_sell_opportunities.py` (extend the existing
   brandfetch cases at lines 189-190):
   - A **retail** assessment's sell opportunities NEVER list `brandfetch_redistribution` (assert its
     id is absent from every `opportunities[*].product_id`), and MAY list `brandfetch_distribution`
     against a CMS/FRONTEND/UI-navigation/branding gap.
   - An **exchange** assessment's sell opportunities NEVER list `brandfetch_distribution`, and list
     `brandfetch_redistribution` when the relevant gaps are assessed-and-weak.
   - The GRS-0169 empty-state note still appears for a segment with no applicable product (unchanged
     assertion).
3. **Earnings/carrot unaffected** — `uv run pytest tests/test_earnings.py`: both variants keep their
   existing rate stanzas, so the commission carrots for `brandfetch_distribution` /
   `brandfetch_redistribution` are numerically unchanged (the profile move touches fit, not rates).
4. **Course note** — `uv run pytest tests/test_brandfetch_course.py`: both tiers still resolve live
   (`dist.yr1_bps > redist.yr1_bps`), the module/lesson counts hold, and each tier's lesson now
   carries its segment note (assert the retail/exchange phrasing is present).
5. **Frontend** — `bunx vitest run frontend/components/SellOpportunitiesPanel.test.tsx`: a retail
   mock never renders the redistribution variant; an exchange mock renders it with its segment-correct
   pitch.
6. **Golden master untouched** — `uv run pytest tests/test_atlas_engine_golden_master.py` (fit
   profiles are not a scoring input).

## Out of scope

- The full per-segment Brandfetch course split — GRS-0191 (this ticket adds a one-line note only).
- Adding an `information_vendor` operating-model profile to the registry — redistribution is scoped to
  `exchange` until that profile exists (one-ticket-one-PR).
- Any change to commission rates, the two-stream model, or the sell-opportunity ranking logic.
- Re-scoping any other product's fit stanza.

## Acceptance

Retail and exchange sell panels each show only their applicable Brandfetch variant, with a segment-
correct pitch (distribution = the client's own app on-brand; redistribution = licensed brand data
served downstream); a retail report never lists redistribution and an exchange report never lists
distribution (proven by test). `load_product_fit()` fails loud on any profile/key drift; the
GRS-0169 empty-state note still fires; commission rates and the golden master are untouched.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `55e34f5` (GRS-0185 + GRS-0187: scope Brandfetch by segment, surface Stream B).

This ticket carried no *What shipped* record; the commits above are that record.
