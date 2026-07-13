"""Seed the local SQLite database with a demo consultant and a full engagement chain, so the app
can be driven end-to-end locally (GRS-0019 needs seeded data for the browser workflow).

Auth is invite-only, so the first consultant is bootstrapped directly through the repository (as the
tests do); the rest of the chain — a contracted prospect, a finalised assessment (with its scoring
run), and an engagement linking them — is created through the real HTTP API via an in-process
TestClient, so it exercises exactly the surface the frontend uses.

Run:  uv run python scripts/seed_dev.py   (against ./local.db by default)
Login printed at the end. Idempotent on the consultant; re-running adds another prospect/engagement.
"""

from __future__ import annotations

import os

os.environ.setdefault("GM_JWT_SECRET", "local-dev-secret-that-is-more-than-thirty-two-chars-xxxxx")
os.environ.setdefault("GM_DATABASE_URL", "sqlite+pysqlite:///./local.db")

from bcap_contracts.assessments import (  # noqa: E402
    AssessmentDocument,
    MetricEntry,
    PowerEntry,
    SubcomponentRating,
)
from bcap_contracts.common import (  # noqa: E402
    AssessorLevel,
    ConsultantTier,
    EvidenceGrade,
    MaturityLevel,
    MetricConfidence,
    Role,
    StrengthRating,
)
from bcap_contracts.entities import PipelineStage  # noqa: E402
from bcap_contracts.registry import load_registry  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from grassmarket.auth.security import create_access_token, hash_password  # noqa: E402
from grassmarket.config import get_settings  # noqa: E402
from grassmarket.data.database import (  # noqa: E402
    make_engine,
    make_session_factory,
    run_migrations,
)
from grassmarket.data.repository import Repository  # noqa: E402
from grassmarket.web.app import create_app  # noqa: E402

DEMO_EMAIL = "advisor@bruntsfieldcapital.com"
DEMO_PASSWORD = "grassmarket-demo"  # pragma: allowlist secret  (local dev seed only)
_TO_CONTRACTED = (
    PipelineStage.WORKSHOP_SCHEDULED,
    PipelineStage.WORKSHOP_DELIVERED,
    PipelineStage.QUALIFIED,
    PipelineStage.SCOPED,
    PipelineStage.CONTRACTED,
)


def _scoreable_partial_doc() -> AssessmentDocument:
    """A genuinely partial but scoreable document: all 7 powers graded, one metric, one rated
    subcomponent in a core module — enough to finalise into a real scoring run."""
    registry = load_registry()
    e3 = EvidenceGrade.E3_ARTIFACT
    powers = tuple(
        PowerEntry(
            power_key=p.key,
            benefit=StrengthRating.EMERGING,
            barrier=StrengthRating.EMERGING,
            benefit_grade=e3,
            barrier_grade=e3,
        )
        for p in registry.powers
    )
    metrics = (
        MetricEntry(metric_key="AUA", raw=1_000_000_000, confidence=MetricConfidence.AUDITED),
    )
    subs = (
        SubcomponentRating(
            module_key="APP_SERVER",
            subcomponent_key="APP_SERVER_SECURITY_COMPLIANCE",
            level=MaturityLevel.ADVANCED,
            evidence_grade=e3,
        ),
    )
    return AssessmentDocument(
        subject="Meridian Securities", subcomponents=subs, metrics=metrics, powers=powers
    )


def main() -> None:
    settings = get_settings()
    engine = make_engine(settings.database_url)
    run_migrations(engine)
    session_factory = make_session_factory(engine)

    # Bootstrap the demo consultant directly (no self-register endpoint exists).
    session = session_factory()
    repo = Repository(session)
    stored = repo.get_consultant_by_email(DEMO_EMAIL)
    if stored is None:
        stored = repo.create_consultant(
            email=DEMO_EMAIL,
            full_name="Demo Advisor",
            hashed_password=hash_password(DEMO_PASSWORD),
            role=Role.CONSULTANT,
            tier=ConsultantTier.CONSULTANT,
            assessor_level=AssessorLevel.TRAINED,
        )
        session.commit()
    session.close()

    token = create_access_token(
        settings,
        consultant_id=stored.id,
        email=stored.email,
        role=stored.role,
        tier=stored.tier,
        assessor_level=stored.assessor_level,
    )
    headers = {"Authorization": f"Bearer {token}"}

    client = TestClient(create_app(settings=settings, engine=engine))

    pid = client.post(
        "/prospects", json={"company_name": "Meridian Securities"}, headers=headers
    ).json()["id"]
    for stage in _TO_CONTRACTED:
        client.patch(f"/prospects/{pid}/stage", json={"stage": stage.value}, headers=headers)

    aid = client.post(
        "/assessments", json={"subject": "Meridian Securities"}, headers=headers
    ).json()["id"]
    client.put(
        f"/assessments/{aid}",
        json=_scoreable_partial_doc().model_dump(mode="json"),
        headers=headers,
    )
    client.post(f"/assessments/{aid}/finalise", headers=headers)

    eid = client.post(
        "/engagements",
        json={
            "prospect_id": pid,
            "title": "Meridian Securities — delivery",
            "assessment_ids": [aid],
        },
        headers=headers,
    ).json()["id"]

    print("Seeded local database.")
    print(f"  Login:      {DEMO_EMAIL} / {DEMO_PASSWORD}")
    print(f"  Prospect:   {pid}")
    print(f"  Assessment: {aid} (finalised)")
    print(f"  Engagement: {eid}")


if __name__ == "__main__":
    main()
