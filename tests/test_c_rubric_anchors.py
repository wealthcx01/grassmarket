"""GRS-0081 — C rubric anchors (ADR-0023). Every Customer-Proposition subcomponent carries a full
anchor set at all four maturity levels, so the fail-loud loader stays green and the wizard
(GRS-0083) can present guidance for C. Authored as DRAFT (statement from the §4 maturity ladder),
reconcile with the seven completed reviews. No B/P/L anchor is touched."""

from __future__ import annotations

import pytest
from bcap_contracts.common import MaturityLevel
from bcap_contracts.registry import load_registry
from bcap_contracts.rubric import (
    AnchorStatus,
    MissingAnchorError,
    RubricLibrary,
    load_rubric_library,
)


def test_every_c_subcomponent_has_a_full_anchor_set() -> None:
    lib = load_rubric_library()  # validates coverage on load (raises if any pair missing)
    r = load_registry()
    c_keys = r.all_c_subcomponent_keys()
    assert len(c_keys) == 39
    for key in c_keys:
        levels = {a.level for a in lib.for_subcomponent(key)}
        assert levels == set(MaturityLevel), f"{key} is missing a level"


def test_c_anchors_are_drafted_with_content() -> None:
    lib = load_rubric_library()
    c_keys = load_registry().all_c_subcomponent_keys()
    c_anchors = [a for a in lib.anchors if a.subcomponent_key in c_keys]
    assert len(c_anchors) == 156  # 39 subcomponents × 4 levels
    assert all(a.status is AnchorStatus.DRAFT for a in c_anchors)
    assert all(a.statement.strip() for a in c_anchors)  # draft ⇒ a real statement


def test_bpl_anchor_count_is_unchanged() -> None:
    lib = load_rubric_library()
    bpl_keys = load_registry().all_subcomponent_keys()
    bpl_anchors = [a for a in lib.anchors if a.subcomponent_key in bpl_keys]
    assert len(bpl_anchors) == 204  # 51 B/P/L subcomponents × 4 levels, untouched


def test_a_missing_c_anchor_is_a_load_time_error() -> None:
    # Drop the C anchors and re-validate → the loader refuses (C coverage is now required).
    lib = load_rubric_library()
    registry = load_registry()
    c_keys = registry.all_c_subcomponent_keys()
    without_c = RubricLibrary(
        status="test", anchors=tuple(a for a in lib.anchors if a.subcomponent_key not in c_keys)
    )
    with pytest.raises(MissingAnchorError):
        without_c.validate_against(registry)
