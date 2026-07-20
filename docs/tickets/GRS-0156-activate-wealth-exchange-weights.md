# GRS-0156 — Activate the Phase-4 wealth & exchange weights (client-usable)

**Status:** Done (2026-07-20). **Founder-directed** — explicit sign-off to activate. ADR-0037 (now ACTIVATED), ADR-0022, ADR-0038.
**Loop:** Part 2 — the single biggest lever from the re-measure ("indicative, not client-usable" was the universal non-retail ceiling).

## What changed

The research-validated STARTER elicited coefficient sets (GRS-0150) + the critical-control cap
(GRS-0151) were **wired and gated off**. On the founder's sign-off, this **activates** them for wealth
& exchange — a per-profile flip of the two client-usability seams together (ADR-0022):

- **`active.profile_scoring_context`** routes `wealth → elicited_wealth_coefficient_set`, `exchange →
  elicited_exchange_coefficient_set` (both `client_usable=True`, θ + cap κ=0.5). Retail unchanged
  (draft) — **golden master byte-identical**.
- **`active_uncertainty_model(profile_key)`** is now profile-aware: activated profiles draw the
  client-usable elicited §7 widths, retail draws the draft widths. The two models carry identical
  widths, so **no range moves** — this only pairs the client-usability gate so a client pack for an
  activated segment passes and a draft segment still refuses. Callers (live-score, finalise, deliverable
  render) pass the assessment's profile; committee stays retail-global (unchanged).

## Effects
- A **client-facing** wealth/exchange deliverable now renders (both the coefficient gate and the
  uncertainty gate pass). Retail client packs still refuse (draft).
- The wizard **"indicative, not client-usable" caveat now keys on actual client-usability** (GRS-0156),
  not "non-retail": `GET /registry/profiles` exposes `client_usable` per profile; the Overview banner
  and the score-view `ProvisionalScoreBanner` show only for a non-retail profile that is NOT
  client-usable. So the caveat **drops for activated wealth/exchange** but a future draft profile still
  carries it.
- Provenance records the activation honestly: `founder-activated 2026-07-20, panel ratification
  scheduled (review_due)`.

## Tests
`test_elicited_coefficients` — segment sets now active (both seams client-usable; retail draft); the
client-pack gate opens end-to-end for wealth/exchange and refuses for retail.
`test_profile_wizard_routing` — live-score/context version now `{wealth,exchange}-v1-elicited-starter-2026`.
Golden master intact; full backend + frontend green.

## Follow-up (non-blocking)
Formal panel elicitation refines the starter numbers in place (no structural change). If the founder
wants the θ_L operational-maturity variant instead of the research EV-leaning θ, that's a one-line
change to the elicited sets (see `docs/elicitation/scored-effect-analysis.md`).
