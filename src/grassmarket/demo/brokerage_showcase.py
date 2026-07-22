"""The repeatable brokerage-showcase demo seed (GRS-0159).

Promotes the 2026-07-21 staging end-to-end run (`scratch/stage/brokerage_e2e.py` +
`earnings_e2e.py`) to a first-class, reviewable, versioned seed: for each showcase brokerage it
builds the pipeline chain (prospect → Contracted), a COMPLETE review-grounded assessment (all nine
infrastructure modules, all seven powers, business metrics, and the full C-index customer
proposition), finalises it, opens the engagement, runs the real deliverable generators, and records
the illustrative Year-1 product commission — so a clean environment demos with populated pipeline,
portfolio (V + C spread), deliverables, and a non-zero earnings statement.

Every assessment is created with DEMO provenance (ADR-0029): self-approvable (no co-rater or
committee), permanently watermarked, and excluded from the benchmark population. All figures are
ILLUSTRATIVE ONLY — grounded in each brokerage's completed public widget review, never client data.

Idempotent: a brokerage whose DEMO assessment already exists for the owner is skipped whole
(assessment, engagement, deliverables, and commission), so re-running never duplicates records.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from bcap_contracts.assessments import (
    AssessmentDocument,
    MetricEntry,
    PowerEntry,
    RecordProvenance,
    SubcomponentRating,
)
from bcap_contracts.common import EvidenceGrade
from bcap_contracts.deliverables import DeliverableType
from bcap_contracts.entities import PipelineStage
from bcap_contracts.registry import load_registry

_E3 = EvidenceGrade.E3_ARTIFACT

# The date of the staging simulation the deals reproduce — deterministic on purpose, so a re-run
# (or a test) never depends on "today" and the seeded statement is stable.
_DEAL_EARNED_ON = date(2026, 7, 21)

# The five single-run diagnostic documents the generate endpoint supports (roadmap and
# score-evolution have their own paths and are refused there).
_SHOWCASE_DELIVERABLES: tuple[DeliverableType, ...] = (
    DeliverableType.PLATFORM_POWER_REPORT,
    DeliverableType.EXECUTIVE_SUMMARY,
    DeliverableType.INFRASTRUCTURE_HEATMAP,
    DeliverableType.TECHNICAL_APPENDIX,
    DeliverableType.WORKSHOP_OUTPUT,
)

# The pipeline lifecycle up to Contracted, in legal-move order. Advancement resumes from the
# prospect's CURRENT stage, so a reused prospect is never pushed through an illegal transition.
_LIFECYCLE_TO_CONTRACTED: tuple[PipelineStage, ...] = (
    PipelineStage.PROSPECT,
    PipelineStage.WORKSHOP_SCHEDULED,
    PipelineStage.WORKSHOP_DELIVERED,
    PipelineStage.QUALIFIED,
    PipelineStage.SCOPED,
    PipelineStage.CONTRACTED,
)


@dataclass(frozen=True)
class BrokerageSpec:
    """One showcase brokerage: the review-grounded assessment inputs plus its illustrative deal.

    Level/rating/confidence values are the contract enums' string values — validated (fail-loud)
    when the document is constructed, so a typo here can never seed a malformed record.
    """

    subject: str
    # (metric_key, raw value, MetricConfidence value)
    metrics: tuple[tuple[str, float, str], ...]
    # power_key -> (benefit, barrier) StrengthRating values
    powers: tuple[tuple[str, tuple[str, str]], ...]
    # Infrastructure: per-module base MaturityLevel, with per-subcomponent overrides.
    v_base: tuple[tuple[str, str], ...]
    v_over: tuple[tuple[str, str], ...]
    # Customer proposition (C-index): per-module base level (subcomponent overrides unused so far).
    c_base: tuple[tuple[str, str], ...]
    # The represented product "sold" against the report, and the Year-1 cash received (GBP minor
    # units) — the illustrative commission the earnings statement shows.
    product_id: str
    deal_value_minor: int


# ---- Review-grounded specs (retail operating model — the golden-master coefficient set) ----------
# Maturity/strength levels come from each brokerage's completed public widget-review checklist.

REVOLUT = BrokerageSpec(
    subject="Revolut",
    metrics=(
        ("ACTIVE_CLIENTS", 3_000_000, "estimated"),
        ("AUA", 20_000_000_000, "estimated"),
        ("NET_REVENUE", 1_800_000_000, "estimated"),
        ("CLIENT_GROWTH_RATE", 25, "estimated"),
    ),
    powers=(
        ("BRANDING", ("Established", "Established")),
        ("NETWORK_ECONOMIES", ("Emerging", "Emerging")),
        ("SWITCHING_COSTS", ("Emerging", "Emerging")),
        ("SCALE_ECONOMIES", ("Emerging", "Emerging")),
        ("COUNTER_POSITIONING", ("Established", "Emerging")),
        ("CORNERED_RESOURCE", ("None", "None")),
        ("PROCESS_POWER", ("Emerging", "Emerging")),
    ),
    v_base=(
        ("FRONTEND", "Advanced"),
        ("APP_SERVER", "Advanced"),
        ("MARKET_DATA", "Developing"),
        ("ORCHESTRATION", "Advanced"),
        ("CMS", "Developing"),
        ("BACKOFFICE", "Advanced"),
        ("OEMS", "Developing"),
        ("EMS_GATEWAY", "Developing"),
        ("LIQ_CONNECT", "Developing"),
    ),
    v_over=(
        ("FRONTEND_UX_NAVIGATION", "Frontier"),
        ("OEMS_ORDER_TYPES", "Basic"),
    ),
    c_base=(
        ("CUST_ONBOARDING", "Frontier"),
        ("CUST_UI_NAVIGATION", "Advanced"),
        ("CUST_TRADING_EXPERIENCE", "Developing"),
        ("CUST_FEES_PRICING", "Basic"),
        ("CUST_PRODUCT_RANGE", "Developing"),
        ("CUST_RESEARCH_EDUCATION", "Developing"),
        ("CUST_AI_PERSONALISATION", "Developing"),
        ("CUST_SUPPORT_COMMUNITY", "Basic"),
        ("CUST_SECURITY_REGULATION", "Advanced"),
        ("CUST_INNOVATION_DIFFERENTIATORS", "Advanced"),
    ),
    product_id="benzinga",
    deal_value_minor=10_000_000,  # £100,000 Year-1 deal
)

HARGREAVES_LANSDOWN = BrokerageSpec(
    subject="Hargreaves Lansdown",
    metrics=(
        ("AUA", 155_300_000_000, "management_reported"),
        ("ACTIVE_CLIENTS", 2_000_000, "management_reported"),
        ("NET_REVENUE", 764_000_000, "estimated"),
    ),
    powers=(
        ("BRANDING", ("Established", "Established")),
        ("SWITCHING_COSTS", ("Established", "Established")),
        ("SCALE_ECONOMIES", ("Established", "Emerging")),
        ("NETWORK_ECONOMIES", ("None", "None")),
        ("COUNTER_POSITIONING", ("None", "None")),
        ("CORNERED_RESOURCE", ("None", "None")),
        ("PROCESS_POWER", ("Emerging", "Emerging")),
    ),
    v_base=(
        ("FRONTEND", "Developing"),
        ("APP_SERVER", "Advanced"),
        ("MARKET_DATA", "Developing"),
        ("ORCHESTRATION", "Developing"),
        ("CMS", "Advanced"),
        ("BACKOFFICE", "Advanced"),
        ("OEMS", "Basic"),
        ("EMS_GATEWAY", "Developing"),
        ("LIQ_CONNECT", "Developing"),
    ),
    v_over=(
        ("BACKOFFICE_CUSTODY", "Advanced"),
        ("BACKOFFICE_REG_REPORTING", "Advanced"),
        ("OEMS_ORDER_TYPES", "Basic"),
        ("OEMS_ASSET_COVERAGE", "Basic"),
        ("FRONTEND_DEVICE_COVERAGE", "Developing"),
    ),
    c_base=(
        ("CUST_ONBOARDING", "Developing"),
        ("CUST_UI_NAVIGATION", "Developing"),
        ("CUST_TRADING_EXPERIENCE", "Basic"),
        ("CUST_FEES_PRICING", "Developing"),
        ("CUST_PRODUCT_RANGE", "Advanced"),
        ("CUST_RESEARCH_EDUCATION", "Advanced"),
        ("CUST_AI_PERSONALISATION", "Basic"),
        ("CUST_SUPPORT_COMMUNITY", "Developing"),
        ("CUST_SECURITY_REGULATION", "Advanced"),
        ("CUST_INNOVATION_DIFFERENTIATORS", "Basic"),
    ),
    product_id="openbb",
    deal_value_minor=15_000_000,  # £150,000 Year-1 deal
)

WEBULL = BrokerageSpec(
    subject="WeBull",
    metrics=(
        ("ACTIVE_CLIENTS", 4_000_000, "estimated"),
        ("CLIENT_GROWTH_RATE", 15, "estimated"),
        ("NET_REVENUE", 400_000_000, "estimated"),
    ),
    powers=(
        ("PROCESS_POWER", ("Emerging", "Emerging")),
        ("COUNTER_POSITIONING", ("Emerging", "Emerging")),
        ("NETWORK_ECONOMIES", ("Emerging", "Emerging")),
        ("BRANDING", ("Emerging", "Emerging")),
        ("SCALE_ECONOMIES", ("Emerging", "Emerging")),
        ("SWITCHING_COSTS", ("None", "None")),
        ("CORNERED_RESOURCE", ("None", "None")),
    ),
    v_base=(
        ("FRONTEND", "Developing"),
        ("APP_SERVER", "Advanced"),
        ("MARKET_DATA", "Advanced"),
        ("ORCHESTRATION", "Advanced"),
        ("CMS", "Developing"),
        ("BACKOFFICE", "Developing"),
        ("OEMS", "Frontier"),
        ("EMS_GATEWAY", "Advanced"),
        ("LIQ_CONNECT", "Developing"),
    ),
    v_over=(
        ("OEMS_ORDER_TYPES", "Frontier"),
        ("OEMS_ASSET_COVERAGE", "Advanced"),
        ("FRONTEND_UX_NAVIGATION", "Developing"),
        ("BACKOFFICE_PAYMENTS_FUNDING", "Basic"),
    ),
    c_base=(
        ("CUST_ONBOARDING", "Developing"),
        ("CUST_UI_NAVIGATION", "Developing"),
        ("CUST_TRADING_EXPERIENCE", "Frontier"),
        ("CUST_FEES_PRICING", "Advanced"),
        ("CUST_PRODUCT_RANGE", "Advanced"),
        ("CUST_RESEARCH_EDUCATION", "Advanced"),
        ("CUST_AI_PERSONALISATION", "Basic"),
        ("CUST_SUPPORT_COMMUNITY", "Advanced"),
        ("CUST_SECURITY_REGULATION", "Developing"),
        ("CUST_INNOVATION_DIFFERENTIATORS", "Advanced"),
    ),
    product_id="connecttrade",
    deal_value_minor=8_000_000,  # £80,000 Year-1 deal
)

SHOWCASE: tuple[BrokerageSpec, ...] = (REVOLUT, HARGREAVES_LANSDOWN, WEBULL)


class ShowcaseSeedError(RuntimeError):
    """A seeding step failed. Fail loud — never leave a half-seeded record silently behind."""


def showcase_document(spec: BrokerageSpec) -> AssessmentDocument:
    """The complete review-grounded document for one brokerage: every subcomponent of every
    infrastructure AND customer-proposition module rated (base level per module, targeted
    overrides), all seven powers, and the business metrics. Pure (no DB); validates against the
    registry at construction."""
    from bcap_contracts.common import MaturityLevel, MetricConfidence, StrengthRating

    registry = load_registry()
    # Enum coercion up front — an unknown level/rating/confidence value in a spec fails HERE with
    # the enum's own error, before any record is touched.
    v_base = {k: MaturityLevel(v) for k, v in spec.v_base}
    v_over = {k: MaturityLevel(v) for k, v in spec.v_over}
    c_base = {k: MaturityLevel(v) for k, v in spec.c_base}

    subs = tuple(
        SubcomponentRating(
            module_key=module.key,
            subcomponent_key=sc.key,
            level=v_over.get(sc.key, v_base[module.key]),
            evidence_grade=_E3,
        )
        for module in registry.modules
        for sc in module.subcomponents
    )
    c_subs = tuple(
        SubcomponentRating(
            module_key=module.key,
            subcomponent_key=sc.key,
            level=c_base[module.key],
            evidence_grade=_E3,
        )
        for module in registry.c_modules
        for sc in module.subcomponents
    )
    powers = tuple(
        PowerEntry(
            power_key=key,
            benefit=StrengthRating(benefit),
            barrier=StrengthRating(barrier),
            benefit_grade=_E3,
            barrier_grade=_E3,
        )
        for key, (benefit, barrier) in spec.powers
    )
    metrics = tuple(
        MetricEntry(metric_key=key, raw=raw, confidence=MetricConfidence(confidence))
        for key, raw, confidence in spec.metrics
    )
    return AssessmentDocument(
        subject=spec.subject,
        subcomponents=subs,
        metrics=metrics,
        powers=powers,
        c_subcomponents=c_subs,
    )


def seed_brokerage_showcase(
    session_factory, engine, settings, *, owner_email: str
) -> list[dict[str, str]]:
    """Seed the full showcase for `owner_email` and return one summary dict per brokerage.

    Assessments are created SERVER-SIDE with DEMO provenance (the HTTP create endpoint only honours
    sandbox for a client — demo is a server concern), then driven through the REAL endpoints:
    save document → finalise (self-approves, ADR-0029) → engagement → every deliverable generator →
    the admin-recorded product commission. Any step failing raises `ShowcaseSeedError`.
    """
    # Imported lazily so the pure spec/document layer above has no web/DB import cost.
    from bcap_contracts.common import AssessorLevel, ConsultantTier, Role
    from fastapi.testclient import TestClient

    from grassmarket.auth.security import create_access_token, hash_password
    from grassmarket.data.repository import Principal, Repository
    from grassmarket.web.app import create_app

    # 1) Ensure the owner (a Certified Lead, like the dev-seed advisor) and the admin who records
    #    commissions (objective money facts are never self-attested — the endpoint is admin-only).
    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(owner_email)
        if owner is None:
            owner = repo.create_consultant(
                email=owner_email,
                full_name="Demo Advisor",
                hashed_password=hash_password("grassmarket-demo"),
                role=Role.CONSULTANT,
                tier=ConsultantTier.CONSULTANT,
                assessor_level=AssessorLevel.CERTIFIED_LEAD,
            )
        admin = repo.get_consultant_by_email("admin@bruntsfieldcapital.com")
        if admin is None:
            admin = repo.create_consultant(
                email="admin@bruntsfieldcapital.com",
                full_name="Demo Admin",
                hashed_password=hash_password("grassmarket-reviewer"),
                role=Role.ADMIN,
                tier=ConsultantTier.CONSULTANT,
                assessor_level=AssessorLevel.CERTIFIED_LEAD,
            )
        session.commit()
        principal = Principal(consultant_id=owner.id, role=owner.role)
        # Idempotency: a brokerage whose DEMO assessment already exists is skipped whole.
        seeded_subjects = {
            a.subject
            for a in repo.list_assessments(principal)
            if a.provenance is RecordProvenance.DEMO
        }
        prospects = {p.company_name: p for p in repo.list_prospects(principal)}
    finally:
        session.close()

    def _headers(stored) -> dict[str, str]:
        token = create_access_token(
            settings,
            consultant_id=stored.id,
            email=stored.email,
            role=stored.role,
            tier=stored.tier,
            assessor_level=stored.assessor_level,
        )
        return {"Authorization": f"Bearer {token}"}

    headers = _headers(owner)
    admin_headers = _headers(admin)
    client = TestClient(create_app(settings=settings, engine=engine))
    results: list[dict[str, str]] = []

    for spec in SHOWCASE:
        if spec.subject in seeded_subjects:
            results.append({"subject": spec.subject, "status": "exists (skipped)"})
            continue

        # 2) Pipeline: reuse the prospect if a previous partial run created it; advance only the
        #    stages AFTER its current one, so a reused prospect never takes an illegal move.
        existing = prospects.get(spec.subject)
        if existing is not None:
            pid = str(existing.id)
            current = PipelineStage(existing.stage)
        else:
            created = client.post(
                "/prospects", json={"company_name": spec.subject}, headers=headers
            )
            if created.status_code != 201:
                raise ShowcaseSeedError(
                    f"{spec.subject}: create prospect failed {created.status_code}: {created.text}"
                )
            pid = created.json()["id"]
            current = PipelineStage.PROSPECT
        for stage in _LIFECYCLE_TO_CONTRACTED[_LIFECYCLE_TO_CONTRACTED.index(current) + 1 :]:
            moved = client.patch(
                f"/prospects/{pid}/stage", json={"stage": stage.value}, headers=headers
            )
            if moved.status_code != 200:
                raise ShowcaseSeedError(
                    f"{spec.subject}: stage {stage.value} failed {moved.status_code}: {moved.text}"
                )

        # 3) The DEMO assessment (server-side, immutable provenance) + the complete document.
        session = session_factory()
        try:
            assessment = Repository(session).create_assessment(
                principal, subject=spec.subject, provenance=RecordProvenance.DEMO
            )
            session.commit()
            aid = str(assessment.id)
        finally:
            session.close()
        saved = client.put(
            f"/assessments/{aid}",
            json=showcase_document(spec).model_dump(mode="json"),
            headers=headers,
        )
        if saved.status_code != 200:
            raise ShowcaseSeedError(
                f"{spec.subject}: save document failed {saved.status_code}: {saved.text}"
            )

        # 4) Finalise — a DEMO record self-approves (no co-rater/committee; gate untouched).
        finalised = client.post(f"/assessments/{aid}/finalise", headers=headers)
        if finalised.status_code != 200:
            raise ShowcaseSeedError(
                f"{spec.subject}: finalise failed {finalised.status_code}: {finalised.text}"
            )

        # 5) Engagement + the real generator for every supported deliverable.
        opened = client.post(
            "/engagements",
            json={
                "prospect_id": pid,
                "title": f"{spec.subject} — delivery",
                "assessment_ids": [aid],
            },
            headers=headers,
        )
        if opened.status_code != 201:
            raise ShowcaseSeedError(
                f"{spec.subject}: create engagement failed {opened.status_code}: {opened.text}"
            )
        eid = opened.json()["id"]
        for dtype in _SHOWCASE_DELIVERABLES:
            generated = client.post(
                f"/engagements/{eid}/deliverables",
                json={"deliverable_type": dtype.value, "client_facing": False},
                headers=headers,
            )
            if generated.status_code not in (200, 201):
                raise ShowcaseSeedError(
                    f"{spec.subject}: deliverable {dtype.value} failed "
                    f"{generated.status_code}: {generated.text}"
                )

        # 6) The illustrative Year-1 product commission, recorded by the admin (ADR-0026).
        recorded = client.post(
            "/earnings/commissions/product",
            json={
                "advisor_id": str(owner.id),
                "engagement_id": eid,
                "product_id": spec.product_id,
                "base_value_minor": spec.deal_value_minor,
                "currency": "GBP",
                "base_value_ref": "Brokerage showcase — illustrative Year-1 deal (DEMO)",
                "contract_year": 1,
                "earned_on": _DEAL_EARNED_ON.isoformat(),
            },
            headers=admin_headers,
        )
        if recorded.status_code != 201:
            raise ShowcaseSeedError(
                f"{spec.subject}: record commission failed {recorded.status_code}: {recorded.text}"
            )

        results.append(
            {
                "subject": spec.subject,
                "status": "seeded",
                "prospect_id": pid,
                "assessment_id": aid,
                "engagement_id": eid,
                "product_sold": spec.product_id,
            }
        )

    return results
