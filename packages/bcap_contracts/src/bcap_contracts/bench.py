"""Bench-time queue + performance view (GRS-0026, PRD §6).

Two derived, self-scoped views over an advisor's own workbench state — never persisted, always
recomputed, so they can't drift from the records they summarise:

- `BenchQueue` — the prioritised "what to do next" an idle advisor lands on when no engagement is
  active: the next certification step, then due drills, then a practice-arena scenario, then an
  Opportunity Radar research task. Priority is explicit and deterministic (lower number first).
- `PerformanceSummary` — an advisor's own development picture (engagements, conversion, learning,
  drill streak, arena trend). Scoped to self; the cross-advisor/admin view is Holy Corner scope.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from bcap_contracts.common import AssessorLevel, Score


class BenchItemKind(StrEnum):
    """What a queue item points the advisor at — the bench sources, in priority order. GRS-0128
    folds the governance + Academy surfaces into the same hub (rating requests + committee reviews
    sit above certification because others are waiting on them; Academy sits with the ladder)."""

    RATING_REQUEST = "rating_request"
    COMMITTEE = "committee"
    CERTIFICATION = "certification"
    ACADEMY = "academy"
    DRILL = "drill"
    ARENA = "arena"
    RESEARCH = "research"


class BenchQueueItem(BaseModel):
    """One prioritised next action. `ref_id` links to the concrete record (learning module, drill
    card, arena scenario, prospect) where one applies; a pure-guidance item has none."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: BenchItemKind
    priority: int = Field(ge=1, description="1 is the single most important next action.")
    title: str = Field(min_length=1)
    detail: str = Field(min_length=1)
    action_hint: str = Field(min_length=1, description="complete / review / practise / research")
    ref_id: UUID | None = None


class BenchQueue(BaseModel):
    """The advisor's prioritised bench-time queue — recomputed on read, never stored."""

    model_config = ConfigDict(extra="forbid")

    owner_consultant_id: UUID
    generated_at: datetime
    items: tuple[BenchQueueItem, ...] = ()


class ArenaTrendPoint(BaseModel):
    """One scored practice-arena session on the advisor's completeness trend line."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scored_at: datetime
    completeness: Score


class PerformanceSummary(BaseModel):
    """An advisor's own development picture — self-scoped (no cross-advisor comparison here)."""

    model_config = ConfigDict(extra="forbid")

    owner_consultant_id: UUID
    level: AssessorLevel
    engagements_active: int = Field(ge=0)
    engagements_completed: int = Field(ge=0)
    prospects_total: int = Field(ge=0)
    pipeline_conversion_rate: Score = Field(
        description="Share of the advisor's prospects that reached contracted-or-beyond (0 if none)"
    )
    coursework_complete: bool
    exam_passed: bool
    drills_due: int = Field(ge=0)
    drill_best_streak: int = Field(ge=0)
    arena_sessions_scored: int = Field(ge=0)
    arena_best_completeness: Score | None = None
    arena_trend: tuple[ArenaTrendPoint, ...] = ()
