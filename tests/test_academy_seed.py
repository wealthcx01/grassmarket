"""GRS-0158 — the production Academy seed fills an empty catalog and is idempotent.

Reproduces the founder-reported symptom (a fresh Railway DB shows an empty Workbench) and proves the
seed fixes it, so the empty-catalog regression can't return silently.
"""

from __future__ import annotations

from uuid import uuid4

from bcap_contracts.common import Role
from sqlalchemy.orm import Session, sessionmaker

from grassmarket.data.repository import Principal, Repository
from grassmarket.workbench.content.seed import ensure_seed_admin, seed_academy

_EXPECTED = {
    "sales-egoist",
    "sales-ops-playbook",
    "product-openbb",
    "product-brandfetch-distribution",
    "product-benzinga",
}


def test_academy_seed_fills_empty_db_and_is_idempotent(
    session_factory: sessionmaker[Session],
) -> None:
    # A freshly-migrated DB serves NO courses — the exact production symptom.
    anyone = Principal(consultant_id=uuid4(), role=Role.ADMIN)
    assert Repository(session_factory()).list_published_courses(anyone) == []

    seed_academy(session_factory)

    repo = Repository(session_factory())
    slugs = {c.slug for c in repo.list_published_courses(ensure_seed_admin(repo))}
    assert _EXPECTED <= slugs

    # Re-running the seed does not error or duplicate the catalog (safe on every boot).
    seed_academy(session_factory)
    repo2 = Repository(session_factory())
    assert {c.slug for c in repo2.list_published_courses(ensure_seed_admin(repo2))} == slugs
