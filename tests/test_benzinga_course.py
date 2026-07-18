"""Benzinga product course tests (GRS-0124).

The acceptance: a deep, use-case-aligned Benzinga course exists in the CMS on the GRS-0123 base so
its commission section resolves LIVE (the advisor's 15% share); it covers the key sellable facts +
honest caveats; it seeds idempotently; and completing it counts toward the `product:benzinga`
certification.
"""

from __future__ import annotations

from datetime import UTC, datetime

from bcap_contracts.commissions import load_commission_config

from grassmarket.data.repository import Repository
from grassmarket.earnings.product_carrot import product_commission_carrot
from grassmarket.workbench.content.benzinga_course import (
    BENZINGA_PRODUCT_ID,
    BENZINGA_SLUG,
    benzinga_course,
)
from grassmarket.workbench.content.seed import seed_academy_content
from grassmarket.workbench.course_certs import course_cert_subjects, product_subject_key
from tests.conftest import SeededConsultant

_NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def _carrot():
    return product_commission_carrot(BENZINGA_PRODUCT_ID, load_commission_config())


def test_course_is_deep_and_multi_module() -> None:
    tree = benzinga_course(_carrot())
    assert len(tree.modules) == 5
    lessons = [lesson for m in tree.modules for lesson in m.lessons]
    assert len(lessons) >= 18
    for lesson in lessons:
        assert lesson.body.strip() and lesson.drill_topics


def test_commission_resolves_live_the_advisor_share() -> None:
    carrot = _carrot()
    # The advisor share is 15% (Bruntsfield takes the reseller's 30% and shares half).
    assert carrot.yr1_bps == 1500
    body = next(
        lesson.body
        for m in benzinga_course(carrot).modules
        for lesson in m.lessons
        if lesson.title == "How much you earn"
    )
    assert carrot.schedule_version in body  # from the compute, not typed in


def test_content_covers_the_key_facts_and_caveats() -> None:
    text = " ".join(lesson.body for m in benzinga_course(_carrot()).modules for lesson in m.lessons)
    lower = text.lower()
    for fact in ("wiim", "analyst rating", "unusual options", "redistribution", "raznick"):
        assert fact in lower, f"the course does not mention {fact!r}"
    # Honest positioning + attribution discipline are present.
    assert "not a terminal" in lower or "not a full institutional terminal" in lower
    assert "not validated alpha" in lower


def test_seed_publishes_and_aligns_with_the_product_cert(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    published = repo.get_published_course(alice.principal, BENZINGA_SLUG)
    assert published.tree.title == "Benzinga — product course"
    assert len(published.tree.modules) == 5

    subj = next(
        s for s in course_cert_subjects(["benzinga"]) if s.key == product_subject_key("benzinga")
    )
    assert subj.backing_slug == BENZINGA_SLUG


def test_seed_is_idempotent(repo: Repository, admin: SeededConsultant) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    seed_academy_content(repo, admin.principal, now=_NOW)
    versions = repo.list_course_versions(admin.principal, BENZINGA_SLUG)
    assert [v.version for v in versions] == [1, 2]
    ids_v1 = [lesson.id for m in versions[0].tree.modules for lesson in m.lessons]
    ids_v2 = [lesson.id for m in versions[1].tree.modules for lesson in m.lessons]
    assert ids_v1 == ids_v2
