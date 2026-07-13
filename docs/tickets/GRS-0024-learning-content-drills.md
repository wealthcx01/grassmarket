# GRS-0024 — Learning content + Power Drills

- **Loop:** 5
- **Branch:** `grs-0024-learning-content-drills`
- **Status:** Planned
- **Normative source:** PRD §6 (Workbench); CLAUDE.md #8.
- **Depends on:** GRS-0023 (progress-tracking hooks).

## Goal

The Workbench's teaching half: structured content plus spaced-repetition drills.

## Scope

1. Content model: playbook modules, sales journeys (old school / new school), technical primers, exam quizzes — with per-advisor completion tracking feeding certification evidence.
2. Power Drills: spaced-repetition micro-quizzes (SM-2 or equivalent) over the 7 Powers, the triad, the 9 modules, and rubric anchors; scheduled per advisor; streaks tracked.
3. Weekly quiz generator from Briefing content: AI-generated draft, approval-gated before publication (non-negotiable #8 — never auto-publishes).
4. Question bank versioned; answers link back to the rubric/methodology section they teach.

## Exit criteria

- Drill scheduling round-trips: due → answered → rescheduled per algorithm (deterministic test with fixed clock).
- Generated quiz lands in an approval queue; unapproved content is unreachable by advisors.
- Completions feed GRS-0023 certification evidence.
- Full gate green; CI green.
