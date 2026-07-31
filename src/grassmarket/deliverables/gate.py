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
from bcap_contracts.uncertainty import UncertaintyModel

from grassmarket.atlas.committee import committee_blockers, required_committee_items
from grassmarket.atlas.results import AtlasResult


class ClientUsabilityError(Exception):
    """A client-facing document was requested against a coefficient set that is not client-usable.
    A runtime refusal — the fail-safe that keeps a draft-weighted pack away from a client."""


class UncertaintyNotClientUsableError(Exception):
    """A client-facing pack was requested against an uncertainty model that is not client-usable.
    The §7 twin of ``ClientUsabilityError``: a client pack's P10/P50/P90 ranges, tornado, and
    weight-stability interval must be drawn from elicited widths, never draft placeholders (#3).
    Defence-in-depth — the gate refuses independently of which artifact the seam serves."""


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


class ReportApprovalPendingError(Exception):
    """A client report was about to reach a client without the founder having signed off its PROSE.

    Distinct from `FounderApprovalPendingError`, which guards the assessment document. GRS-0245
    measured why both are needed: the founder approves a scored document, the advisor then writes
    the words a client actually reads, and nothing bound the second to the first. The gate is on the
    CONTENT rather than on its authorship, so AI-drafted sections (GRS-0222) flow through it
    unchanged when they arrive.
    """


def assert_report_founder_approved(
    approval: object | None,
    *,
    non_production: bool,
    changed_sections: tuple[str, ...] = (),
    ever_approved: bool = False,
) -> None:
    """Refuse to release a client report whose prose the founder has not signed off.

    `non_production` records (demo/sandbox) are exempt and stay exempt: they self-approve under
    ADR-0029 and carry the GRS-0229 watermark on every rendition, which IS their gate. Putting them
    through founder review would spend the founder's attention on work that is not going anywhere.

    The refusal teaches (GRS-0245 scope 3). An advisor who is stopped is told which of the three
    states they are in — never submitted, submitted and waiting, or approved and then edited — and
    what to do next, because "403" tells them nothing and a queue they cannot see is
    indistinguishable from a broken button.
    """
    if non_production or approval is not None:
        return
    if ever_approved:
        edited = ", ".join(changed_sections) if changed_sections else "the report"
        raise ReportApprovalPendingError(
            f"This report was approved and then edited ({edited}), so the approval no longer "
            f"covers it. Send it back to the founder for review — they will see exactly which "
            f"sections changed."
        )
    raise ReportApprovalPendingError(
        "The founder signs off every report before it reaches a client (ADR-0041), and this one "
        "has not been signed off yet. Send it for review from the report editor; it joins the "
        "founder's queue and you will be able to issue the link as soon as it is approved."
    )


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


class FounderApprovalPendingError(Exception):
    """A client-facing pack was requested for a document the founder has not signed off at its
    current version (ADR-0041). Defence in depth: finalisation already gates on this, and the
    client-pack layer refuses independently too, because a pack is what reaches a client."""


def assert_founder_approved(approval: object | None, *, client_facing: bool) -> None:
    """Refuse a client-facing pack without a current founder approval (ADR-0041, GRS-0188).

    `approval` is `Repository.current_founder_approval(...)`, which returns None both when nothing
    was ever approved and when the document has changed since it was. Those two cases are the same
    refusal on purpose: what matters is whether the version about to reach a client is the version
    the founder read.

    Watermarked internal drafts are allowed through, exactly as they were under the committee gate
    this replaces — they are not client-facing and say so on every page.
    """
    if not client_facing:
        return
    if approval is None:
        raise FounderApprovalPendingError(
            "Refusing a client-facing pack: the founder has not approved this version of the "
            "document (ADR-0041). Submit it for review, or re-submit if it changed after approval."
        )


def assert_senior_approval(*, author_tier: ConsultantTier, approver_tier: ConsultantTier) -> None:
    """The quality-review gate (PRD §5): a narrative authored under a junior tier requires a
    senior (Consultant-tier) approver. A Consultant-tier author may self-approve."""
    if _TIER_RANK[author_tier] < _SENIOR_RANK and _TIER_RANK[approver_tier] < _SENIOR_RANK:
        raise SeniorApprovalError(
            f"A narrative authored under tier '{author_tier.value}' requires senior "
            f"(Consultant-tier) approval; approver tier '{approver_tier.value}' is not senior."
        )


def assert_uncertainty_client_usable(model: UncertaintyModel, *, client_facing: bool) -> None:
    """Refuse a client-facing pack whose §7 uncertainty model is not client-usable. The ranges,
    tornado, and stability interval a client pack renders come from these widths; draft placeholder
    widths must never price a client document (#3). Watermarked internal drafts are allowed."""
    if not client_facing:
        return
    if not model.client_usable:
        raise UncertaintyNotClientUsableError(
            "This assessment's uncertainty ranges are still provisional (drawn from draft "
            "placeholder widths, pending expert elicitation), so a client-facing deliverable can't "
            "be produced yet. Generate the internal, watermarked draft instead."
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
                "This assessment's scores are still in draft (weights pending expert elicitation), "
                "so a client-facing deliverable can't be produced yet. Generate the internal, "
                "watermarked draft instead."
            )
        return DeliverableMode.CLIENT
    return DeliverableMode.DRAFT_INTERNAL
