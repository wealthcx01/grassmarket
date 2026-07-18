# GRS-0138 — Academy learning legibility (dead-ends + honest labels)

**Status:** In progress
**Loop:** Part 2 — critical review / trust hardening

## Why (outside-in critical review)

The Academy's product-course content is genuinely good, but the learner surface around it had
read-and-forget friction and one false affordance:

- **Completion dead-ends.** After reading every lesson, the reader showed a single line and nothing
  to do next — no route to reinforce or continue. Reading is step one; the learner was left there.
- **A false "reinforced by drills" promise.** Each lesson listed its `drill_topics` under "Reinforced
  by drills:", but completing a lesson creates no drill card — the label promised automatic
  reinforcement that does not happen. It is honest to call these the lesson's *practice topics*.

## What changed (bounded)

- The course-complete state is now an actionable "what next" card: rehearse it in the Practice Arena,
  or pick the next course — so learning leads somewhere. The coursework-credit line only shows when the
  course actually carries that credit.
- "Reinforced by drills:" → **"Practice topics:"** — honest about what those tags are (the topics this
  lesson maps to for the Practice Arena), not a promise of automatic drilling.

## Flagged for the founder (the bigger learning-loop builds, from the review)

These convert the Academy from read-and-forget into real learning, but each is a substantial build:
1. **Gate completion behind a comprehension check.** Today "Mark complete" is a click with no test —
   an advisor can 100% a course without reading. Wire the existing `quiz.py` drafter into an
   end-of-module quiz that must pass before completion registers.
2. **Wire the spaced-repetition loop.** Completing a lesson should auto-enroll `DrillCard`s for its
   `drill_topics`, and `DrillCard` needs a `prompt`/`answer` (today it is a bare topic string), so the
   drill is real retrieval practice, not a blank flashcard.
3. **Deepen the mandatory doctrine courses** (Sales Egoist / Sales Ops) with worked examples, sample
   dialogue, and one worked objection each — today they are one abstract paragraph per lesson.
4. **Tie the credential to demonstrated skill** — require a passing quiz score / minimum Practice-Arena
   completeness the signer can see before the course-cert sign-off clears.

## Acceptance
- Course completion offers a next action (Practice Arena / next course), no dead-end. No label promises
  reinforcement that doesn't happen. Golden master untouched.
