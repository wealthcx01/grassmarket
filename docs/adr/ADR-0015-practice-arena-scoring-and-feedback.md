# ADR-0015 — Practice Arena: deterministic scoring, AI-drafted feedback, no client data

- **Status:** Accepted
- **Loop:** 5 (GRS-0025)
- **Normative source:** PRD §6 (Practice Arena; vignettes double as calibration content);
  CLAUDE.md #8 (AI proposes, humans approve); #9 (data scoping absolute).
- **Builds on:** ADR-0012 (calibration vignettes, the anonymised profiles the arena role-plays);
  ADR-0014 (the injectable-drafter / gated-AI pattern the feedback reuses).

## Context

The Practice Arena lets an advisor rehearse a discovery conversation against an AI-role-played client
executive, then be told how complete their extraction was. Two halves have very different trust
requirements. The **role-play** is a live, non-deterministic Claude conversation — untestable in CI
and unscorable byte-for-byte. The **assessment of the transcript** is the thing that feeds an
advisor's history and, downstream, certification evidence and the bench queue — so it must be exact,
reproducible, and never fabricated. Pinning both under one "AI session" would make the score as flaky
as the chat. Three questions needed deciding: what is deterministic vs. live, how feedback stays a
labelled proposal (#8), and how the arena avoids touching client data (#9).

## Decision

### 1. Split the live role-play from a deterministic, golden-mastered score

The transcript is scored by a pure function (`workbench/arena.py::score_transcript`) over the
submitted turns — no model call, no clock, no I/O. It measures extraction completeness against the
scenario's targets:

- **Powers** — a power is *fully probed* only when BOTH its benefit cue AND its barrier cue appear in
  the advisor's turns (0.5 credit for one side, 1.0 for both). Probing benefit without barrier is a
  half-answer, and the score says so.
- **Modules** — a module is *evidenced* when any of its cues appear (1.0 each).
- **Evidence questions** — E-grade-raising asks ("can you show", "do you have data") are counted.
- **Completeness** = `round(achieved / possible, 6)`, or `0.0` when a scenario targets nothing.

Only **advisor** turns count — client turns are lower-cased context, never scored, so a client who
volunteers the answer cannot inflate the advisor. The whole thing is **golden-mastered**
(`test_arena_scoring.py`): a hand-computed fixture pins `completeness = 0.625` with SCALE fully
probed, NETWORK benefit-only, APP_SERVER evidenced, one evidence question — the scorer can never
silently drift. The live role-play is exercised manually; CI never makes a live call.

### 2. Feedback is AI-drafted, labelled, and never authoritative (#8)

Coaching feedback goes through an injectable `ArenaFeedbackDrafter` port (a deterministic offline
`TemplateArenaFeedbackDrafter` for CI, versioned `template-arena-feedback-v1`; the real Claude drafter
plugs in behind the same call). Every drafted string is prefixed with the `AI-DRAFTED` label, the
session carries `feedback_is_ai_drafted = True` and the `drafter_version`, and the **numeric score is
computed deterministically, not by the model** — the advisor's history records a real measurement, and
the prose around it is visibly a machine draft. AI proposes the coaching; the deterministic scorer,
not the model, decides the number.

### 3. No client data — vignettes only, and sessions are owner-scoped (#9)

Scenarios are authored from anonymised vignette profiles (ADR-0012), never from a real engagement, and
the arena has no path to prospect/engagement data. Scenario authoring is **admin-only** (a
`ScopeViolationError` otherwise) but the scenario library is org-shared reading. A **session** is
private to the advisor who ran it: `submit`, `get`, and `list` all go through `_assert_can_access`, so
one advisor can neither see nor score another's session (404, not 403 — a foreign session is not shown
to exist). Submission is single-shot: a session already `SCORED` refuses re-submission
(`ConflictError` → 409), so a score is immutable once recorded.

## Consequences

- The arena score is reproducible and pinned by a golden master; feedback flakiness lives entirely in
  the un-scored prose, never in the number that reaches an advisor's history.
- Sessions become certification evidence and bench-queue input (GRS-0026) with the same
  owner-scoping and immutability guarantees the rest of the platform has.
- **Accepted scope boundaries:** the live Claude role-play driver (the session runner) and the real
  feedback drafter are founder-track wiring behind the ports defined here — the scorer, the gate, the
  label, and the persistence are in place for them. The scenario *content* (the vignette question
  banks) is authoring, not code. Bench-queue consumption of these scores is GRS-0026.
