# GRS-0041 — Expose gated module rating words in the live-score contract

- **Loop:** 6 (scoring surface)
- **Status:** Triage — found in the 2026-07-14 post-redesign audit. NOT yet built (contract change).
- **Severity:** Medium — a real gap between what the engine computes and what the advisor/client sees.
- **Normative source:** ATLAS Methodology v1.2 §5.2 (the module rating gate); ADR-0003 (rating gate);
  CLAUDE.md #7 (two-track: continuous scores prioritise, rule-based gates produce the headline words).

## Problem

ATLAS is two-track (ADR-0002): the continuous `q_m` prioritises *what to fix first*, and a
**rule-based rating gate** produces the **headline word** per module (Basic → Developing → Advanced →
Frontier) — and a module can be Advanced-by-number yet **Developing-by-gate** (e.g. a critical
subcomponent is Basic). The redesign's LiveScorePanel now surfaces the `q_m` bottleneck and a
weakest-first module breakdown — good — but the **gated rating words** are **not in the `LiveScore`
contract**, so the client never sees the boardroom word the methodology says it should ("what you
defend in the boardroom", per `/guide`). The engine already computes them (`gate_band` /
`gate_bands` on `AtlasResult`); they just aren't plumbed to the live-score / client surface.

## Change (scope for the implementing ticket)

1. **Contract:** add the per-module gate band (and its blocked/critical reason where relevant) to the
   `LiveScore` response model in `bcap-contracts` (Pydantic + JSON Schema + TS mirror). Keep it words,
   never decimals (the triad/gate outputs are ordinal — no score/currency mixing).
2. **Backend:** populate it from the engine's existing `gate_bands` on the live-score path (no new
   scoring — it's already computed; just exposed).
3. **Frontend:** show the gated word next to each module in the LiveScorePanel / module breakdown,
   visually distinct from the `q_m` number, and explain when the two diverge (Advanced-by-number,
   Developing-by-gate) — the single most important "words rate, numbers rank" teaching moment.

## Exit criteria

- The live score returns each assessed module's gated band word; the UI shows it distinctly from the
  continuous score.
- Golden-master/contract tests pin the words; schema parity holds; the two-track separation is intact.
