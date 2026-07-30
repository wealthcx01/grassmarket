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
from grassmarket.data.repository import Repository, StoredConsultant  # noqa: E402
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


def _ensure_consultant(
    session_factory,
    *,
    email: str,
    full_name: str,
    password: str | None,
    role: Role = Role.CONSULTANT,
) -> StoredConsultant:
    """Bootstrap a consultant directly (no self-register endpoint exists); idempotent on email.
    Returns the stored record (with id/role/tier/assessor_level for token minting)."""
    session = session_factory()
    try:
        repo = Repository(session)
        stored = repo.get_consultant_by_email(email)
        if stored is None:
            stored = repo.create_consultant(
                email=email,
                full_name=full_name,
                hashed_password=hash_password(password or "grassmarket-reviewer"),
                role=role,
                tier=ConsultantTier.CONSULTANT,
                assessor_level=AssessorLevel.CERTIFIED_LEAD,
            )
            session.commit()
        return stored
    finally:
        session.close()


def _seed_academy(session_factory, admin: StoredConsultant) -> None:
    """Publish the Academy's seeded courses (Sales Egoist core, GRS-0122) as the admin."""
    from datetime import UTC, datetime

    from grassmarket.data.repository import Principal
    from grassmarket.workbench.content.seed import seed_academy_content

    session = session_factory()
    try:
        repo = Repository(session)
        seed_academy_content(
            repo, Principal(consultant_id=admin.id, role=admin.role), now=datetime.now(UTC)
        )
        session.commit()
    finally:
        session.close()


def _headers(settings, stored) -> dict:
    token = create_access_token(
        settings,
        consultant_id=stored.id,
        email=stored.email,
        role=stored.role,
        tier=stored.tier,
        assessor_level=stored.assessor_level,
    )
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    settings = get_settings()
    engine = make_engine(settings.database_url)
    run_migrations(engine)
    session_factory = make_session_factory(engine)

    stored = _ensure_consultant(
        session_factory, email=DEMO_EMAIL, full_name="Demo Advisor", password=DEMO_PASSWORD
    )
    # The founder reviewer (ADR-0041). Identity is derived per request from the token's email
    # against `founder_reviewer_email` — not a role and not a column — so the seed only has to
    # create a consultant under that address for the gate to recognise them.
    founder = _ensure_consultant(
        session_factory,
        email=settings.founder_reviewer_email,
        full_name="Demo Founder",
        password=None,
    )
    # An admin seeds the Academy catalog content (authoring is admin-gated, ADR-0028).
    admin = _ensure_consultant(
        session_factory,
        email="admin@bruntsfieldcapital.com",
        full_name="Demo Admin",
        password=None,
        role=Role.ADMIN,
    )
    _seed_academy(session_factory, admin)
    headers = _headers(settings, stored)
    founder_headers = _headers(settings, founder)

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

    # The founder review gate (ADR-0041, GRS-0188): a production record cannot finalise until the
    # founder has approved the version in front of them. This replaced the dual-rating consensus
    # and Rating Committee steps that used to sit here — both now answer 410 Gone, which is how
    # this seed broke: it kept calling them and read the refusal body as a queue.
    submitted = client.post(f"/assessments/{aid}/submit-for-review", headers=headers)
    if submitted.status_code != 200:
        raise SystemExit(
            f"Seed failed to submit for founder review: {submitted.status_code} {submitted.text}"
        )
    approved = client.post(f"/assessments/{aid}/founder-approval", headers=founder_headers)
    if approved.status_code != 201:
        raise SystemExit(
            f"Seed failed to record founder approval: {approved.status_code} {approved.text}"
        )

    finalised = client.post(f"/assessments/{aid}/finalise", headers=headers)
    if finalised.status_code != 200:
        raise SystemExit(
            f"Seed failed to finalise the assessment: {finalised.status_code} {finalised.text}"
        )

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
