# GRS-0196 — Practice Arena v2: an AI client to practise against

**Status:** OPEN (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-23, founder feedback item 22). **Priority:** MED-HIGH._
**Loop:** founder-feedback remediation, Wave 4. Founder decision 23/07: build in-house, no
imported mechanism.

## Why

The arena's intent is right and the founder says so — but the advisor currently types BOTH sides
of the role-play ("Add my line" / "Add client line") and is then keyword-scored, which is
"horrible to use and makes no sense".

## Scope

1. **Roleplay seam (the AI client).** New Protocol `ArenaClientRoleplay` in
   `src/grassmarket/workbench/arena.py`, alongside `ArenaFeedbackDrafter`:
   `version: str` and `reply(scenario: ArenaScenario, history: Sequence[ArenaTurn]) -> str` —
   returns the client persona's next line given the conversation so far. Two implementations:
   - `ClaudeArenaRoleplay` (Claude Agent SDK), constructed **only** in the router, prompted with
     the scenario `brief` + `client_persona` and instructed to stay in character and never coach.
   - `ScriptedArenaRoleplay` (fixture), constructed in tests, replying deterministically from a
     scripted list so CI makes no live call — the same seam pattern as `GoogleOAuthClient` and
     `ArenaFeedbackDrafter`/`TemplateArenaFeedbackDrafter`.
   Decision on gating: the client's turns are AI-authored but the arena is self-only training
   content that never reaches a client, so — exactly like the feedback drafter — it carries **no**
   ActiveGraph approval record; the gate is the self-scoping plus an AI-authored label on the
   client turns in the UI (the deliberate non-negotiable #8 exception, ADR-0009). No approval
   policy is added.
2. **Turn-by-turn advance.** New repository method
   `advance_arena_session(principal, session_id, *, advisor_line, roleplay, now) -> ArenaSession`
   in `src/grassmarket/data/repository.py`, beside `submit_arena_session` (~4487): loads the
   caller's own session (404 on foreign/unknown via `_assert_can_access`), refuses a session that
   is not `IN_PROGRESS` (`ConflictError` → 409), appends the advisor `ArenaTurn`, calls
   `roleplay.reply(scenario, history)`, appends the returned client `ArenaTurn`, persists the grown
   transcript to `ArenaSessionORM.transcript_json`, and returns the session (still `IN_PROGRESS`).
   New endpoint `POST /arena/sessions/{id}/reply` in `src/grassmarket/web/routers/arena.py` with
   body `ArenaReplyRequest{ advisor_line: str = Field(min_length=1) }` → 200 `ArenaSession`; 404
   foreign/unknown; 409 already scored. The real `ClaudeArenaRoleplay` is injected here via a
   dependency; tests override the dependency with `ScriptedArenaRoleplay`.
3. **End + score — scorer untouched.** `POST /arena/sessions/{id}/submit` changes semantics: it no
   longer accepts a caller-supplied transcript (the `SubmitRequest` body is removed). It scores the
   **accumulated stored transcript** by calling the existing `submit_arena_session`, which is
   refactored to read `row.transcript_json` instead of a `transcript` argument; it then calls
   `score_transcript(scenario, transcript)` and `drafter.draft(...)` exactly as today. Refuses an
   empty transcript with 409 "Nothing to score — conduct the discovery first." Decision: submit
   scores only what the roleplay actually produced, which removes the fabricated-transcript path
   entirely. **`score_transcript` (arena.py ~47–80) is byte-for-byte unchanged; the deterministic
   cue scorer stays the score of record and the golden master must remain identical.**
4. **Frontend rewrite.** `frontend/components/workbench/ArenaPanel.tsx`
   `ArenaSessionView` replaces the dual "Add my line / Add client line" buttons (~196–201) with a
   single advisor input: on send, `api.arenaReply(session.id, advisorLine)` posts and the returned
   session's last two turns (advisor + AI client) render; the client bubble carries a small
   `AI` label. A single "End & score" button calls `api.submitArenaSession(session.id)` (now
   argument-free). The scored view (deterministic completeness + AI-DRAFTED coaching) is unchanged.
   `frontend/lib/api.ts`: add `arenaReply(sessionId, advisorLine)` (POST `/reply`) and change
   `submitArenaSession(sessionId)` to send no transcript.
5. **History becomes progress.** The "Your history" section (~87–103) becomes a progress view:
   a completeness trend across scored sessions (reuse the `arena_trend` already on
   `PerformanceSummary`), per-power coverage (how often each `power_key` was fully probed across
   the advisor's sessions, computed client-side from `api.arenaSessions`), and each row links to
   its scenario and — where the scenario maps to a course — the relevant Academy course. No new
   contract field is required (trend + per-session scores already exist).
6. **Offline CI.** `ScriptedArenaRoleplay` drives the full flow (start → several replies → submit)
   in tests with no network. The real `ClaudeArenaRoleplay` is never constructed in tests.

## Test plan

Backend (pytest, offline):
- New/extended `tests/test_arena.py`:
  - `advance_arena_session` with a scripted roleplay appends exactly one advisor turn and one
    client turn per call; the transcript grows across three calls in order.
  - Scoring the accumulated transcript equals `score_transcript(scenario, stored_transcript)`
    exactly — the two are asserted identical (the scorer path is unchanged).
  - Golden master: `tests/test_arena_scoring.py` (the deterministic scorer's golden master) is
    **unchanged and green** — no stored score changes.
  - Scoping: advisor B calling `POST /arena/sessions/{A}/reply` or `.../submit` → 404 (foreign
    session not shown to exist); advisor A can advance/submit their own.
  - 409: replying to an already-scored session; submitting a session with an empty transcript.
  - `POST /reply` uses the injected `ScriptedArenaRoleplay` (dependency override) — no live call.
- `tests/test_arena.py` retains the `TemplateArenaFeedbackDrafter` coverage: submit still attaches
  AI-DRAFTED, self-scoped feedback.

Frontend (vitest, per-file):
- `bunx vitest run frontend/components/workbench/ArenaPanel.test.tsx`: the advisor types only their
  own line; sending shows the advisor bubble and the mocked AI client bubble (with the AI label);
  "End & score" renders the deterministic completeness and the AI-DRAFTED coaching; the history
  section renders the completeness trend and per-power coverage and links each session to its
  scenario.

## Out of scope

- Any change to `score_transcript`, `ArenaScore`, `ArenaTurn`, or the golden master (immutable).
- Turning arena feedback into an approval-gated, client-facing artifact (the self-scoped #8
  exception is deliberate and preserved).
- Persisting the roleplay prompt/model version as a scoring input (the score derives only from the
  advisor's turns; the client turns are context, not scored).
- One ticket = one branch = one PR.

## Acceptance

An advisor can run a believable discovery conversation against an AI client — typing only their own
lines, seeing labelled AI client replies — and on "End & score" receives the deterministic
extraction-completeness score plus AI-DRAFTED coaching; the full flow runs in CI offline via the
scripted roleplay; the scorer golden master is byte-identical; a foreign advisor cannot advance or
score another's session (404).

---

## Status reconciliation — 2026-08-01

**OPEN.** No implementing commit on main; genuinely unbuilt.
