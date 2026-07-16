"""Rubric anchor library tests (GRS-0008, Methodology §4).

The library is contract-typed storage with an ADR-0001 loader: every (subcomponent, level) pair is
present or explicitly TODO, unknown keys refuse, and an 'authored' anchor with no content refuses.
Content is John's to author; these tests gate the STRUCTURE, not the prose.
"""

from __future__ import annotations

import pytest
from bcap_contracts.common import MaturityLevel
from bcap_contracts.registry import (
    ModuleDef,
    Registry,
    SubcomponentDef,
    UnknownKeyError,
    load_registry,
)
from bcap_contracts.rubric import (
    AnchorStatus,
    DuplicateAnchorError,
    MissingAnchorError,
    RubricAnchor,
    RubricError,
    RubricLibrary,
    load_rubric_library,
)

_LEVELS = tuple(MaturityLevel)


def _tiny_registry() -> Registry:
    return Registry(
        modules=(
            ModuleDef(
                key="M1",
                name="M1",
                description="d",
                subcomponents=(SubcomponentDef(key="M1_A", name="A", module_key="M1"),),
            ),
        )
    )


def _todo(sub: str, level: MaturityLevel) -> RubricAnchor:
    return RubricAnchor(subcomponent_key=sub, level=level, status=AnchorStatus.TODO)


# --- The seeded library round-trips -----------------------------------------------------


def test_seeded_library_loads_all_204_anchors() -> None:
    lib = load_rubric_library()
    bpl_keys = load_registry().all_subcomponent_keys()
    bpl = [a for a in lib.anchors if a.subcomponent_key in bpl_keys]
    assert len(bpl) == 51 * 4 == 204  # the B/P/L set — C anchors (GRS-0081) are counted separately
    assert lib.status == "draft-pending-ratification"
    # Every anchor's level is a valid MaturityLevel; keys are registry-legal (the loader validated).
    assert all(a.level in _LEVELS for a in lib.anchors)


def test_seeded_library_has_the_authored_oems_example() -> None:
    lib = load_rubric_library()
    # The B/P/L library is fully authored: all 51 subcomponents × 4 levels = 204 authored anchors —
    # the §4 worked example (OEMS_EXEC_ALGOS), the 14 CRITICAL (★) subcomponents (first pass), and
    # the remaining 36 non-critical subcomponents (second pass, GRS-0008). C anchors are DRAFT, not
    # authored, so authored_count is exactly the B/P/L 204.
    assert lib.authored_count() == 204
    levels = lib.for_subcomponent("OEMS_EXEC_ALGOS")
    assert [a.level for a in levels] == list(_LEVELS)  # returned in rank order
    for a in levels:
        assert a.status is AnchorStatus.AUTHORED
        assert a.statement.strip()
        assert a.required_evidence and a.differentiator_questions and a.misgrading_notes


def test_seeded_authored_critical_subcomponent_is_complete() -> None:
    lib = load_rubric_library()
    # A CRITICAL subcomponent authored under GRS-0008 carries the full §4 template at every level.
    levels = lib.for_subcomponent("BACKOFFICE_CUSTODY")
    assert [a.level for a in levels] == list(_LEVELS)
    for a in levels:
        assert a.status is AnchorStatus.AUTHORED
        assert a.statement.strip()
        assert a.required_evidence and a.differentiator_questions and a.misgrading_notes


def test_seeded_non_critical_subcomponent_is_fully_authored() -> None:
    lib = load_rubric_library()
    # A non-critical subcomponent authored in the second pass (GRS-0008) now carries the full §4
    # template at every level — no TODO placeholder remains anywhere in the library.
    levels = lib.for_subcomponent("FRONTEND_DEVICE_COVERAGE")
    assert [a.level for a in levels] == list(_LEVELS)
    for a in levels:
        assert a.status is AnchorStatus.AUTHORED
        assert a.statement.strip()
        assert a.required_evidence and a.differentiator_questions and a.misgrading_notes
    # The whole library is authored — no explicit TODO pairs are left.
    assert not any(a.status is AnchorStatus.TODO for a in lib.anchors)


# --- Completeness & key refusals (validate_against) -------------------------------------


def test_complete_tiny_library_validates() -> None:
    lib = RubricLibrary(status="draft", anchors=tuple(_todo("M1_A", lvl) for lvl in _LEVELS))
    lib.validate_against(_tiny_registry())  # must not raise


def test_missing_level_is_a_load_time_refusal() -> None:
    # Only three of the four levels present → the fourth is silently missing → refusal.
    lib = RubricLibrary(status="draft", anchors=tuple(_todo("M1_A", lvl) for lvl in _LEVELS[:3]))
    with pytest.raises(MissingAnchorError):
        lib.validate_against(_tiny_registry())


def test_unknown_subcomponent_key_is_refused() -> None:
    lib = RubricLibrary(
        status="draft",
        anchors=(*(_todo("M1_A", lvl) for lvl in _LEVELS), _todo("M1_TYPO", MaturityLevel.BASIC)),
    )
    with pytest.raises(UnknownKeyError):
        lib.validate_against(_tiny_registry())


def test_duplicate_anchor_is_refused() -> None:
    lib = RubricLibrary(
        status="draft",
        anchors=(*(_todo("M1_A", lvl) for lvl in _LEVELS), _todo("M1_A", MaturityLevel.BASIC)),
    )
    with pytest.raises(DuplicateAnchorError):
        lib.validate_against(_tiny_registry())


def test_get_missing_pair_raises() -> None:
    lib = load_rubric_library()
    # Every registry pair exists, but an off-registry key is a miss.
    with pytest.raises(MissingAnchorError):
        lib.get("NOT_A_SUBCOMPONENT", MaturityLevel.BASIC)


# --- Anchor content invariants (construction-time) --------------------------------------


def test_authored_anchor_requires_a_statement() -> None:
    with pytest.raises(RubricError):
        RubricAnchor(
            subcomponent_key="M1_A",
            level=MaturityLevel.BASIC,
            status=AnchorStatus.AUTHORED,
            statement="   ",  # blank — a silently empty anchor
            required_evidence=("x",),
            differentiator_questions=("y",),
            misgrading_notes="z",
        )


def test_authored_anchor_requires_the_full_template() -> None:
    with pytest.raises(RubricError):
        RubricAnchor(
            subcomponent_key="M1_A",
            level=MaturityLevel.BASIC,
            status=AnchorStatus.AUTHORED,
            statement="A real statement.",
            # required_evidence / differentiators / misgrading_notes missing
        )


def test_todo_anchor_must_carry_no_content() -> None:
    with pytest.raises(RubricError):
        RubricAnchor(
            subcomponent_key="M1_A",
            level=MaturityLevel.BASIC,
            status=AnchorStatus.TODO,
            statement="content hiding behind a todo",
        )


def test_draft_anchor_needs_a_statement_but_not_the_full_template() -> None:
    a = RubricAnchor(
        subcomponent_key="M1_A",
        level=MaturityLevel.DEVELOPING,
        status=AnchorStatus.DRAFT,
        statement="A first-pass statement drafted from the label.",
    )
    assert a.status is AnchorStatus.DRAFT
