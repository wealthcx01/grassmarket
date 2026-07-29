"""Committee fixtures that survive ADR-0041.

The Rating Committee routes are retired (GRS-0188), but `assert_committee_approved` and the
high-stakes item derivation stay in the codebase, dormant and still unit tested, so the decision is
reversible. This builds the approved-decision tuple those pure-layer tests need.

The HTTP helpers that used to live here (`seed_committee_member`, `committee_queue`, `decide`,
`approve_committee_queue`) went with the routes they drove. See
`tests/test_retired_governance_routes.py`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from bcap_contracts.committee import CommitteeDecision, CommitteeDecisionStatus

from grassmarket.atlas.committee import required_committee_items
from grassmarket.atlas.results import AtlasResult


def approved_decisions_for(result: AtlasResult) -> tuple[CommitteeDecision, ...]:
    """Build an APPROVED committee decision for every high-stakes item in a result — the
    service-level fixture for rendering a client pack that has cleared committee sign-off (§8)."""
    now = datetime.now(UTC)
    return tuple(
        CommitteeDecision(
            id=uuid4(),
            owner_consultant_id=uuid4(),
            created_at=now,
            updated_at=now,
            assessment_id=uuid4(),
            item_type=item.item_type,
            item_key=item.item_key,
            rating=item.rating,
            status=CommitteeDecisionStatus.APPROVED,
            rationale="Peer-reviewed against the moat-duration rubric; the rating holds.",
            decided_by_consultant_id=uuid4(),
            decided_at=now,
        )
        for item in required_committee_items(result)
    )
