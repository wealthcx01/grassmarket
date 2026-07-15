"""Which scored ratings need Rating Committee sign-off, and whether they have it (Methodology §8).

Pure functions over an `AtlasResult`: `required_committee_items` derives the high-stakes set (power
Established+, triad above None, module gate Frontier); `committee_blockers` reports which of those
still lack a matching APPROVED decision. Score-points never enter here — this is an ordinal, rule-
based gate on the headline words, exactly like the module rating gate (ADR-0002)."""

from __future__ import annotations

from collections.abc import Sequence

from bcap_contracts.committee import (
    CommitteeDecision,
    CommitteeDecisionStatus,
    CommitteeItem,
    CommitteeItemType,
)

from grassmarket.atlas.results import AtlasResult

# Strength ordering for the "Established or above" test. StrengthRating carries no rank (unlike
# MaturityLevel), so the ordering is stated here, weakest→strongest (Methodology §8).
_STRENGTH_RANK = {"None": 0, "Emerging": 1, "Established": 2, "Wide": 3}
_ESTABLISHED_RANK = _STRENGTH_RANK["Established"]

_FRONTIER_BAND = "Frontier"

_TRIAD_LABELS = {
    "economic_value": "Economic Value",
    "perceived_value": "Perceived Value",
    "defence_value": "Defence Value",
}


def required_committee_items(result: AtlasResult) -> tuple[CommitteeItem, ...]:
    """The high-stakes ratings in this result that require committee sign-off (Methodology §8):
    any power Established+, any triad dimension above None, any module whose gate band is Frontier.
    """
    items: list[CommitteeItem] = []

    for power in result.powers.powers:
        # Index directly — an unrecognised strength must fail loud, never silently rank 0 and
        # escape the gate (CLAUDE.md #3; the triad and module branches also index directly).
        if _STRENGTH_RANK[power.strength] >= _ESTABLISHED_RANK:
            items.append(
                CommitteeItem(
                    item_type=CommitteeItemType.POWER,
                    item_key=power.key,
                    rating=power.strength,
                    label=power.key,
                    reason="Power rated Established or above.",
                )
            )

    for attr, label in _TRIAD_LABELS.items():
        dimension = getattr(result.triad, attr)
        # A Not-Assessed dimension (rating is None) is not a high-stakes rating — only a rating
        # strictly above the "None" moat floor needs committee sign-off.
        if dimension.rating is not None and dimension.rating != "None":
            items.append(
                CommitteeItem(
                    item_type=CommitteeItemType.TRIAD,
                    item_key=attr,
                    rating=dimension.rating,
                    label=label,
                    reason="Triad rating above None.",
                )
            )

    for module in result.modules:
        if module.gate_band == _FRONTIER_BAND:
            items.append(
                CommitteeItem(
                    item_type=CommitteeItemType.MODULE,
                    item_key=module.key,
                    rating=module.gate_band,
                    label=module.name,
                    reason="Module rating gate is Frontier.",
                )
            )

    return tuple(items)


def _approved_index(
    decisions: Sequence[CommitteeDecision],
) -> dict[tuple[CommitteeItemType, str, str], CommitteeDecision]:
    """Map (item_type, item_key, rating) → the APPROVED decision for it. A decision only counts for
    the exact rating it reviewed, so re-rating a high-stakes item re-opens the gate."""
    return {
        (d.item_type, d.item_key, d.rating): d
        for d in decisions
        if d.status is CommitteeDecisionStatus.APPROVED
    }


def committee_blockers(
    required: Sequence[CommitteeItem], decisions: Sequence[CommitteeDecision]
) -> list[str]:
    """What still blocks sign-off: every required item without a matching APPROVED decision
    (pending, rejected, or approved at a since-changed rating). Empty ⟹ the gate clears."""
    approved = _approved_index(decisions)
    blockers: list[str] = []
    for item in required:
        if (item.item_type, item.item_key, item.rating) not in approved:
            blockers.append(
                f"{item.item_type.value} '{item.label}' ({item.rating}) awaits Rating Committee "
                f"sign-off — {item.reason}"
            )
    return blockers
