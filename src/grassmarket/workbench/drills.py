"""The SM-2 spaced-repetition scheduler for Power Drills (GRS-0024, PRD §6).

A pure, deterministic implementation of the SuperMemo SM-2 algorithm — golden-mastered like the
calibration statistics, so the schedule a drill card produces is reproducible and never drifts. Each
review takes a recall-quality grade q ∈ 0..5; the card's easiness, repetition count and interval are
updated, and the next due date is `reviewed_at + interval days`.

Fail-loud: an out-of-range grade is refused, never clamped or defaulted around (CLAUDE.md #3).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

INITIAL_EASINESS = 2.5
MIN_EASINESS = 1.3
# A grade below this is a lapse: the card relearns from the start (SM-2).
PASSING_GRADE = 3
MAX_GRADE = 5


class DrillGradeError(ValueError):
    """A recall-quality grade outside 0..5 — refused, never scored around."""


@dataclass(frozen=True)
class DrillState:
    """A card's SM-2 memory state. `interval_days` is the gap until the next review; a fresh card is
    (0 repetitions, initial easiness, 0-day interval — due immediately)."""

    repetitions: int = 0
    easiness: float = INITIAL_EASINESS
    interval_days: int = 0


def review(state: DrillState, grade: int) -> DrillState:
    """Apply one SM-2 review at recall-quality `grade` (0..5) and return the new memory state.

    grade ≥ 3 is a pass (the interval grows: 1 day, then 6, then ×easiness); grade < 3 is a lapse
    (repetitions reset, interval back to 1 day). The easiness factor is updated on every review and
    floored at 1.3, exactly as SM-2 specifies."""
    if not 0 <= grade <= MAX_GRADE:
        raise DrillGradeError(f"A drill grade must be an integer 0..{MAX_GRADE} (got {grade!r}).")

    if grade < PASSING_GRADE:
        repetitions = 0
        interval = 1
    else:
        if state.repetitions == 0:
            interval = 1
        elif state.repetitions == 1:
            interval = 6
        else:
            interval = round(state.interval_days * state.easiness)
        repetitions = state.repetitions + 1

    easiness = state.easiness + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    easiness = max(MIN_EASINESS, easiness)
    return DrillState(repetitions=repetitions, easiness=easiness, interval_days=interval)


def next_due(reviewed_at: datetime, state: DrillState) -> datetime:
    """The next review date: the moment of review plus the card's interval (SM-2)."""
    return reviewed_at + timedelta(days=state.interval_days)
