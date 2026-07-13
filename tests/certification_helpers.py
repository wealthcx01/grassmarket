"""Test helpers for the certification ladder (GRS-0023).

Seeds consultants at a chosen `AssessorLevel` (the finalise cert-gate reads the assessment owner's
level), and assembles a Frontier-bearing assessment that has already cleared the §9 consensus and §8
committee gates — so the only thing standing between it and finalisation is the certification floor.
"""

from __future__ import annotations

from uuid import uuid4

from bcap_contracts.common import AssessorLevel, ConsultantTier, MaturityLevel, Role
from bcap_contracts.registry import load_registry

from grassmarket.auth.security import create_access_token, hash_password
from grassmarket.data.repository import Principal, Repository
from tests.committee_helpers import approve_committee_queue
from tests.conftest import SeededConsultant, auth_header
from tests.dual_rating_helpers import reach_consensus

_REGISTRY = load_registry()
_MODULE = "APP_SERVER"
_APP_SERVER_SUBS = tuple(s.key for s in _REGISTRY.require_module(_MODULE).subcomponents)


def seed_consultant_at_level(
    client, level: AssessorLevel, *, email: str | None = None
) -> SeededConsultant:
    """Seed a consultant at a chosen certification level + token against the app's engine."""
    factory = client.app.state.session_factory
    settings = client.app.state.settings
    email = email or f"advisor-{uuid4().hex[:10]}@bruntsfieldcapital.com"
    session = factory()
    try:
        repo = Repository(session)
        stored = repo.create_consultant(
            email=email,
            full_name=email.split("@")[0].title(),
            hashed_password=hash_password("correct-horse-battery-staple"),
            role=Role.CONSULTANT,
            tier=ConsultantTier.CONSULTANT,
            assessor_level=level,
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


def _frontier_document() -> dict:
    """A scoreable document whose APP_SERVER module rates Frontier (every subcomponent Frontier)."""
    e3 = "E3"
    return {
        "subject": "Frontier case",
        "subcomponents": [
            {
                "module_key": _MODULE,
                "subcomponent_key": s,
                "level": "Frontier",
                "evidence_grade": e3,
            }
            for s in _APP_SERVER_SUBS
        ],
        "metrics": [{"metric_key": "AUA", "raw": 1_000_000_000, "confidence": "audited"}],
        "powers": [
            {
                "power_key": p.key,
                "benefit": "Emerging",
                "barrier": "Emerging",
                "benefit_grade": e3,
                "barrier_grade": e3,
            }
            for p in _REGISTRY.powers
        ],
    }


def frontier_assessment_ready_to_finalise(client, owner: SeededConsultant) -> str:
    """A Frontier-bearing assessment owned by `owner`, already through dual-rating consensus and
    Rating Committee sign-off (§8) — ready to finalise but for the certification floor (§9)."""
    aid = client.post("/assessments", json={}, headers=auth_header(owner)).json()["id"]
    client.put(f"/assessments/{aid}", json=_frontier_document(), headers=auth_header(owner))
    reach_consensus(
        client, aid, owner, _MODULE, [(s, MaturityLevel.FRONTIER) for s in _APP_SERVER_SUBS]
    )
    approve_committee_queue(client, aid, owner)
    return aid
