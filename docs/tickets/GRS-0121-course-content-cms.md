# GRS-0121 — Course/content model + back-end catalog CMS (foundation)

**Status:** Planned
**Loop:** Part 2 — Bruntsfield Academy / Workbench (one program)
**Depends on:** ADR-0028 (Bruntsfield Academy / Workbench)

## Why

The Academy program needs somewhere to store teaching material, and today there is none. **Confirmed
greenfield:** `LearningModule` (`bcap_contracts/learning.py:84`) is a *titled pointer* —
`kind`/`title`/`methodology_ref`/`certification_credit`, with **no body, lesson, page, video, ordering,
or prerequisite**; the teaching material isn't stored at all. Every downstream Academy ticket (Sales
Egoist core, the three product courses, the ops playbook) has nowhere to live until this exists. The
founder also wants the catalog **replaceable/updatable without a deploy**, so authoring must be
back-end, not hardcoded content.

## What to build

- A versioned **Course → Module → Lesson → Drill/Assessment** content model in
  `packages/bcap_contracts/` (extending, not replacing, `LearningModule` at `learning.py:84` — lessons,
  pages, video refs, ordering, prerequisites become first-class), served through the `workbench/`
  service and `web/routers/workbench.py`, with an **admin-authoring UI** so the catalog is edited
  in-app.
- **Reuse the plumbing that already exists** — completion → coursework credit → certification evidence
  (`LearningModule.certification_credit`, `POST /workbench/learning/modules/{id}/complete`). Do not
  rebuild the credit path; extend it to the new lesson granularity.
- **Reuse the approval-gate pattern** already used for AI-drafted quizzes (`GeneratedQuiz`/`QuizStatus`,
  `POST /workbench/quizzes/{id}/approve`) — apply the same gate to AI-authored **lesson** drafts so
  AI-authored content stays approval-gated per ADR-0009.

## Acceptance / verification

- A course with nested modules/lessons/drills can be authored and re-published through the admin UI
  **without a redeploy**, and versions are retained.
- Completing a lesson still credits coursework toward certification via the existing
  `.../complete` path (no regression to `certification_credit`).
- An AI-authored lesson draft is blocked from publication until approved through the reused
  quiz-style gate (ADR-0009).

## Not in scope

- The actual course content — Sales Egoist (GRS-0122), the product courses (GRS-0124–0126), the ops
  playbook (GRS-0129) are authored *through* this CMS in their own tickets.
- Learner-facing catalog browsing polish beyond what the hub (GRS-0128) surfaces.
