"""The Revolut worked example (GRS-0117, ADR-0029).

A neobank/wealth showcase seeded as a DEMO record so a solo tester can reach the platform's payoff —
prospect → finalised assessment → the REAL AI-generated deliverables — without a co-rater or
committee. The DEMO provenance makes the finalise endpoint self-approve (never weakening the
production gate, which is untouched), permanently watermarks every surface, and keeps the record out
of the benchmark population. All figures here are ILLUSTRATIVE ONLY — no real Revolut client data.

The document reads like a strong challenger neobank: real network / scale / switching / brand power,
thin cornered-resource / process power, and a spread of infrastructure maturity so the heat map and
report have genuine content. Client-facing deliverables are gated off product-wide until the
coefficient panel ratifies (ADR-0022), so the demo generates the watermarked internal drafts a
tester can actually see today.
"""

from __future__ import annotations

from datetime import UTC, datetime

from bcap_contracts.assessments import (
    AssessmentDocument,
    MetricEntry,
    PowerEntry,
    RecordProvenance,
    SubcomponentRating,
)
from bcap_contracts.common import (
    EvidenceGrade,
    MaturityLevel,
    MetricConfidence,
    Role,
    StrengthRating,
)
from bcap_contracts.deliverables import DeliverableType
from bcap_contracts.entities import PipelineStage

REVOLUT_SUBJECT = "Revolut (DEMO)"
_E3 = EvidenceGrade.E3_ARTIFACT

# The five single-run diagnostic documents the generate endpoint supports (roadmap + score-evolution
# have their own paths and are refused there). The demo runs the real generator for each.
_DEMO_DELIVERABLES: tuple[DeliverableType, ...] = (
    DeliverableType.PLATFORM_POWER_REPORT,
    DeliverableType.EXECUTIVE_SUMMARY,
    DeliverableType.INFRASTRUCTURE_HEATMAP,
    DeliverableType.TECHNICAL_APPENDIX,
    DeliverableType.WORKSHOP_OUTPUT,
)

# (power, benefit, barrier) — a challenger neobank's moat: strong network/scale/switching/brand,
# thin cornered-resource/process. Illustrative only.
_POWERS: tuple[tuple[str, StrengthRating, StrengthRating], ...] = (
    ("NETWORK_ECONOMIES", StrengthRating.ESTABLISHED, StrengthRating.ESTABLISHED),
    ("SCALE_ECONOMIES", StrengthRating.ESTABLISHED, StrengthRating.EMERGING),
    ("SWITCHING_COSTS", StrengthRating.EMERGING, StrengthRating.ESTABLISHED),
    ("BRANDING", StrengthRating.ESTABLISHED, StrengthRating.EMERGING),
    ("COUNTER_POSITIONING", StrengthRating.EMERGING, StrengthRating.EMERGING),
    ("CORNERED_RESOURCE", StrengthRating.NONE, StrengthRating.EMERGING),
    ("PROCESS_POWER", StrengthRating.EMERGING, StrengthRating.NONE),
)

# A spread of infrastructure maturity across two core modules so the heat map is not uniform.
_SUBS: tuple[tuple[str, str, MaturityLevel], ...] = (
    ("APP_SERVER", "APP_SERVER_HOSTING_ELASTICITY", MaturityLevel.FRONTIER),
    ("APP_SERVER", "APP_SERVER_RESILIENCE_DR", MaturityLevel.ADVANCED),
    ("APP_SERVER", "APP_SERVER_API_DESIGN", MaturityLevel.ADVANCED),
    ("APP_SERVER", "APP_SERVER_SECURITY_COMPLIANCE", MaturityLevel.DEVELOPING),
    ("OEMS", "OEMS_ASSET_COVERAGE", MaturityLevel.DEVELOPING),
    ("OEMS", "OEMS_PRE_TRADE_RISK", MaturityLevel.BASIC),
)

_METRICS: tuple[tuple[str, float, MetricConfidence], ...] = (
    ("ACTIVE_CLIENTS", 45_000_000, MetricConfidence.MANAGEMENT),
    ("AUA", 30_000_000_000, MetricConfidence.MANAGEMENT),
    ("NET_REVENUE", 2_200_000_000, MetricConfidence.AUDITED),
)


def revolut_demo_document() -> AssessmentDocument:
    """The illustrative Revolut assessment document — all 7 powers, three metrics, and a spread of
    infrastructure ratings. Pure (no DB); validates against the registry at construction."""
    powers = tuple(
        PowerEntry(
            power_key=key,
            benefit=benefit,
            barrier=barrier,
            benefit_grade=_E3,
            barrier_grade=_E3,
        )
        for key, benefit, barrier in _POWERS
    )
    subs = tuple(
        SubcomponentRating(module_key=m, subcomponent_key=s, level=level, evidence_grade=_E3)
        for m, s, level in _SUBS
    )
    metrics = tuple(
        MetricEntry(metric_key=k, raw=raw, confidence=conf) for k, raw, conf in _METRICS
    )
    return AssessmentDocument(
        subject=REVOLUT_SUBJECT, subcomponents=subs, metrics=metrics, powers=powers
    )


def seed_revolut_demo(session_factory, engine, settings, *, owner_email: str) -> dict[str, str]:
    """Seed the whole Revolut DEMO chain for `owner_email` and return the created ids.

    The DEMO assessment is created SERVER-SIDE via the repository (the HTTP create endpoint only
    honours sandbox for a client — demo is a server concern), then driven through the REAL endpoints
    (save document → finalise → engagement → generate every deliverable). The finalise endpoint
    self-approves a non-production record (ADR-0029), so no co-rater/committee is needed and the
    production gate is untouched. Idempotent-ish: re-running adds another demo record.
    """
    # Imported lazily so the pure document builder above has no web/DB import cost.
    from fastapi.testclient import TestClient

    from grassmarket.auth.security import create_access_token, hash_password
    from grassmarket.data.repository import Principal, Repository
    from grassmarket.web.app import create_app

    # 1) Ensure the owner exists (a Certified Lead, like the dev seed advisor).
    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(owner_email)
        if owner is None:
            from bcap_contracts.common import AssessorLevel, ConsultantTier

            owner = repo.create_consultant(
                email=owner_email,
                full_name="Demo Advisor",
                hashed_password=hash_password("grassmarket-demo"),
                role=Role.CONSULTANT,
                tier=ConsultantTier.CONSULTANT,
                assessor_level=AssessorLevel.CERTIFIED_LEAD,
            )
            session.commit()
        owner_id = owner.id
        # 2) Create the DEMO assessment server-side (immutable provenance, ADR-0029).
        principal = Principal(consultant_id=owner_id, role=owner.role)
        assessment = repo.create_assessment(
            principal, subject=REVOLUT_SUBJECT, provenance=RecordProvenance.DEMO
        )
        session.commit()
        assessment_id = str(assessment.id)
    finally:
        session.close()

    token = create_access_token(
        settings,
        consultant_id=owner_id,
        email=owner_email,
        role=owner.role,
        tier=owner.tier,
        assessor_level=owner.assessor_level,
    )
    headers = {"Authorization": f"Bearer {token}"}
    client = TestClient(create_app(settings=settings, engine=engine))

    # 3) A Revolut prospect at contracted, so the engagement has a real home.
    pid = client.post("/prospects", json={"company_name": REVOLUT_SUBJECT}, headers=headers).json()[
        "id"
    ]
    for stage in (
        PipelineStage.WORKSHOP_SCHEDULED,
        PipelineStage.WORKSHOP_DELIVERED,
        PipelineStage.QUALIFIED,
        PipelineStage.SCOPED,
        PipelineStage.CONTRACTED,
    ):
        client.patch(f"/prospects/{pid}/stage", json={"stage": stage.value}, headers=headers)

    # 4) Save the illustrative document, then finalise (self-approves for a DEMO record).
    client.put(
        f"/assessments/{assessment_id}",
        json=revolut_demo_document().model_dump(mode="json"),
        headers=headers,
    )
    finalised = client.post(f"/assessments/{assessment_id}/finalise", headers=headers)
    if finalised.status_code != 200:
        raise SystemExit(f"Demo seed failed to finalise: {finalised.status_code} {finalised.text}")

    # 5) The engagement that consumes it.
    eid = client.post(
        "/engagements",
        json={
            "prospect_id": pid,
            "title": f"{REVOLUT_SUBJECT} — delivery",
            "assessment_ids": [assessment_id],
        },
        headers=headers,
    ).json()["id"]

    # 6) Run the REAL generator for every supported deliverable (watermarked internal drafts).
    generated: list[str] = []
    for dtype in _DEMO_DELIVERABLES:
        resp = client.post(
            f"/engagements/{eid}/deliverables",
            json={"deliverable_type": dtype.value, "client_facing": False},
            headers=headers,
        )
        if resp.status_code in (200, 201):
            generated.append(dtype.value)

    return {
        "owner_email": owner_email,
        "prospect_id": pid,
        "assessment_id": assessment_id,
        "engagement_id": eid,
        "deliverables": ",".join(generated),
    }


def seed_revolut_demo_from_env() -> dict[str, str]:
    """Convenience entry for a script: build engine/session from settings and seed for the dev
    advisor. Uses the same DEMO advisor as scripts/seed_dev.py so the record lands in that book."""
    from grassmarket.config import get_settings
    from grassmarket.data.database import (
        make_engine,
        make_session_factory,
        run_migrations,
    )

    settings = get_settings()
    engine = make_engine(settings.database_url)
    run_migrations(engine)
    session_factory = make_session_factory(engine)
    _ = datetime.now(UTC)  # (reserved for future dated seeding)
    return seed_revolut_demo(
        session_factory, engine, settings, owner_email="advisor@bruntsfieldcapital.com"
    )
