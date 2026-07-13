# GRS-0025 — Practice Arena v1

- **Loop:** 5
- **Branch:** `grs-0025-practice-arena`
- **Status:** In review
- **Normative source:** PRD §6 (Practice Arena; vignettes double as calibration content); CLAUDE.md #8.
- **Depends on:** GRS-0022 (vignettes), GRS-0017 (gated-AI plumbing pattern).

## Goal

AI-simulated client sessions: advisors practise discovery against a role-played client executive, scored against ATLAS extraction completeness.

## Scope

1. Session runner (Claude Agent SDK): the model role-plays a client executive built from an anonymised vignette profile; advisor conducts a discovery conversation in chat.
2. Scoring against extraction completeness: which of the 7 powers were probed (benefit AND barrier), which modules were evidenced, whether E-grade-raising questions were asked; model answers rendered after the session.
3. AI feedback is a proposal, visibly labelled as AI-drafted (non-negotiable #8); no client data anywhere near the arena — vignettes only.
4. Session scores persist to advisor history (certification evidence + bench queue input).
5. Arena scenarios reuse calibration vignettes (single content pipeline).

## Exit criteria

- A full arena session runs end-to-end with rubric-based scoring against a fixture transcript (deterministic scoring test; the role-play itself exercised manually). ✅
- Feedback labelled AI-drafted; scores persist and appear in advisor history. ✅
- Full gate green; CI green. ✅

## Implementation notes

- Deterministic scorer `workbench/arena.py::score_transcript` (golden-mastered at completeness
  0.625); AI feedback behind an injectable `ArenaFeedbackDrafter` port (offline Template impl for CI),
  `AI-DRAFTED`-labelled with `feedback_is_ai_drafted`/`drafter_version` — the *number* is
  deterministic, not model-authored (#8). Design recorded in ADR-0015.
- Scenario authoring admin-only; sessions owner-scoped (foreign session → 404) and single-shot
  (re-submit → 409). No client data — anonymised vignettes only (#9).
