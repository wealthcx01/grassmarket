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


def evidence_blockers(record: CertificationRecord, target: AssessorLevel) -> list[str]:
    """The evidence `target` requires that this record does not have. Empty ⟹ the rung is earned.

    Deliberately ignores the advisor's *current* level: this answers "does the evidence support this
    rung", which is a different question from "may they be promoted to it now". `promotion_blockers`
    adds the one-rung-at-a-time rule on top; `earned_level` walks the ladder with it. One
    implementation of each rung's requirements, so the gate and the display cannot drift apart
    (GRS-0242 scope 3).
    """
    blockers: list[str] = []
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


def earned_level(record: CertificationRecord) -> AssessorLevel:
    """The highest rung this advisor's **evidence** supports, ignoring the level they are marked at.

    The ladder is cumulative, so this walks up from Trained and stops at the first rung whose
    evidence is missing. Trained is the floor: it is the rung an advisor starts on and needs no
    evidence to hold.

    This exists because a level and its evidence are stored in two different places. The level lives
    on the consultant record (and the JWT), where an invite, a seed or an admin can set it
    directly; the evidence lives on the certification record and is only written by the ladder.
    Nothing reconciled them, so the Workbench could show "Certified Lead" beside a ladder with
    no coursework, no exam and no shadow assessments — both true, contradicting each other on
    one screen (GRS-0242).
    """
    earned = AssessorLevel.TRAINED
    for rung in _LADDER[1:]:
        if evidence_blockers(record, rung):
            break
        earned = rung
    return earned


def level_is_evidenced(record: CertificationRecord) -> bool:
    """Whether the advisor's marked level is one their evidence actually supports.

    False means the level was set outside the ladder. That is not necessarily wrong — an
    administrator may legitimately grant one — but it must never render as though it were earned.
    """
    return _RANK[record.level] <= _RANK[earned_level(record)]


def promotion_blockers(record: CertificationRecord, target: AssessorLevel) -> list[str]:
    """Why `record`'s advisor may NOT yet be promoted to `target`. Empty ⟹ the evidence is in.

    Promotion is one rung at a time (the current level must be exactly the one below `target`), and
    each rung requires its evidence to be recorded first (Methodology §9)."""
    current = record.level
    if _RANK.get(target) is None:
        return [f"{target} is not a ladder level."]
    if _RANK[target] != _RANK[current] + 1:
        return [
            f"Promotion is one rung at a time: cannot go from {current.value} to {target.value}."
        ]
    return evidence_blockers(record, target)


def requires_certified_lead(result: AtlasResult) -> list[str]:
    """The ratings in a scored assessment that require a Certified Lead to lead it (Methodology §9):
    a module whose gate is Frontier, or a power rated Wide. Empty ⟹ no floor applies.

    Relationship to the committee trigger (`atlas/committee.py:required_committee_items`, GRS-0131):
    the two gates are deliberately nested, not in conflict. Committee review fires on the BROADER
    set — any power Established+ (rank ≥ 2), any triad above None, any module Frontier — while
    the Certified-Lead floor is the STRICTER subset: module Frontier (⊆ committee's module branch)
    and power Wide (rank 3 ≥ Established, so ⊆ committee's power branch). Therefore anything that
    needs a Certified Lead also needs committee review, but committee also catches lesser-stakes
    ratings the lead-floor lets pass. `test_certification` pins this subset invariant."""
    reasons: list[str] = []
    reasons.extend(
        f"module {m.key} is rated Frontier" for m in result.modules if m.gate_band == "Frontier"
    )
    reasons.extend(
        f"power {p.key} is rated Wide" for p in result.powers.powers if p.strength == "Wide"
    )
    return reasons
