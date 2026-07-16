"""GRS-0080 — the Customer-Proposition (C) registry section + 93-widget Level-1 layer (ADR-0023).

C is a PARALLEL dimension to B/P/L (its own `c_modules`/`c_widgets`), so the golden master is
untouched. Keys are globally unique across the keyspace, every widget carries a rarity, and the
retail widget taxonomy is retail-scoped — all fail-loud (ADR-0001)."""

from __future__ import annotations

import pytest
from bcap_contracts.registry import (
    RegistryError,
    WidgetDef,
    _build_registry,
    load_registry,
)
from pydantic import ValidationError

# The 10 Phase-E modules (ADR-0023), verbatim keys.
_PHASE_E = {
    "CUST_ONBOARDING",
    "CUST_UI_NAVIGATION",
    "CUST_TRADING_EXPERIENCE",
    "CUST_PRODUCT_RANGE",
    "CUST_RESEARCH_EDUCATION",
    "CUST_AI_PERSONALISATION",
    "CUST_SECURITY_REGULATION",
    "CUST_SUPPORT_COMMUNITY",
    "CUST_FEES_PRICING",
    "CUST_INNOVATION_DIFFERENTIATORS",
}


def test_c_section_loads_with_ten_modules_and_ninety_three_widgets() -> None:
    r = load_registry()
    assert {m.key for m in r.c_modules} == _PHASE_E
    assert len(r.c_widgets) == 93
    assert len({w.category for w in r.c_widgets}) == 15
    assert len(r.widget_keys()) == 93  # keys unique


def test_every_widget_has_a_rarity_and_maps_to_a_c_module() -> None:
    r = load_registry()
    c_modules = r.c_module_keys()
    for w in r.c_widgets:
        assert w.rarity in {"Common", "Uncommon", "Rare"}
        assert w.module_key in c_modules


def test_widget_taxonomy_is_retail_scoped() -> None:
    r = load_registry()
    assert r.c_widget_profile == "retail"
    assert len(r.widgets_for_profile("retail")) == 93
    assert r.widgets_for_profile("exchange") == ()  # a non-retail profile is never scored on them


def test_the_bpl_registry_and_golden_master_are_untouched() -> None:
    # C is a parallel dimension — the B/P/L module set is unchanged (the golden master reproduces in
    # tests/test_atlas_engine_golden_master.py; here we pin the structural invariant).
    r = load_registry()
    assert len(r.modules) == 9  # the 9 infrastructure (L) modules, unchanged
    # No C key leaks into the B/P/L subcomponent keyspace.
    assert not (r.all_c_subcomponent_keys() & r.all_subcomponent_keys())
    assert not (r.widget_keys() & r.all_subcomponent_keys())


def test_a_widget_with_an_unknown_rarity_fails_loud() -> None:
    with pytest.raises(ValidationError):  # the closed Literal rejects a stray value
        WidgetDef(key="X", name="X", category="Y", rarity="Sometimes", module_key="Z")  # type: ignore[arg-type]


def _c_raw(widgets: list[dict], c_modules: list[dict] | None = None) -> dict:
    return {
        "status": "draft-pending-ratification",
        "profile": "retail",
        "c_modules": c_modules
        or [
            {
                "key": "CUST_ONBOARDING",
                "name": "Onboarding",
                "description": "x",
                "subcomponents": [],
            }
        ],
        "widgets": widgets,
    }


def _min_registry(c_raw: dict):
    return _build_registry({}, {"status": "s"}, {"status": "s"}, c_raw)


def test_duplicate_widget_key_is_a_load_time_error() -> None:
    w = {"name": "W", "category": "C", "rarity": "Common", "module_key": "CUST_ONBOARDING"}
    with pytest.raises(RegistryError, match="Duplicate widget key"):
        _min_registry(_c_raw([{"key": "WDG_DUP", **w}, {"key": "WDG_DUP", **w}]))


def test_c_module_key_colliding_with_an_l_module_is_refused() -> None:
    # A C module key that shadows an L module key must fail loud (one module keyspace).
    c_raw = _c_raw(
        [],
        c_modules=[{"key": "FRONTEND", "name": "Clash", "description": "x", "subcomponents": []}],
    )
    with pytest.raises(RegistryError, match="Duplicate module key"):
        _build_registry(
            {},
            {
                "status": "s",
                "modules": [{"key": "FRONTEND", "name": "F", "description": "d"}],
            },
            {"status": "s"},
            c_raw,
        )


def test_registry_c_yaml_requires_a_status() -> None:
    with pytest.raises(RegistryError, match="status"):
        _build_registry({}, {"status": "s"}, {"status": "s"}, {"profile": "retail", "widgets": []})
