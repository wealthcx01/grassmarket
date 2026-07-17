"""Seed the Academy's authored catalog content (GRS-0122).

Idempotent: applies each seeded course through the CMS via ``upsert_published_course`` — safe to
run on every boot or from ``scripts/seed_dev.py``. Requires an admin principal (authoring is
admin-gated, ADR-0028). Seeded content is versioned like any other, so a founder deepening it later
just publishes a new version over the top.
"""

from __future__ import annotations

from datetime import datetime

from grassmarket.data.repository import Principal, Repository
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
    the Sales Operations Playbook (GRS-0129), and the Academy-grounded Practice Arena scenarios
    (GRS-0130). Idempotent — courses upsert by slug; scenarios are created only when absent."""
    repo.upsert_published_course(admin, SALES_EGOIST_SLUG, sales_egoist_course(), now=now)
    repo.upsert_published_course(admin, SALES_OPS_SLUG, sales_ops_playbook_course(), now=now)

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
