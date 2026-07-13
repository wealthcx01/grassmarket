"""The certification-ladder state machine (GRS-0023, Methodology §9).

Pure functions: what evidence each rung of the ladder requires, whether an advisor may advance one
rung, and whether a scored assessment carries a rating high-stakes enough to need a Certified Lead.
No silent defaults — a promotion with missing evidence returns the reasons, it never half-succeeds.
"""

from __future__ import annotations

from bcap_contracts.certification import (
    SHADOW_ASSESSMENTS_REQUIRED,
    CertificationRecord,
)
from bcap_contracts.common import AssessorLevel

from grassmarket.atlas.results import AtlasResult

# The ladder, weakest → strongest (Methodology §9). The order both defines "the next rung" and
# forbids skipping one.
_LADDER = (
    AssessorLevel.TRAINED,
    AssessorLevel.SHADOW,
    AssessorLevel.OBSERVED_LEAD,
    AssessorLevel.CERTIFIED_LEAD,
)
_RANK = {level: i for i, level in enumerate(_LADDER)}


def next_level(level: AssessorLevel) -> AssessorLevel | None:
    """The rung above `level`, or None if already at the top (Certified Lead)."""
    i = _RANK[level]
    return _LADDER[i + 1] if i + 1 < len(_LADDER) else None


def is_at_least(level: AssessorLevel, floor: AssessorLevel) -> bool:
    return _RANK[level] >= _RANK[floor]


def promotion_blockers(record: CertificationRecord, target: AssessorLevel) -> list[str]:
    """Why `record`'s advisor may NOT yet be promoted to `target`. Empty ⟹ the evidence is in.

    Promotion is one rung at a time (the current level must be exactly the one below `target`), and
    each rung requires its evidence to be recorded first (Methodology §9)."""
    blockers: list[str] = []
    current = record.level
    if _RANK.get(target) is None:
        return [f"{target} is not a ladder level."]
    if _RANK[target] != _RANK[current] + 1:
        return [
            f"Promotion is one rung at a time: cannot go from {current.value} to {target.value}."
        ]

    if target is AssessorLevel.SHADOW:
        # To leave Trained: the Trained credentials (coursework + passed exam) AND two shadows (§9).
        if not record.coursework_complete:
            blockers.append("Coursework is not complete.")
        if not record.exam_passed:
            blockers.append("The rubric exam has not been passed.")
        if record.shadow_count < SHADOW_ASSESSMENTS_REQUIRED:
            blockers.append(
                f"{record.shadow_count}/{SHADOW_ASSESSMENTS_REQUIRED} shadow assessments logged."
            )
    elif target is AssessorLevel.OBSERVED_LEAD:
        if not record.observed_lead_logged:
            blockers.append("No observed lead recorded (must lead one assessment under review).")
    elif target is AssessorLevel.CERTIFIED_LEAD:
        if record.observed_lead_signoff_by is None:
            blockers.append("No sign-off recorded from a Certified Lead.")

    return blockers


def requires_certified_lead(result: AtlasResult) -> list[str]:
    """The ratings in a scored assessment that require a Certified Lead to lead it (Methodology §9):
    a module whose gate is Frontier, or a power rated Wide. Empty ⟹ no floor applies."""
    reasons: list[str] = []
    reasons.extend(
        f"module {m.key} is rated Frontier" for m in result.modules if m.gate_band == "Frontier"
    )
    reasons.extend(
        f"power {p.key} is rated Wide" for p in result.powers.powers if p.strength == "Wide"
    )
    return reasons
