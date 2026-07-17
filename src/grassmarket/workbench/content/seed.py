"""Seed the Academy's authored catalog content (GRS-0122).

Idempotent: applies each seeded course through the CMS via ``upsert_published_course`` — safe to
run on every boot or from ``scripts/seed_dev.py``. Requires an admin principal (authoring is
admin-gated, ADR-0028). Seeded content is versioned like any other, so a founder deepening it later
just publishes a new version over the top.
"""

from __future__ import annotations

from datetime import datetime

from bcap_contracts.commissions import load_commission_config

from grassmarket.data.repository import Principal, Repository
from grassmarket.earnings.product_carrot import product_commission_carrot
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
