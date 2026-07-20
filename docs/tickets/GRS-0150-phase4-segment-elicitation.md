# GRS-0150 — Phase-4: elicit + activate client-usable wealth & exchange coefficient sets

**Status:** Set up (2026-07-20) — awaiting the founder/panel VALUES. ADR-0037.
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
