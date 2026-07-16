# GRS-0070 — Diagnostic visuals (radar · waterfall · weighted module table · scenario bars)

**Status:** Shipped
**Loop:** Track A (guided consulting UX — delivery review §4, NEXT-STEPS §3.6)
**Branch:** `grs-0070-diagnostic-visuals`

## Why

The delivery review asked for "diagnostic visuals (radar of module q_m, B→P→L→V waterfall, module
table with κ_m, scenario chart)" to make the results legible as a consulting output rather than a
number dump. The `LiveScore` already carried per-module q_m bands but **not** the weights the score
was built from, so the waterfall and κ_m table had no data. This ticket adds those weights
(transparently) and the visuals.

## What shipped

**Contract (additive, safe):** `LiveScore` gains `theta_b/p/l` (the θ value-weights) and
`module_weights` (δ_m). Populated in `assessments/service.live_score` from the active coefficient
set; present only when scoreable. This is transparency of the active coefficients (the `/guide`
already publishes θ), **not** a client price — the client-facing gate stays on deliverables. §5.1 and
the engine are untouched; the committed `LiveScore.json` schema was regenerated (parity green).

**Visuals** (`frontend/components/Diagnostics.tsx`, hand-built inline SVG — no charting dependency,
consistent with the existing div-bar breakdown; theme-aware via CSS custom properties):
- **Maturity radar** — one spoke per module at its q_m (P50); reference rings; the dent points to
  the bottleneck.
- **Value waterfall** — B→P→L→V: each lens contributes θ × its P50, the three stepping up to V
  (score domain only — never currency, ADR-0002).
- **Module table with κ_m** — weakest-first, each module's weight **share** (δ_m normalised) beside
  its q_m band (via the honest `formatBand`).
- **Scenario impact bars** — the Scenarios step's Upgrade Priority Index now renders ΔV as ranked
  horizontal bars (longest = highest-leverage upgrade).

Wired into the Summary step below the triad card, gated on `scoreable`.

**Honesty:** the shape visuals plot the P50 point for orientation; the full P10/P90 uncertainty
stays in the `LiveScorePanel` bands, and the table's q_m column goes through `formatBand` (the tested
ADR-0008 gate). Nothing renders when not scoreable or when weights are absent — never a misleading
empty chart. Kept P10/P50/P90 throughout (delivery-review caveat).

## Tests

`frontend/lib/diagnostics.test.ts` — waterfall contributions sum to V and step cumulatively; module
weights normalise to shares summing to 1 and sort weakest-first; fail-soft to empty when not
scoreable / weights absent; radar geometry (spoke 0 at 12 o'clock). Backend schema parity + full
suite green; frontend type-check · lint · vitest green.

## Not in scope

- Structured create + Step-1 business profile — GRS-0068.
- "Your Brokerages" portfolio home — GRS-0071.
