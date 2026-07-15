# GRS-0054 — Audit doc/precision fixes (arena gate note, MC reproducibility docstring)

- **Loop:** — (documentation)
- **Status:** Fixed — from the 2026-07-14 audit backlog (GRS-0049, findings API #6 and scoring F4).
- **Severity:** Low — accuracy of the docs, no behaviour change.

## Changes

- **CLAUDE.md #8 (arena gate).** Clarified that practice-arena AI feedback is self-only training
  content that never reaches a client, so its gate is the AI-drafted label + self-scoping rather than
  a recorded approval (unlike extraction / deliverable drafts / weekly quizzes) — a deliberate
  difference, not an omission. This matches what the review verified in the code.
- **`montecarlo.py` reproducibility docstring.** The module and `_perturb` docstrings claimed draws
  consume the RNG in a "fixed registry order". Subcomponents are drawn in registry order, but
  metrics and powers are drawn in **input-tuple order**; determinism therefore holds for a given
  input ordering (which the app fixes canonically via `_complete_inputs`). Corrected the wording to
  be precise — no behaviour change.

## Exit criteria

- The two docstrings accurately describe the reproducibility invariant; CLAUDE.md #8 states the
  arena gate accurately. No code path changes (golden master unchanged).

(The remaining backlog item — humanizing bare single-token registry keys in `labels.ts` — is folded
into PR #55/GRS-0046, which already owns that file.)
