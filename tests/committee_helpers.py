"""Test helpers for the Rating Committee workflow (GRS-0021, Methodology §8).

The triad rates above None for any scored assessment, so committee sign-off is a routine
precondition of finalisation. `approve_committee_queue` clears it: it seeds a committee member
(never the owner — peer challenge), reads the assessment's high-stakes queue, and approves every
item at its current rating. Callers of the shared finalise helpers need not thread a member through
— the helper supplies one, seeded against the app's engine (the conftest bootstrap pattern).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from bcap_contracts.committee import CommitteeDecision, CommitteeDecisionStatus
from bcap_contracts.common import AssessorLevel, ConsultantTier, Role

from grassmarket.atlas.committee import required_committee_items
from grassmarket.atlas.results import AtlasResult
from grassmarket.auth.security import create_access_token, hash_password
from grassmarket.data.repository import Principal, Repository
from tests.conftest import SeededConsultant, auth_header


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


def seed_committee_member(client, *, email: str | None = None) -> SeededConsultant:
    """Seed a consultant with the COMMITTEE_MEMBER role + bearer token against the app's engine."""
    factory = client.app.state.session_factory
    settings = client.app.state.settings
    email = email or f"committee-{uuid4().hex[:10]}@bruntsfieldcapital.com"
    session = factory()
    try:
        repo = Repository(session)
        stored = repo.create_consultant(
            email=email,
            full_name=email.split("@")[0].title(),
            hashed_password=hash_password("correct-horse-battery-staple"),
            role=Role.COMMITTEE_MEMBER,
            tier=ConsultantTier.CONSULTANT,
            assessor_level=AssessorLevel.CERTIFIED_LEAD,
        )
        session.commit()
    finally:
        session.close()
    token = create_access_token(
        settings,
        consultant_id=stored.id,
        email=stored.email,
        role=stored.role,
        tier=stored.tier,
        assessor_level=stored.assessor_level,
    )
    return SeededConsultant(
        stored=stored,
        principal=Principal(consultant_id=stored.id, role=stored.role),
        token=token,
    )


def committee_queue(client, aid: str, viewer: SeededConsultant) -> list[dict]:
    resp = client.get(f"/assessments/{aid}/committee", headers=auth_header(viewer))
    assert resp.status_code == 200, resp.text
    return resp.json()


def decide(
    client,
    aid: str,
    member: SeededConsultant,
    item: dict,
    *,
    status: str = "approved",
    rationale: str = "Reviewed against the moat-duration rubric; the rating holds.",
    dissent_note: str | None = None,
) -> dict:
    body = {
        "item_type": item["item_type"],
        "item_key": item["item_key"],
        "rating": item["rating"],
        "status": status,
        "rationale": rationale,
    }
    if dissent_note is not None:
        body["dissent_note"] = dissent_note
    resp = client.post(
        f"/assessments/{aid}/committee/decide", json=body, headers=auth_header(member)
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def approve_committee_queue(
    client, aid: str, owner: SeededConsultant, *, member: SeededConsultant | None = None
) -> SeededConsultant:
    """Approve every high-stakes item on an assessment (Methodology §8), so it can finalise. Reads
    the queue as the owner, approves each as a committee member (≠ owner). Returns the member."""
    reviewer = member or seed_committee_member(client)
    entries = committee_queue(client, aid, owner)
    for entry in entries:
        decide(client, aid, reviewer, entry["item"])
    return reviewer
