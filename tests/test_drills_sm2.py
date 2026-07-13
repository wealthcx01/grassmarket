"""Golden-master + property tests for the SM-2 drill scheduler (GRS-0024, PRD §6).

The sequence below is hand-computed (worked out in the comments) so the scheduler is pinned to an
independently-derived answer, not to itself — the same discipline as the ATLAS/calibration golden
masters. Easiness update per review: EF' = EF + (0.1 − (5−q)(0.08 + (5−q)·0.02)), floored at 1.3.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

import pytest

from grassmarket.workbench.drills import (
    INITIAL_EASINESS,
    DrillGradeError,
    DrillState,
    next_due,
    review,
)


def test_sm2_golden_sequence() -> None:
    s = DrillState()  # (0 reps, EF 2.5, 0-day interval) — a fresh card

    # q=5: reps 0 → interval 1, reps→1; EF = 2.5 + (0.1 − 0) = 2.6
    s = review(s, 5)
    assert (s.repetitions, s.interval_days) == (1, 1)
    assert math.isclose(s.easiness, 2.6, abs_tol=1e-9)

    # q=4: reps 1 → interval 6, reps→2; EF = 2.6 + (0.1 − 1·(0.08 + 0.02)) = 2.6 + 0 = 2.6
    s = review(s, 4)
    assert (s.repetitions, s.interval_days) == (2, 6)
    assert math.isclose(s.easiness, 2.6, abs_tol=1e-9)

    # q=3: reps 2 → interval round(6·2.6)=round(15.6)=16, reps→3;
    #      EF = 2.6 + (0.1 − 2·(0.08 + 2·0.02)) = 2.6 + (0.1 − 0.24) = 2.46
    s = review(s, 3)
    assert s.repetitions == 3 and s.interval_days == 16
    assert math.isclose(s.easiness, 2.46, abs_tol=1e-9)

    # q=1 (lapse): reps→0, interval→1;
    #      EF = 2.46 + (0.1 − 4·(0.08 + 4·0.02)) = 2.46 + (0.1 − 0.64) = 1.92
    s = review(s, 1)
    assert s.repetitions == 0 and s.interval_days == 1
    assert math.isclose(s.easiness, 1.92, abs_tol=1e-9)


def test_next_due_adds_the_interval() -> None:
    reviewed = datetime(2026, 7, 13, 9, 0, tzinfo=UTC)
    state = DrillState(repetitions=2, easiness=2.5, interval_days=6)
    assert next_due(reviewed, state) == datetime(2026, 7, 19, 9, 0, tzinfo=UTC)


def test_easiness_is_floored_at_1_3() -> None:
    # Repeated poor grades cannot drive the easiness below the SM-2 floor.
    s = DrillState()
    for _ in range(10):
        s = review(s, 0)
    assert s.easiness == 1.3


def test_a_lapse_resets_repetitions_and_interval() -> None:
    s = DrillState(repetitions=5, easiness=2.4, interval_days=40)
    s = review(s, 2)  # below the passing grade
    assert s.repetitions == 0
    assert s.interval_days == 1


def test_a_high_grade_grows_the_interval() -> None:
    s = DrillState(repetitions=3, easiness=2.5, interval_days=10)
    grown = review(s, 5)
    assert grown.interval_days == round(10 * 2.5)  # 25
    assert grown.repetitions == 4


@pytest.mark.parametrize("bad", [-1, 6, 7, 100])
def test_out_of_range_grade_is_refused(bad: int) -> None:
    with pytest.raises(DrillGradeError):
        review(DrillState(), bad)


def test_initial_easiness_constant() -> None:
    assert DrillState().easiness == INITIAL_EASINESS == 2.5
