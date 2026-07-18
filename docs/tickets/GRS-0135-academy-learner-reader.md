# GRS-0135 — Bruntsfield Academy: learner catalog + course reader

**Status:** In progress
**Loop:** Part 2 — Bruntsfield Academy / Workbench
**Depends on:** GRS-0121 (course CMS + published-catalog API), GRS-0122 (Sales Egoist), GRS-0123–0126 (product courses), GRS-0128 (workbench hub)

## The gap (found in the v1 UI/UX audit)

The CMS (GRS-0121) gave admins a way to **author** courses and the back-end exposes an
**org-wide** learner read (`GET /workbench/courses/published`, `GET /workbench/courses/{slug}/published`,
`POST /workbench/courses/{slug}/lessons/{lesson_id}/complete`). Five deep courses are published
(Sales Egoist, Benzinga, Brandfetch, OpenBB, Sales Ops). **But there is no learner-facing UI.** An
advisor who follows the Workbench "Continue the Academy" action or navigates to a course lands on the
admin editor at `/workbench/courses/{slug}`, which correctly refuses non-admins with "Course
authoring is admin-only." — a dead end. The entire course investment is unreachable by the people
meant to learn from it. The tickets already presume a "learner catalog" and "learner path" (0122/0128).

## What to build

**Back-end (small read to make progress persist):**
- `Repository.list_lesson_completions(principal, slug) -> list[LessonCompletion]` — the caller's own
  completions for a published course. Owner-scoped (a consultant sees only their own progress); the
  course itself is org-wide readable. 404 if the course was never published.
- `GET /workbench/courses/{slug}/completions` → `list[LessonCompletion]`. So the reader shows which
  lessons are already done (and never re-POSTs a completed lesson into a 409).

**Front-end (the learner surface):**
- `/workbench/academy` — the learner catalog: every published course, the mandatory-first one first
  with a "Start here" badge, its summary + certification-credit, linking to the reader.
- `/workbench/academy/[slug]` — the reader: renders the published `CourseTree` (modules → lessons),
  each lesson's prose body + its "how you measure you applied it" + the drill topics it reinforces,
  with a per-lesson **Mark complete** control (progress from the completions read) and a course
  progress bar. Completing every lesson of a coursework-credit course grants the credit (existing path).
- Entry points: the Workbench **Learning & Drills** tab surfaces the Academy catalog and links in;
  the bench **Academy** next-action links to the catalog.

## Not in scope
- No new markdown dependency — lesson bodies render as prose paragraphs (CSP-safe). No video player
  (video_ref is not populated). No change to the admin CMS, the certification path, or scoring.

## Acceptance
- A non-admin advisor can browse the catalog, open any published course, read every lesson, mark
  lessons complete, see progress persist across reload, and (for a coursework course) earn the credit.
- Owner-scoping: an advisor's completions are their own. Golden master untouched.
