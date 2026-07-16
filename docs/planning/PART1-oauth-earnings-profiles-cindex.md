# Execution plan — Part 1: OAuth · Earnings v7 · Profiles · C-index

**For the execution VM.** Four founder-greenlit workstreams, planned as ADRs + `GRS-` tickets so the build
can proceed without the founder's laptop on. This is the entry point: read the ADR, then the tickets, in
order. (A **Part 2** — a UI/UX review of Advisor Studio — will add more tickets later; not covered here.)

## Workstreams → docs

| WS | Decision (ADR) | Tickets | Gist |
|---|---|---|---|
| **1 · Google OAuth + public-site → app login** | ADR-0024 | GRS-0073 (oauth-signin), GRS-0074 (public-site-login-handoff) | Authorization-code flow, backend mints the *existing* GM JWT; invite-only email match; one-time-code cross-site hand-off; multi-origin CORS. Operator provisions the Google client. |
| **2 · Earnings: Commission Schedule v7** | ADR-0026 (amends ADR-0017) | GRS-0075 (config+models), GRS-0076 (compute+API) | Two-stream model: Stream A product (Yr1/Yr2 + dated window), Stream B consultancy (delivery-type × sourcing matrix), pay-when-paid. Byoung = first-hire validation. |
| **3 · Operating-model profiles** | ADR-0025 | GRS-0077 (mechanism), GRS-0078 (exchange-profile), GRS-0079 (wizard-selector) | Profile = module/critical/weight view over the registry superset. Retail stays default + invariant. **Exchange-first** (active book: ASX, NSE). |
| **4 · C-index (Customer Proposition), Loop 7** | ADR-0023 (Accepted) · Methodology v1.3 (normative, Stage 1) | GRS-0080 (registry+widgets), 0081 (rubrics), 0082 (engine+coeffs), 0083 (wizard+widget-grid), 0084 (benchmark), 0085 (deliverables), 0086 (into-V, v1.4 · gated) | C rides the L aggregation path (`_score_c` clones `_score_l`). Phase-E 10 modules; 93-widget Level-1 evidence. **Stage 1 reports C alongside V — §5.1 untouched, golden master survives.** |

## Suggested order for the VM
1. **WS1 OAuth** — pairs with the just-shipped design alignment; delivers the login story.
2. **WS2 Earnings v7** — self-contained; first-hire-blocking.
3. **WS3 profile mechanism → exchange profile** — build the mechanism first, then the exchange content.
4. **WS4 C-index Stage 1** (build profile-aware, after WS3's mechanism lands). **Stage 2 (GRS-0086) is gated** on the θ_C elicitation panel + a golden-master v2 — do not start it until Stage 1 is done and the panel has convened.

## Hard invariants (do not break)
- **Golden master:** WS3 and WS4-Stage-1 must keep `tests/test_atlas_engine_golden_master.py` byte-identical (`V = 0.478565`). C is *reported alongside* V in v1.3; it enters the composite (`engine.py:76-80`) only at v1.4, which needs a **golden-master v2**. An engine with no elicited `θ_C` must **refuse** a four-index V (never default 0).
- **Fail-loud / ADR-0001:** registry key uniqueness, coefficient completeness (`validate_against`), no silent defaults — extend, never bypass.
- **No client data committed:** OneDrive contracts / engagement packs / review corpus are read reference-only; ingestion is config/seed through scoped storage.
- **Governance:** commission config is governed (ADR-0017/0026); AI-surfaced benchmark ingestion is approval-gated (ADR-0009).

## Needs a human (not blocking the buildable parts)
- **WS1:** the operator provisions the Google OAuth client (`GM_GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI`). Engineering wires the flow; no secrets in the repo.
- **WS4 Stage 2:** the θ_C elicitation panel (I-4) — meanwhile use the existing elicited coefficient set as the launch default.
- **Content track:** Power Primers (D-6) and calibration vignettes are founder-track content dependencies.

## Status of the gating items
All Part-1 decisions/inputs are resolved — see `PENDING-FOUNDER-REVIEW.md` (D-1..D-7 ✅, I-1..I-3 provided, I-4 use-existing, O1 done, O2 → OAuth, O3 pre-release, O4 proceed) and `NEXT-STEPS-2026-07.md` §4.
