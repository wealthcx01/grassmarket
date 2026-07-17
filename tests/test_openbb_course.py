"""OpenBB product course tests (GRS-0126).

The acceptance: a rich, use-case-aligned OpenBB course exists in the CMS, built on the GRS-0123
template so its commission section resolves LIVE from the Earnings v7 schedule; it is deep
(multiple modules of research-grounded content); it seeds idempotently; and completing it counts
toward the `product:openbb` certification (GRS-0127) via the `product-openbb` slug.
"""

from __future__ import annotations

from datetime import UTC, datetime

from bcap_contracts.commissions import load_commission_config

from grassmarket.data.repository import Repository
from grassmarket.earnings.product_carrot import product_commission_carrot
from grassmarket.workbench.content.openbb_course import (
    OPENBB_PRODUCT_ID,
    OPENBB_SLUG,
    openbb_course,
)
from grassmarket.workbench.content.seed import seed_academy_content
from grassmarket.workbench.course_certs import product_subject_key
from tests.conftest import SeededConsultant

_NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def _carrot():
    return product_commission_carrot(OPENBB_PRODUCT_ID, load_commission_config())


def test_course_is_deep_and_multi_module() -> None:
    tree = openbb_course(_carrot())
    # Template spine + 4 deep modules; a genuinely deep course (not the 4-lesson minimum).
    assert len(tree.modules) == 5
    lessons = [lesson for m in tree.modules for lesson in m.lessons]
    assert len(lessons) >= 18
    for lesson in lessons:
        assert lesson.body.strip() and lesson.drill_topics
    # Every deep lesson (all but the 4 template-spine sections) carries a measurement.
    assert sum(1 for lesson in lessons if lesson.measurement) >= 18


def test_commission_section_resolves_live_not_hardcoded() -> None:
    carrot = _carrot()
    tree = openbb_course(carrot)
    commission_lessons = [
        lesson for m in tree.modules for lesson in m.lessons if lesson.title == "How much you earn"
    ]
    assert len(commission_lessons) == 1
    body = commission_lessons[0].body
    # The live rate + schedule version appear (from the Earnings v7 compute, not typed in).
    assert carrot.schedule_version in body


def test_content_covers_the_key_sellable_facts() -> None:
    text = " ".join(
        lesson.body for m in openbb_course(_carrot()).modules for lesson in m.lessons
    ).lower()
    # Accuracy anchors from the research pass.
    for fact in ("workspace", "open data platform", "agplv3", "mcp", "custom backend", "snowflake"):
        assert fact in text, f"the course does not mention {fact!r}"
    # The honest positioning + the founder story are present.
    assert "bloomberg" in text and "gamestonk" in text


def test_seed_publishes_openbb_and_aligns_with_the_product_cert(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    published = repo.get_published_course(alice.principal, OPENBB_SLUG)
    assert published.tree.title == "OpenBB — product course"
    assert len(published.tree.modules) == 5

    # The slug backs the product:openbb certification subject (GRS-0127).
    from grassmarket.workbench.course_certs import course_cert_subjects

    subj = next(
        s for s in course_cert_subjects(["openbb"]) if s.key == product_subject_key("openbb")
    )
    assert subj.backing_slug == OPENBB_SLUG


def test_seed_is_idempotent(repo: Repository, admin: SeededConsultant) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    seed_academy_content(repo, admin.principal, now=_NOW)
    versions = repo.list_course_versions(admin.principal, OPENBB_SLUG)
    assert [v.version for v in versions] == [1, 2]
    ids_v1 = [lesson.id for m in versions[0].tree.modules for lesson in m.lessons]
    ids_v2 = [lesson.id for m in versions[1].tree.modules for lesson in m.lessons]
    assert ids_v1 == ids_v2  # stable uuid5 ids across re-seeds
