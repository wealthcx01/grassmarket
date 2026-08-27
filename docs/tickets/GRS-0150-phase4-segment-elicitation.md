# GRS-0150 — Phase-4: elicit + activate client-usable wealth & exchange coefficient sets

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: Set up (2026-07-20) — awaiting the founder/panel VALUES. ADR-0037._
**Loop:** Part 2 — segment fit, Phase 4 (founder/panel-gated per non-negotiable #2)

## Why

The full mock-advisor re-measure (mean 57→73) identified the one universal ceiling, flagged HIGH by all
4 non-retail personas: wealth & exchange assessments self-declare *"indicative, not client-usable"*
because their weights/criticals are still uniform drafts. Flipping them client-usable is the lever from
~73 toward client-grade — but weights are elicited + provenanced, never an engineering guess (#2).

## Set up (done)
- **ADR-0037** — the elicitation protocol + one-commit activation plan.
- **Worksheets** the panel fills: `docs/elicitation/{wealth,exchange}-elicitation-worksheet.md` — every
  CoefficientSet family (θ, α, δ module weights, w_metric + group weights, w_power, critical modules,
  strength encoding) with the current draft placeholders and blank Elicited columns.

## Remaining (needs founder + panel, then a PR each)
1. Founder/panel runs the wealth + exchange elicitation (fills the worksheets).
2. Engineering authors `elicited_wealth_coefficient_set` / `elicited_exchange_coefficient_set`
   (mirror `elicited_v1_coefficient_set`): the filled values + a `WeightProvenanceRecord` per family,
   `client_usable=True`, pinned by a golden-master fixture, `validate_against` the profile view.
3. **Activate** — route the profile through its elicited set in `profile_scoring_context` (one recorded
   commit, ADR-0022). That removes the "not client-usable" banner and lets the client-pack gate produce
   a client-facing deliverable for that segment.

## Acceptance (per profile, when activated)
- A finalised wealth/exchange assessment produces a **client-facing** deliverable (no draft watermark);
  the wizard drops the "indicative, not client-usable" banner; benchmark rows carry the elicited
  coefficient version. Retail golden master untouched.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `57b8965` (GRS-0150: research-refined elicited wealth+exchange starter sets (gated off) +).

This ticket carried no *What shipped* record; the commits above are that record.


---

## D1 decided 2026-08-27 — the interim shortcut was tried and rejected

Both interim options were built and measured. Neither survived:

- **Ratifying the running weights** would have blessed uniform 1.0 across every weight family as a
  method.
- **Activating the v1 set** buys only four different scalars (θ, α_L, α_module, one strength step) —
  every weight family is uniform in that set too — and it broke firm-ordering stability: perturbing
  the strength encoding by ±20% reordered the showcase firms in 3 of 40 draws, where the draft set
  never did.

**So this ticket is now the only route.** Retail cannot produce a client-facing deliverable until a
real elicitation happens, and that is a deliberate, recorded state rather than an oversight.

The measurement harness built along the way (`tools/weight_sensitivity.py`) is what caught the
ordering problem, and should be re-run against whatever the panel produces before it is activated.
