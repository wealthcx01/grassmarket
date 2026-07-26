"""Bruntsfield Academy course CMS tests (GRS-0121, ADR-0028).

The four things that matter: a nested course can be authored and re-published without a redeploy and
every version is retained; authoring is admin-only; an AI-authored lesson can't reach a published
version until approved (ADR-0009); and completing every lesson of a coursework course credits
coursework through the existing certification path (no regression).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from bcap_contracts.learning import (
    CertificationCredit,
    CourseModule,
    CourseTree,
    Lesson,
    LessonAuthor,
)

from grassmarket.data.repository import ConflictError, Repository, ScopeViolationError
from grassmarket.workbench.courses import is_course_complete, unapproved_ai_lessons
from tests.conftest import SeededConsultant, auth_header

_NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def _lesson(
    order: int, *, author: LessonAuthor = LessonAuthor.HUMAN, approved: bool = True
) -> Lesson:
    # A human lesson is inherently approved; an unapproved AI lesson is the publish blocker.
    lid = uuid.uuid4()
    return Lesson(
        id=lid,
        title=f"Lesson {order}",
        body="Body.",
        order=order,
        author=author,
        approved=approved if author is LessonAuthor.HUMAN else approved,
    )


def _tree(*lessons: Lesson, credit: CertificationCredit = CertificationCredit.NONE) -> CourseTree:
    return CourseTree(
        title="Sales Egoist",
        summary="The doctrine.",
        certification_credit=credit,
        modules=(CourseModule(id=uuid.uuid4(), title="Module 1", order=0, lessons=lessons),),
    )


# ---------------------------------------------------------------- pure service logic
def test_unapproved_ai_lessons_are_the_publish_blockers() -> None:
    ai_pending = _lesson(1, author=LessonAuthor.AI, approved=False)
    tree = _tree(_lesson(0), ai_pending)
    assert unapproved_ai_lessons(tree) == (ai_pending.title,)


def test_course_complete_needs_every_approved_lesson() -> None:
    a, b = _lesson(0), _lesson(1)
    tree = _tree(a, b)
    assert not is_course_complete(tree, frozenset({a.id}))
    assert is_course_complete(tree, frozenset({a.id, b.id}))
    # An empty course is never "complete".
    assert not is_course_complete(_tree(), frozenset())


# ---------------------------------------------------------------- authoring is admin-only
def test_authoring_is_admin_only(repo: Repository, alice: SeededConsultant) -> None:
    with pytest.raises(ScopeViolationError):
        repo.create_course(alice.principal, slug="x", title="X", summary="Y")


def test_http_non_admin_cannot_author(client, alice: SeededConsultant) -> None:
    resp = client.post(
        "/workbench/courses",
        json={"slug": "sales-egoist", "title": "Sales Egoist", "summary": "Doctrine."},
        headers=auth_header(alice),
    )
    assert resp.status_code == 403


# ------------------------------------------------------- author → publish → versions retained
def test_author_publish_and_versions_retained(repo: Repository, admin: SeededConsultant) -> None:
    repo.create_course(
        admin.principal, slug="sales-egoist", title="Sales Egoist", summary="Doctrine."
    )
    repo.save_course_draft(admin.principal, "sales-egoist", _tree(_lesson(0)))
    v1 = repo.publish_course(admin.principal, "sales-egoist", now=_NOW)
    assert v1.version == 1

    # Edit the draft and re-publish WITHOUT a redeploy — a new retained version.
    repo.save_course_draft(admin.principal, "sales-egoist", _tree(_lesson(0), _lesson(1)))
    v2 = repo.publish_course(admin.principal, "sales-egoist", now=_NOW)
    assert v2.version == 2

    versions = repo.list_course_versions(admin.principal, "sales-egoist")
    assert [v.version for v in versions] == [1, 2]  # v1 retained
    # Learners see the latest published version.
    latest = repo.get_published_course(admin.principal, "sales-egoist")
    assert latest.version == 2
    assert len(latest.tree.modules[0].lessons) == 2


def test_duplicate_slug_refused(repo: Repository, admin: SeededConsultant) -> None:
    repo.create_course(admin.principal, slug="dup", title="A", summary="B")
    with pytest.raises(ConflictError):
        repo.create_course(admin.principal, slug="dup", title="C", summary="D")


# -------------------------------------------------------- AI lesson approval gate (ADR-0009)
def test_ai_lesson_blocks_publication_until_approved(
    repo: Repository, admin: SeededConsultant
) -> None:
    ai = _lesson(0, author=LessonAuthor.AI, approved=False)
    repo.create_course(admin.principal, slug="ai-course", title="AI", summary="S")
    repo.save_course_draft(admin.principal, "ai-course", _tree(ai))

    # Refuses while the AI lesson is unapproved.
    with pytest.raises(ConflictError):
        repo.publish_course(admin.principal, "ai-course", now=_NOW)

    # Approve → now it publishes, and the published lesson records its approver.
    repo.approve_course_lesson(admin.principal, "ai-course", ai.id, now=_NOW)
    version = repo.publish_course(admin.principal, "ai-course", now=_NOW)
    published_lesson = version.tree.modules[0].lessons[0]
    assert published_lesson.approved is True
    assert published_lesson.approved_by_consultant_id == admin.principal.consultant_id


def test_http_ai_gate_returns_409(client, admin: SeededConsultant) -> None:
    client.post(
        "/workbench/courses",
        json={"slug": "ai-http", "title": "AI", "summary": "S"},
        headers=auth_header(admin),
    )
    ai = _lesson(0, author=LessonAuthor.AI, approved=False)
    draft = _tree(ai).model_dump(mode="json")
    assert (
        client.put("/workbench/courses/ai-http/draft", json=draft, headers=auth_header(admin))
    ).status_code == 200
    resp = client.post("/workbench/courses/ai-http/publish", headers=auth_header(admin))
    assert resp.status_code == 409


# ---------------------------------------------------------------- completion → coursework credit
def test_completing_all_lessons_credits_coursework(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    a, b = _lesson(0), _lesson(1)
    repo.create_course(admin.principal, slug="cw", title="CW", summary="S")
    repo.save_course_draft(
        admin.principal, "cw", _tree(a, b, credit=CertificationCredit.COURSEWORK)
    )
    repo.publish_course(admin.principal, "cw", now=_NOW)

    # Baseline: no coursework credit yet.
    before = repo.get_certification_record(alice.principal, alice.principal.consultant_id)
    assert before.coursework_complete is False

    repo.complete_lesson(alice.principal, "cw", a.id, now=_NOW)
    mid = repo.get_certification_record(alice.principal, alice.principal.consultant_id)
    assert mid.coursework_complete is False  # not all lessons done

    repo.complete_lesson(alice.principal, "cw", b.id, now=_NOW)
    after = repo.get_certification_record(alice.principal, alice.principal.consultant_id)
    assert after.coursework_complete is True  # credited via the existing path


def test_completing_a_lesson_twice_is_refused(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    a = _lesson(0)
    repo.create_course(admin.principal, slug="once", title="O", summary="S")
    repo.save_course_draft(admin.principal, "once", _tree(a))
    repo.publish_course(admin.principal, "once", now=_NOW)
    repo.complete_lesson(alice.principal, "once", a.id, now=_NOW)
    with pytest.raises(ConflictError):
        repo.complete_lesson(alice.principal, "once", a.id, now=_NOW)


# ---------------------------------------------------- rich lesson content (GRS-0190)
# The renderer's contract half: references are https-only and assets are non-empty AT THE CONTRACT,
# so malformed content is refused by existing validation rather than reaching a published version
# and having to be caught by the renderer.


def _rich_lesson() -> Lesson:
    from bcap_contracts.learning import LessonAsset, SourceRef, SourceRefKind

    return Lesson(
        id=uuid.uuid4(),
        title="Rich lesson",
        body=(
            "## A heading\n\nProse with **bold** and a [link](https://docs.openbb.co).\n\n"
            "- one\n- two"
        ),
        order=0,
        video_ref="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        references=(
            SourceRef(title="Platform docs", url="https://docs.openbb.co", kind=SourceRefKind.DOCS),
            SourceRef(
                title="The pivot", url="https://openbb.co/blog/pivot", kind=SourceRefKind.BLOG
            ),
            SourceRef(
                title="Repo",
                url="https://github.com/OpenBB-finance/OpenBB",
                kind=SourceRefKind.REPO,
            ),
        ),
        assets=(
            LessonAsset(
                caption="The barbell",
                alt="Two heavy ends joined by a thin bar",
                svg='<svg viewBox="0 0 10 10"><rect x="0" y="0" width="4" height="10" /></svg>',
            ),
        ),
    )


def test_a_rich_lesson_round_trips_through_save_publish_and_fetch(
    repo: Repository, admin: SeededConsultant
) -> None:
    repo.create_course(admin.principal, slug="rich", title="Rich", summary="s")
    repo.save_course_draft(admin.principal, "rich", _tree(_rich_lesson()))
    published = repo.publish_course(admin.principal, "rich", now=_NOW)
    lesson = published.tree.modules[0].lessons[0]
    assert lesson.video_ref == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert [r.url for r in lesson.references] == [
        "https://docs.openbb.co",
        "https://openbb.co/blog/pivot",
        "https://github.com/OpenBB-finance/OpenBB",
    ]
    assert lesson.assets[0].alt == "Two heavy ends joined by a thin bar"
    assert "## A heading" in lesson.body


def test_a_lesson_without_the_new_fields_still_publishes_and_serves(
    repo: Repository, admin: SeededConsultant
) -> None:
    # Every seeded course predates GRS-0190 and must be unaffected by it.
    repo.create_course(admin.principal, slug="plain", title="Plain", summary="s")
    repo.save_course_draft(admin.principal, "plain", _tree(_lesson(0)))
    published = repo.publish_course(admin.principal, "plain", now=_NOW)
    lesson = published.tree.modules[0].lessons[0]
    assert lesson.references == ()
    assert lesson.assets == ()
    assert lesson.video_ref is None


def test_a_non_https_reference_is_refused_by_the_contract(
    client, admin: SeededConsultant, repo: Repository
) -> None:
    repo.create_course(admin.principal, slug="badref", title="Bad", summary="s")
    draft = _tree(_lesson(0)).model_dump(mode="json")
    draft["modules"][0]["lessons"][0]["references"] = [
        {"title": "Downgraded", "url": "http://example.com", "kind": "docs"}
    ]
    assert (
        client.put(
            "/workbench/courses/badref/draft", json=draft, headers=auth_header(admin)
        ).status_code
        == 422
    )


def test_an_unknown_reference_kind_is_refused(
    client, admin: SeededConsultant, repo: Repository
) -> None:
    repo.create_course(admin.principal, slug="badkind", title="Bad", summary="s")
    draft = _tree(_lesson(0)).model_dump(mode="json")
    draft["modules"][0]["lessons"][0]["references"] = [
        {"title": "Odd", "url": "https://example.com", "kind": "podcast"}
    ]
    assert (
        client.put(
            "/workbench/courses/badkind/draft", json=draft, headers=auth_header(admin)
        ).status_code
        == 422
    )


def test_an_empty_asset_is_refused(client, admin: SeededConsultant, repo: Repository) -> None:
    repo.create_course(admin.principal, slug="badasset", title="Bad", summary="s")
    draft = _tree(_lesson(0)).model_dump(mode="json")
    draft["modules"][0]["lessons"][0]["assets"] = [{"caption": "c", "alt": "a", "svg": ""}]
    assert (
        client.put(
            "/workbench/courses/badasset/draft", json=draft, headers=auth_header(admin)
        ).status_code
        == 422
    )


def test_an_asset_without_alt_text_is_refused(
    client, admin: SeededConsultant, repo: Repository
) -> None:
    # Alt text is required and never derived: a diagram nobody can read is not accessible content.
    repo.create_course(admin.principal, slug="noalt", title="Bad", summary="s")
    draft = _tree(_lesson(0)).model_dump(mode="json")
    draft["modules"][0]["lessons"][0]["assets"] = [
        {"caption": "c", "alt": "", "svg": "<svg viewBox='0 0 1 1'></svg>"}
    ]
    assert (
        client.put(
            "/workbench/courses/noalt/draft", json=draft, headers=auth_header(admin)
        ).status_code
        == 422
    )
