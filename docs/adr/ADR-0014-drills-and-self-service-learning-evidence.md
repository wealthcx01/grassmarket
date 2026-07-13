# ADR-0014 — Power Drills (SM-2) and self-service learning evidence

- **Status:** Accepted
- **Loop:** 5 (GRS-0024)
- **Normative source:** PRD §6 (Workbench: spaced-repetition drills, learning content, weekly quiz);
  CLAUDE.md #8 (AI proposes, humans approve).
- **Builds on:** ADR-0013 (the certification evidence this feeds); ADR-0009 (the AI-proposes /
  human-approves pattern the weekly quiz reuses).

## Context

The Workbench's teaching half needs three things wired: a spaced-repetition scheduler for Power
Drills, learning content whose completion counts toward certification, and a weekly AI-generated quiz
that must never reach an advisor unreviewed. Two design questions needed pinning: which scheduling
algorithm (and how to keep it deterministic), and how content completion interacts with the
admin-only certification evidence GRS-0023 established.

## Decision

### 1. Drills use SM-2, deterministic and golden-mastered, with an injected clock

The scheduler is a pure implementation of SuperMemo SM-2 (`workbench/drills.py`): quadratic-free,
easiness-factor updated every review and floored at 1.3, interval 1 → 6 → ×easiness, a lapse (grade
< 3) resetting to a 1-day interval. It is **golden-mastered** — a hand-computed review sequence
(κ-style) pins the exact easiness/interval/repetition values, so the schedule can never silently
drift. The repository never calls `datetime.now()` inside; the clock is **injected** (`now=`) at
every scheduling call, so the round-trip (due → answered → rescheduled) is deterministic under test.
A grade outside 0..5 is refused, not clamped.

### 2. Learning completion grants evidence self-service; the PROMOTION stays admin-gated

GRS-0023 made certification evidence admin-recorded so an advisor cannot self-certify. Learning
completion appears to conflict — an advisor completes a module themselves. The resolution splits
evidence by whether the advisor can honestly self-report it:

- **Coursework is self-service.** Completing a coursework module is binary and platform-verifiable
  ("did the module"), so the coursework credit is the advisor's to earn — written directly to their
  certification record and **audited as a `CertificationEvent`** (attributed to the advisor, "via
  learning module").
- **The exam is objective, so it is NEVER self-attested.** A score is only meaningful if it cannot be
  chosen by the person it certifies. So an exam-quiz *here* is **practice content**: completing one
  may record a self-assessment score on the completion (the advisor's own tracking), but it does
  **not** grant any certification credit. The certification rubric exam stays **proctored /
  admin-recorded** (GRS-0023 `record_exam`) — a self-service completion can neither manufacture a
  passed exam nor overwrite a proctored score.
- **Experiential evidence stays admin-recorded** (shadow assessments, observed lead, sign-off), and
  **the promotion itself stays admin-only** (ADR-0013 unchanged).

So an advisor earns their coursework credential by doing the work, but the exam and every rung change
stay human-gated. Self-*study* is possible; self-*certification* is not.

### 3. The weekly quiz is AI-drafted and gated (#8), advisor-invisible until approved

Generation goes through an injectable `QuizDrafter` port (a deterministic offline `TemplateQuizDrafter`
for CI; the real Claude drafter plugs in behind the same call). A drafted quiz is stored `PROPOSED`
and is **invisible to advisors**: `list_quizzes` filters non-admins to APPROVED, and `get_quiz`
returns 404 for a non-admin on a non-approved quiz (not shown to exist). Only an admin approves or
rejects; approval is what makes it visible. AI content never reaches an advisor unreviewed.

## Consequences

- The drill schedule is reproducible and pinned by a golden master; a future refactor cannot change
  the spacing silently.
- Completions feed the certification evidence GRS-0023 gates on, closing the learning → certification
  loop, while the human-gated promotion keeps the anti-self-certification guarantee intact.
- **Accepted scope boundaries:** a shadow-assessment credit is still a bare admin-recorded counter
  (ADR-0013's note stands); the drill *content* (the question bank's real prompts/answers) and the
  coursework content are founder-track authoring tasks — the model, scheduler, gate, and evidence
  wiring are in place for them. A per-advisor streak leaderboard / "My Performance" aggregation
  (GRS-0028) reads these records but is out of scope here.
