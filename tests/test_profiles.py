"""GRS-0077 — the operating-model profile mechanism (ADR-0025). A profile is a validated VIEW over
the registry superset. The load-bearing invariant: the **retail** profile's view is byte-identical
to the full registry, so the golden master reproduces. The mechanism is fail-loud (ADR-0001): an
unknown selected module, an addition to an unselected module, or an override of a subcomponent not
in the view all refuse."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from bcap_contracts.registry import (
    AnchorPoint,
    MetricDef,
    NormalisationSpec,
    ProfileDef,
    RegistryError,
    SubcomponentDef,
    UnknownKeyError,
    load_profile,
    load_profiles,
    load_registry,
)

from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set
from grassmarket.atlas.engine import score
from tests.test_atlas_engine_golden_master import _inputs_from_fixture

_FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "golden_master.json"


def _criticals(registry) -> dict[str, bool]:
    return {s.key: s.critical for m in registry.modules for s in m.subcomponents}


def test_retail_view_is_structurally_identical_to_the_superset() -> None:
    r = load_registry()
    view = r.for_profile(load_profile("retail"))
    assert [m.key for m in view.modules] == [m.key for m in r.modules]  # same modules, same order
    assert view.all_subcomponent_keys() == r.all_subcomponent_keys()
    assert _criticals(view) == _criticals(r)
    assert view.power_keys() == r.power_keys() and view.metric_keys() == r.metric_keys()


# --- GRS-0147 / ADR-0035: per-profile B-index metric selection --------------------------


def _metric(key: str) -> MetricDef:
    """A minimal well-formed profile metric addition for the mechanism tests."""
    return MetricDef(
        key=key,
        name=key.replace("_", " ").title(),
        description="A profile-specific metric for the mechanism test.",
        unit="percent",
        direction="higher_is_better",
        group="momentum",
        min_raw=0,
        normalisation=NormalisationSpec(
            anchors=(AnchorPoint(raw=0, normalised=0.1), AnchorPoint(raw=10, normalised=0.9))
        ),
    )


def test_profile_metric_selection_and_additions() -> None:
    r = load_registry()
    # Select two superset metrics and add one profile-specific metric. The view's B metrics are
    # exactly those three, superset-selected keys first (in superset order), then the addition.
    profile = ProfileDef(
        key="probe",
        name="Probe",
        module_keys=tuple(r.module_keys()),
        metric_keys=("AUA", "GROSS_MARGIN"),
        metric_additions=(_metric("PROBE_NNM_RATE"),),
    )
    view = r.for_profile(profile)
    assert view.metric_keys() == frozenset({"AUA", "GROSS_MARGIN", "PROBE_NNM_RATE"})
    # Superset order is preserved among the selected keys.
    keys = [m.key for m in view.metrics]
    assert keys[:2] == ["AUA", "GROSS_MARGIN"] and keys[-1] == "PROBE_NNM_RATE"


def test_profile_can_drop_all_superset_metrics() -> None:
    # metric_keys=() selects NONE of the superset — the view's B is entirely its own additions (the
    # wealth case: no retail AUA/ARPU). The superset itself is untouched (golden master safe).
    r = load_registry()
    profile = ProfileDef(
        key="probe",
        name="Probe",
        module_keys=tuple(r.module_keys()),
        metric_keys=(),
        metric_additions=(_metric("PROBE_A"), _metric("PROBE_B")),
    )
    view = r.for_profile(profile)
    assert view.metric_keys() == frozenset({"PROBE_A", "PROBE_B"})
    assert r.metric_keys() == load_registry().metric_keys()  # superset unchanged


def test_profile_metric_selection_is_fail_loud() -> None:
    r = load_registry()
    unknown = ProfileDef(
        key="probe", name="Probe", module_keys=tuple(r.module_keys()), metric_keys=("NOPE",)
    )
    with pytest.raises(UnknownKeyError):
        r.for_profile(unknown)
    # An addition may not shadow a superset metric key.
    shadow = ProfileDef(
        key="probe",
        name="Probe",
        module_keys=tuple(r.module_keys()),
        metric_additions=(_metric("AUA"),),
    )
    with pytest.raises(RegistryError):
        r.for_profile(shadow)


def test_a_profile_view_carries_the_c_dimension() -> None:
    # C (ADR-0023) is parallel to B/P/L — the profile view must carry the C modules/widgets, or the
    # wizard C step and the live C read would be silently empty for every profile-scoped assessment.
    r = load_registry()
    for profile_key in ("retail", "exchange"):
        view = r.for_profile(load_profile(profile_key))
        assert view.all_c_subcomponent_keys() == r.all_c_subcomponent_keys()
        assert view.widget_keys() == r.widget_keys()
    # The retail widget taxonomy stays retail-scoped in every view.
    exchange_view = r.for_profile(load_profile("exchange"))
    assert exchange_view.widgets_for_profile("exchange") == ()
    assert len(r.for_profile(load_profile("retail")).widgets_for_profile("retail")) == 93


def test_retail_profile_reproduces_the_golden_master() -> None:
    gm = json.loads(_FIXTURE.read_text())
    r = load_registry()
    view = r.for_profile(load_profile("retail"))
    coeffs = draft_v1_coefficient_set(view)
    result = score(_inputs_from_fixture(gm), coeffs, view)
    assert result.composite.v_index == 0.478565  # byte-identical to the ratified oracle


def test_for_profile_unknown_module_fails_loud() -> None:
    r = load_registry()
    with pytest.raises(UnknownKeyError):
        r.for_profile(ProfileDef(key="x", name="X", module_keys=("NOT_A_MODULE",)))


def test_addition_to_unselected_module_fails_loud() -> None:
    r = load_registry()
    add = SubcomponentDef(key="OEMS_EXTRA", name="Extra", module_key="OEMS")
    with pytest.raises(Exception, match="unselected module"):
        # Select only FRONTEND but add a subcomponent to OEMS → refused.
        r.for_profile(
            ProfileDef(key="x", name="X", module_keys=("FRONTEND",), subcomponent_additions=(add,))
        )


def test_override_of_absent_subcomponent_fails_loud() -> None:
    r = load_registry()
    with pytest.raises(UnknownKeyError):
        r.for_profile(
            ProfileDef(
                key="x",
                name="X",
                module_keys=("FRONTEND",),
                critical_overrides={"NOT_A_SUBCOMPONENT": True},
            )
        )


def test_a_partial_profile_view_validates_against_its_own_coefficient_set() -> None:
    # A profile selecting a strict subset of modules yields a coefficient set covering EXACTLY it.
    # (Include the L-critical modules so the uniform draft set's criticals are all present — a
    # subset that drops a critical module needs its own criticals, which is GRS-0078's job.)
    r = load_registry()
    subset = ProfileDef(key="sub", name="Subset", module_keys=("APP_SERVER", "BACKOFFICE", "OEMS"))
    view = r.for_profile(subset)
    assert {m.key for m in view.modules} == {"APP_SERVER", "BACKOFFICE", "OEMS"}
    coeffs = draft_v1_coefficient_set(view)
    coeffs.validate_against(view)  # exact coverage, fail-loud otherwise


def test_a_coefficient_set_referencing_a_module_outside_the_view_is_refused() -> None:
    # Per-profile completeness (ADR-0001): the retail draft set's criticals (incl. BACKOFFICE/OEMS)
    # can't validate against a view that excludes them — proving the profile view enforces coverage.
    r = load_registry()
    narrow = r.for_profile(ProfileDef(key="n", name="N", module_keys=("FRONTEND", "APP_SERVER")))
    retail_coeffs = draft_v1_coefficient_set(r)  # built for the full superset
    with pytest.raises(UnknownKeyError):
        retail_coeffs.validate_against(narrow)


def test_profiles_declare_retail() -> None:
    assert "retail" in load_profiles()


def test_profile_scoring_context_defaults_to_retail_and_reproduces_golden() -> None:
    from grassmarket.atlas.active import profile_scoring_context

    gm = json.loads(_FIXTURE.read_text())
    view, coeffs = profile_scoring_context()  # default = retail
    result = score(_inputs_from_fixture(gm), coeffs, view)
    assert result.composite.v_index == 0.478565
    # An unknown profile fails loud.
    with pytest.raises(UnknownKeyError):
        profile_scoring_context("no_such_profile")
