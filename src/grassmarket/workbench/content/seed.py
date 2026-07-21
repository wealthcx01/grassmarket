"""Seed the Academy's authored catalog content (GRS-0122).

Idempotent: applies each seeded course through the CMS via ``upsert_published_course`` — safe to
run on every boot or from ``scripts/seed_dev.py``. Requires an admin principal (authoring is
admin-gated, ADR-0028). Seeded content is versioned like any other, so a founder deepening it later
just publishes a new version over the top.
"""

from __future__ import annotations

import secrets
from collections.abc import Callable
from datetime import UTC, datetime

from bcap_contracts.commissions import load_commission_config
from bcap_contracts.common import AssessorLevel, ConsultantTier, Role
from sqlalchemy.orm import Session

from grassmarket.auth.security import hash_password
from grassmarket.data.repository import Principal, Repository
from grassmarket.earnings.product_carrot import product_commission_carrot
from grassmarket.workbench.content.benzinga_course import (
    BENZINGA_PRODUCT_ID,
    BENZINGA_SLUG,
    benzinga_course,
)
from grassmarket.workbench.content.brandfetch_course import (
    BRANDFETCH_PRODUCT_ID,
    BRANDFETCH_REDIST_ID,
    BRANDFETCH_SLUG,
    brandfetch_course,
)
from grassmarket.workbench.content.openbb_course import (
    OPENBB_PRODUCT_ID,
    OPENBB_SLUG,
    openbb_course,
)
from grassmarket.workbench.content.practice_scenarios import academy_practice_scenarios
from grassmarket.workbench.content.sales_egoist import (
    SALES_EGOIST_SLUG,
    sales_egoist_course,
)
from grassmarket.workbench.content.sales_ops_playbook import (
    SALES_OPS_SLUG,
    sales_ops_playbook_course,
)


def seed_academy_content(repo: Repository, admin: Principal, *, now: datetime) -> None:
    """Publish (or re-publish) the seeded Academy content: the Sales Egoist core module (GRS-0122),
    the Sales Operations Playbook (GRS-0129), the OpenBB product course (GRS-0126), and the
    Academy-grounded Practice Arena scenarios (GRS-0130). Idempotent — courses upsert by slug;
    scenarios are created only when absent."""
    repo.upsert_published_course(admin, SALES_EGOIST_SLUG, sales_egoist_course(), now=now)
    repo.upsert_published_course(admin, SALES_OPS_SLUG, sales_ops_playbook_course(), now=now)

    # The product courses reuse the GRS-0123 template, so their commission resolves live from the
    # Earnings v7 schedule (fails loud if a product is ever removed from the config).
    config = load_commission_config()
    repo.upsert_published_course(
        admin,
        OPENBB_SLUG,
        openbb_course(product_commission_carrot(OPENBB_PRODUCT_ID, config)),
        now=now,
    )
    # Brandfetch has two tiers; the course shows both live (distribution is the template spine).
    repo.upsert_published_course(
        admin,
        BRANDFETCH_SLUG,
        brandfetch_course(
            product_commission_carrot(BRANDFETCH_PRODUCT_ID, config),
            product_commission_carrot(BRANDFETCH_REDIST_ID, config),
        ),
        now=now,
    )
    repo.upsert_published_course(
        admin,
        BENZINGA_SLUG,
        benzinga_course(product_commission_carrot(BENZINGA_PRODUCT_ID, config)),
        now=now,
    )

    # Practice-arena scenarios have no natural key; seed idempotently by title (create if absent).
    existing_titles = {s.title for s in repo.list_arena_scenarios(admin)}
    for spec in academy_practice_scenarios():
        if spec.title in existing_titles:
            continue
        repo.create_arena_scenario(
            admin,
            title=spec.title,
            brief=spec.brief,
            client_persona=spec.client_persona,
            target_powers=spec.target_powers,
            evidence_cues=spec.evidence_cues,
        )


# The dedicated non-login admin the boot/CLI seed authors as (authoring is admin-gated, ADR-0028).
# Created with an UNGUESSABLE, never-recorded password so it can never be logged into — it exists
# only to own the seeded catalog. Distinct from any real human admin.
_SEEDER_EMAIL = "academy-seeder@system.bruntsfield.internal"


def ensure_seed_admin(repo: Repository) -> Principal:
    """Ensure the system seeding admin exists (idempotent); return a principal to author as."""
    admin = repo.get_consultant_by_email(_SEEDER_EMAIL)
    if admin is None:
        admin = repo.create_consultant(
            email=_SEEDER_EMAIL,
            full_name="Academy Seeder (system)",
            hashed_password=hash_password(secrets.token_urlsafe(32)),  # unusable — no login path
            role=Role.ADMIN,
            tier=ConsultantTier.CONSULTANT,
            assessor_level=AssessorLevel.TRAINED,
        )
    return Principal(consultant_id=admin.id, role=admin.role)


def seed_academy(session_factory: Callable[[], Session], *, now: datetime | None = None) -> None:
    """Ensure the seeding admin, then publish the Academy catalog. Idempotent; one commit. Called at
    boot (GM_SEED_ACADEMY_ON_BOOT) and by ``scripts/seed_academy.py`` (GRS-0158)."""
    session = session_factory()
    try:
        repo = Repository(session)
        seed_academy_content(repo, ensure_seed_admin(repo), now=now or datetime.now(UTC))
        session.commit()
    finally:
        session.close()
