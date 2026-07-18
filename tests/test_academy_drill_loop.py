"""Academy learning loop (GRS-0139).

Completing a lesson wires the spaced-repetition loop: it auto-enrolls a real drill card — with a
recall question and a model answer — for each topic the lesson teaches, so learning is reinforced,
not read-and-forget. Idempotent per topic; the content falls back to the lesson's measurement when
no comprehension check is authored.
"""

from __future__ import annotations

from datetime import UTC, datetime

from grassmarket.data.repository import Repository
from grassmarket.workbench.content.sales_egoist import SALES_EGOIST_SLUG
from grassmarket.workbench.content.sales_ops_playbook import SALES_OPS_SLUG
from grassmarket.workbench.content.seed import seed_academy_content
from tests.conftest import SeededConsultant

_NOW = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)


def _lessons(repo: Repository, principal, slug: str):
    tree = repo.get_published_course(principal, slug).tree
    return [les for m in tree.modules for les in m.lessons]


def test_completing_a_lesson_auto_enrolls_a_real_drill(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    lesson = _lessons(repo, alice.principal, SALES_EGOIST_SLUG)[0]
    assert repo.list_drill_cards(alice.principal) == []  # no drills before

    repo.complete_lesson(alice.principal, SALES_EGOIST_SLUG, lesson.id, now=_NOW)

    cards = repo.list_drill_cards(alice.principal)
    topics = {c.topic for c in cards}
    assert set(lesson.drill_topics) <= topics  # a card per topic the lesson teaches
    card = next(c for c in cards if c.topic in lesson.drill_topics)
    # It's a real flashcard — the authored comprehension check, not a blank topic.
    assert card.prompt and card.answer
    assert card.prompt == lesson.check_question


def test_auto_enroll_is_idempotent_across_lessons(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    lesson = _lessons(repo, alice.principal, SALES_EGOIST_SLUG)[0]
    repo.complete_lesson(alice.principal, SALES_EGOIST_SLUG, lesson.id, now=_NOW)
    before = len(repo.list_drill_cards(alice.principal))
    # Completing a second lesson (different topic) adds its own; a shared topic never duplicates.
    lesson2 = _lessons(repo, alice.principal, SALES_EGOIST_SLUG)[1]
    repo.complete_lesson(alice.principal, SALES_EGOIST_SLUG, lesson2.id, now=_NOW)
    cards = repo.list_drill_cards(alice.principal)
    assert len(cards) == before + len(set(lesson2.drill_topics) - set(lesson.drill_topics))
    # One card per distinct topic — no duplicates.
    assert len({c.topic for c in cards}) == len(cards)


def test_drill_content_falls_back_to_measurement(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    # The sales-ops playbook lessons have no authored check_question → the drill recall prompt is
    # derived from the lesson's measurement, which is the answer key.
    seed_academy_content(repo, admin.principal, now=_NOW)
    lesson = next(
        les for les in _lessons(repo, alice.principal, SALES_OPS_SLUG) if les.check_question is None
    )
    repo.complete_lesson(alice.principal, SALES_OPS_SLUG, lesson.id, now=_NOW)
    card = next(c for c in repo.list_drill_cards(alice.principal) if c.topic in lesson.drill_topics)
    assert lesson.title in card.prompt  # a recall prompt built from the lesson
    assert card.answer == lesson.measurement  # the measurement is the answer key
