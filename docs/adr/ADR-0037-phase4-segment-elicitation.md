# ADR-0037 — Phase-4 weight/critical elicitation for the wealth & exchange profiles

- **Status:** Proposed (2026-07-20). Founder-directed — the ceiling the mock-advisor re-measure identified (4 of 5 personas, HIGH): non-retail assessments self-declare "indicative, not client-usable."
- **Date:** 2026-07-20
- **Deciders:** Founder + the Bruntsfield weight-elicitation panel (the panel VALUES are the deliverable of this ADR; engineering only wires them in).
- **Normative source:** `docs/ATLAS-Methodology-v1.2.md` §6 (weight elicitation), ADR-0006 (weights live in the CoefficientSet), ADR-0022 (elicited-coefficient activation), ADR-0035 (segment fit, Phase 4).
- **Implements:** ADR-0035 Phase 4. **Couples with:** ADR-0025 (profiles), ADR-0009 (client-pack gate).

## Context

The wealth and exchange operating models are now segment-native across L (infrastructure) and B
(metrics) — GRS-0147c/d/g. But both still score with **draft, uniform** coefficient sets
(`draft_wealth_coefficient_set` / `draft_exchange_coefficient_set`, `client_usable=False`), so every
non-retail assessment carries the honest banner *"weights & criticals pending elicitation — scores are
indicative, not client-usable."* The GRS-0015 client-pack gate refuses a client-facing deliverable
from a non-client-usable set (correct, ADR-0009). **This is the single lever that moves the four
non-retail personas from ~72–78 toward client-grade.**

Per non-negotiable #2, weights are settled by **elicitation, provenanced and recorded — never a silent
engineering edit**. Retail already did this: `elicited_v1_coefficient_set` is the client-usable,
panel-provenanced template, held behind the `active_coefficient_set` seam (default = draft) and flipped
only on panel sign-off (ADR-0022). Phase 4 does the same for wealth and exchange.

## Decision

**Run the wealth and exchange weight/critical elicitation panels, then activate in one recorded commit
per profile.** Three parts:

1. **The panels produce the values** (the deliverable of this ADR — founder + panel). Each panel
   elicits, per profile, every CoefficientSet family the engine reads. The exact families, their
   meaning, and their current draft placeholders are laid out as fill-in worksheets:
   - `docs/elicitation/wealth-elicitation-worksheet.md`
   - `docs/elicitation/exchange-elicitation-worksheet.md`
   Method: swing-weighting / Delphi over the panel (Methodology §6), the same protocol retail used;
   each family records method, dispersion, and an annual review-due date (a `WeightProvenanceRecord`).

2. **Engineering wires the values in** (one PR per profile, once the worksheet is filled):
   author `elicited_wealth_coefficient_set` / `elicited_exchange_coefficient_set` mirroring
   `elicited_v1_coefficient_set` exactly — the filled θ/α/δ/w_metric/group_weights/criticals +
   provenance, `client_usable=True`, pinned by a golden-master fixture. No structure changes; the sets
   `validate_against` their profile view (fail-loud on any missing/unknown key).

3. **Activation is a single recorded flip** (ADR-0022): `profile_scoring_context` routes the profile to
   its elicited set instead of the draft. That one-line change (a) removes the "not client-usable"
   banner for that profile and (b) lets the client-pack gate produce a client-facing deliverable. It is
   deliberate, dated, and reviewable — never automatic, never an env toggle.

## What the panels must decide (per profile)

Both wealth and exchange (the worksheets carry the exact keys + current draft values):
- **θ split** `θ_B / θ_P / θ_L` (must sum to 1; draft 0.30/0.30/0.40).
- **α_l** and per-module **α** (bottleneck aggression; draft 0.7).
- **δ** — the module weights across the profile's modules (draft uniform 1.0 each).
- **w_metric** + **group_weights** — the B-index metric and group weights (draft uniform).
- **w_power** — the 7-power weights (draft uniform).
- **critical_modules_for_l** — which modules gate L (wealth draft = App Server/CMS/Back Office;
  exchange draft = App Server/OEMS/Liq-Connect).
- **strength_encoding** — the None/Emerging/Established/Wide → score mapping (draft uniform steps;
  retail elicited uses 0/0.35/0.70/1.0).

## Consequences

- New `elicited_wealth_coefficient_set` / `elicited_exchange_coefficient_set` + fixtures + the
  `profile_scoring_context` activation branches (gated on `client_usable`).
- Until each panel signs off, the profile stays on its draft set — the banner and the gate are
  unchanged, honestly. Nothing here fabricates or activates a weight.
- The retail golden master is untouched (retail already has its own elicited set, also gated off).

## Alternatives considered

- **Ship authored "good-enough" weights and flip client-usable now.** Rejected — non-negotiable #2:
  a client-grade score must trace to an elicitation panel with provenance, not an engineer's guess.
  The draft banner is the honest state until the panel runs.
- **One shared elicited set across profiles.** Rejected — an exchange's θ/δ/criticals are not a wealth
  manager's; benchmark comparability (ADR-0025) also requires per-profile coefficient versions.
