"""Brandfetch product course tests (GRS-0125).

The acceptance: a deep, use-case-aligned Brandfetch course exists in the CMS on the GRS-0123 base
so its commission section resolves LIVE; it centres the two commercial tiers (distribution vs
redistribution) with BOTH live rates; it seeds idempotently; and completing it counts toward the
`product:brandfetch_distribution` certification (whose backing slug is the hyphenated
`product-brandfetch-distribution`).
"""

from __future__ import annotations

from datetime import UTC, datetime

from bcap_contracts.commissions import load_commission_config

from grassmarket.data.repository import Repository
from grassmarket.earnings.product_carrot import product_commission_carrot
from grassmarket.workbench.content.brandfetch_course import (
    BRANDFETCH_PRODUCT_ID,
    BRANDFETCH_REDIST_ID,
    BRANDFETCH_SLUG,
    brandfetch_course,
)
from grassmarket.workbench.content.seed import seed_academy_content
from grassmarket.workbench.course_certs import course_cert_subjects, product_subject_key
from tests.conftest import SeededConsultant

_NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def _course():
    config = load_commission_config()
    return brandfetch_course(
        product_commission_carrot(BRANDFETCH_PRODUCT_ID, config),
        product_commission_carrot(BRANDFETCH_REDIST_ID, config),
    )


def test_course_is_deep_and_multi_module() -> None:
    tree = _course()
    assert len(tree.modules) == 5
    lessons = [lesson for m in tree.modules for lesson in m.lessons]
    assert len(lessons) >= 18
    for lesson in lessons:
        assert lesson.body.strip() and lesson.drill_topics


def test_both_commission_tiers_resolve_live() -> None:
    config = load_commission_config()
    dist = product_commission_carrot(BRANDFETCH_PRODUCT_ID, config)
    redist = product_commission_carrot(BRANDFETCH_REDIST_ID, config)
    body = next(
        lesson.body
        for m in _course().modules
        for lesson in m.lessons
        if lesson.title == "Your two commission tiers, live"
    )
    # Both live rates + the schedule version appear (from the compute, not typed in).
    assert f"{dist.yr1_bps / 100:g}%" in body and f"{redist.yr1_bps / 100:g}%" in body
    assert dist.schedule_version in body
    # Distribution genuinely pays more than redistribution (the reason the lesson teaches).
    assert dist.yr1_bps > redist.yr1_bps


def test_content_covers_the_key_sellable_facts() -> None:
    text = " ".join(lesson.body for m in _course().modules for lesson in m.lessons).lower()
    for fact in ("brand api", "ticker", "isin", "transaction api", "redistribution", "trademark"):
        assert fact in text, f"the course does not mention {fact!r}"
    # Finance peer proof + honest positioning.
    assert "morningstar" in text and "envestnet" in text


def test_seed_publishes_and_aligns_with_the_product_cert(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    published = repo.get_published_course(alice.principal, BRANDFETCH_SLUG)
    assert published.tree.title == "Brandfetch — product course"
    assert len(published.tree.modules) == 5

    # The hyphenated slug backs the product:brandfetch_distribution cert (underscore→hyphen fix).
    subj = next(
        s
        for s in course_cert_subjects(["brandfetch_distribution"])
        if s.key == product_subject_key("brandfetch_distribution")
    )
    assert subj.backing_slug == BRANDFETCH_SLUG


def test_seed_is_idempotent(repo: Repository, admin: SeededConsultant) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    seed_academy_content(repo, admin.principal, now=_NOW)
    versions = repo.list_course_versions(admin.principal, BRANDFETCH_SLUG)
    assert [v.version for v in versions] == [1, 2]
    ids_v1 = [lesson.id for m in versions[0].tree.modules for lesson in m.lessons]
    ids_v2 = [lesson.id for m in versions[1].tree.modules for lesson in m.lessons]
    assert ids_v1 == ids_v2
