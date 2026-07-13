"""The client-usable gate (GRS-0015) — the controlling non-negotiable of Loop 4.

A client-facing pack may **not** be generated from a CoefficientSet with ``client_usable=False``.
That is a runtime refusal, not a convention: until the elicited v1 set (``client_usable=True``,
founder task) lands, the builder may only emit clearly-watermarked "DRAFT — not client-usable"
internal documents. Never silently produce a client pack on draft coefficients.
"""

from __future__ import annotations

from collections.abc import Iterable

from bcap_contracts.assessments import CoefficientSet
from bcap_contracts.committee import CommitteeDecision
from bcap_contracts.common import ConsultantTier
from bcap_contracts.deliverables import DeliverableMode
from bcap_contracts.narratives import AINarrative, NarrativeStatus

from grassmarket.atlas.committee import committee_blockers, required_committee_items
from grassmarket.atlas.results import AtlasResult


class ClientUsabilityError(Exception):
    """A client-facing document was requested against a coefficient set that is not client-usable.
    A runtime refusal — the fail-safe that keeps a draft-weighted pack away from a client."""


class CommitteePendingError(Exception):
    """A client-facing pack was requested while a high-stakes rating (power Established+, triad
    above None, module Frontier) still lacks Rating Committee sign-off (§8). Defence-in-depth:
    finalisation already gates on this, but the client-pack layer refuses independently too."""


class UnapprovedNarrativeError(Exception):
    """A client-facing pack was requested while it still contains an AI narrative that is not
    APPROVED. The GRS-0017 gate extension: AI content never reaches a client unsigned (#8)."""


class SeniorApprovalError(Exception):
    """A narrative authored under a junior tier (Venture Associate / Advisor) was approved without
    senior (Consultant-tier) sign-off — the PRD §5 quality-review gate refuses it."""


DRAFT_WATERMARK = "DRAFT — not client-usable"

# Seniority ordering (ADR-0009). VA and Advisor authors need a Consultant-tier approver; a
# Consultant may self-approve. Revisit here if the PRD later splits "early-tier" Advisors out.
_TIER_RANK = {
    ConsultantTier.VENTURE_ASSOCIATE: 0,
    ConsultantTier.ADVISOR: 1,
    ConsultantTier.CONSULTANT: 2,
}
_SENIOR_RANK = _TIER_RANK[ConsultantTier.CONSULTANT]


def assert_narratives_approved(narratives: Iterable[AINarrative], *, client_facing: bool) -> None:
    """Refuse a client-facing pack that still carries any not-APPROVED AI narrative. Watermarked
    internal documents are allowed (each draft is labelled AI-DRAFTED at render time)."""
    if not client_facing:
        return
    unapproved = [n for n in narratives if n.status is not NarrativeStatus.APPROVED]
    if unapproved:
        sections = ", ".join(sorted(n.section.value for n in unapproved))
        raise UnapprovedNarrativeError(
            f"Refusing a client-facing pack: {len(unapproved)} AI narrative section(s) not "
            f"approved ({sections}). Every AI-drafted section needs consultant sign-off first (#8)."
        )


def assert_committee_approved(
    result: AtlasResult, decisions: Iterable[CommitteeDecision], *, client_facing: bool
) -> None:
    """Refuse a client-facing pack while any high-stakes rating in `result` lacks a matching
    APPROVED committee decision (§8). Watermarked internal drafts are allowed (they carry the
    pending status in the appendix)."""
    if not client_facing:
        return
    blockers = committee_blockers(required_committee_items(result), list(decisions))
    if blockers:
        raise CommitteePendingError("Refusing a client-facing pack: " + " ".join(blockers))


def assert_senior_approval(*, author_tier: ConsultantTier, approver_tier: ConsultantTier) -> None:
    """The quality-review gate (PRD §5): a narrative authored under a junior tier requires a
    senior (Consultant-tier) approver. A Consultant-tier author may self-approve."""
    if _TIER_RANK[author_tier] < _SENIOR_RANK and _TIER_RANK[approver_tier] < _SENIOR_RANK:
        raise SeniorApprovalError(
            f"A narrative authored under tier '{author_tier.value}' requires senior "
            f"(Consultant-tier) approval; approver tier '{approver_tier.value}' is not senior."
        )


def resolve_mode(coefficients: CoefficientSet, *, client_facing: bool) -> DeliverableMode:
    """Decide the document mode, enforcing the gate.

    - ``client_facing=True`` on a client-usable set → CLIENT.
    - ``client_facing=True`` on a NON-client-usable set → **refusal** (``ClientUsabilityError``).
    - ``client_facing=False`` → DRAFT_INTERNAL (allowed on any set; always watermarked).
    """
    if client_facing:
        if not coefficients.client_usable:
            raise ClientUsabilityError(
                f"Refusing to generate a client-facing deliverable from coefficient set "
                f"'{coefficients.version}' (client_usable=False). Only a client-usable "
                f"(elicited/ratified) set may price a client pack; draft sets may emit "
                f"'{DRAFT_WATERMARK}' internal documents only."
            )
        return DeliverableMode.CLIENT
    return DeliverableMode.DRAFT_INTERNAL
