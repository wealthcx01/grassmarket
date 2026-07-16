# GRS-0069 — Guided power cards (7 Powers step)

**Status:** Shipped
**Loop:** Track A (guided consulting UX — delivery review §4, NEXT-STEPS §3.6)
**Branch:** `grs-0069-guided-power-cards`

## Why

The delivery review found the wizard is "data-entry, not the guided consulting workflow the UX brief
specifies." The Strategic Powers step rendered only each power's *name* — even though the registry
already ships a full Helmer definition (`RegistryPower.description`) and lifecycle stage that were
going unused, and the `PowerEntry` contract already carries `benefit_evidence`/`barrier_evidence`
fields the UI never exposed. This ticket turns the step into a guided card.

## What shipped

`frontend/components/steps.tsx` — `StrategicPowersStep`:
- **Plain-English definition** surfaced from `RegistryPower.description` (previously unused).
- **Lifecycle badge** (Origination / Take-off / Stability) from `RegistryPower.lifecycle_stage`.
- **Benefit / Barrier hints** — the Benefit and Barrier labels + selects carry a per-power tooltip
  explaining what a strong benefit vs. barrier *means for that specific power*.
- **"In a brokerage…" example** — a toggle-expandable, illustrative brokerage/trading-platform
  example per power (the `Guidance` toggle pattern reused from the Infrastructure step).
- **"Why this benefit? / Why this barrier?"** optional rationale inputs, wired to the contract's
  `benefit_evidence` / `barrier_evidence` fields (records *why*, the guided-consulting depth the brief
  asks for; an empty string collapses to null so the engine sees absent = blank).
- **Kept benefit/barrier + evidence grades exactly** — the retired 0–10 power slider is NOT
  introduced (delivery review caveat).

`frontend/lib/powerGuidance.ts` (new) — `POWER_GUIDANCE`, per-power `benefitHint` / `barrierHint` /
`example`. Teaching aids grounded in the settled 7 Powers framework (same spirit as the `/guide`
primer's static content) — deliberately generic ("a broker where…"), never a scored claim about a
named firm.

`frontend/lib/doc.ts` — `powerEntry` extended with optional `benefitEvidence` / `barrierEvidence`
(trailing, backward-compatible; existing callers serialise identically).

## Tests

`frontend/lib/powerGuidance.test.ts` — guidance covers exactly the 7 registry power keys, and every
entry has non-empty hints + example (a new power can't ship without guidance). Full frontend suite
(type-check · lint · vitest) green.

## Not in scope

- Diagnostic visuals (radar / waterfall) — GRS-0070.
- Structured create + Step-1 business profile — GRS-0068.
- No backend/contract change (the fields used already existed).
