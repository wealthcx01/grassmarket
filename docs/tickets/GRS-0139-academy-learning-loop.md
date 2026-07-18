# GRS-0139 — Academy learning loop (comprehension gate + wired spaced repetition)

**Status:** In progress
**Loop:** Part 2 — critical review / trust hardening

## Why

The critical review found the Academy was **read-and-forget**: "Mark complete" was a click with no
comprehension check (you could 100% a course without reading), the `drill_topics` on each lesson
created no drill card, and `DrillCard` was a bare topic string (a blank flashcard). The reinforcement
apparatus existed but was unwired. This wires the loop.

## What was built

**Active-recall gate on completion.** A lesson is completed by *retrieval*, not a click: the reader
shows a "Check yourself" question, the advisor writes their recall attempt, reveals the model answer,
then marks complete. The mandatory **Sales Egoist** course carries an authored comprehension Q&A per
lesson (8); every other lesson derives a recall prompt from its `measurement`. (`Lesson` gains
`check_question` / `check_answer`.)

**Wired spaced repetition with real content.** Completing a lesson **auto-enrolls a real `DrillCard`**
for each of its `drill_topics` — carrying the recall **question** + model **answer** (from the
comprehension check, or the measurement) — so "Power drills due" populates after learning and each
drill is real retrieval: read the question, try to recall, reveal, self-grade (SM-2). Idempotent per
topic. (`DrillCard` gains `prompt` / `answer`; migration `0031` backfills legacy cards to empty.)

## Files
- Contracts: `Lesson.check_question/check_answer`, `DrillCard.prompt/answer` (schemas regenerated).
- `models.py` + migration `0031` (drill_cards prompt/answer).
- `repository.py`: `complete_lesson` auto-enrolls drills (idempotent), `create_drill_card` +
  `_lesson_drill_content` (authored check → measurement fallback), `_to_drill_card` carries content.
- `content/sales_egoist.py`: 8 authored comprehension Q&A.
- Reader `[slug]/page.tsx`: the active-recall gate. `LearningDrillsPanel.tsx`: drill = question →
  reveal answer → self-grade.
- Tests: `test_academy_drill_loop.py` (auto-enroll + idempotent + measurement fallback); reader vitest
  updated (recall gate).

## Flagged (still open, larger)
- The comprehension gate is a UX-level active-recall gate (self-assessed), not a server-enforced quiz
  pass — appropriate for a self-improvement tool. Auto-grading would need multiple-choice items.
- Deepen the doctrine course *bodies* (still one paragraph each); author checks for the product courses
  (they fall back to measurement today); tie the cert sign-off to a minimum drill/arena record.

## Acceptance
- Completing a lesson requires a recall attempt + reveal; it auto-enrolls a real Q&A drill per topic;
  the drills strip shows question → reveal answer → grade. Golden master untouched.
