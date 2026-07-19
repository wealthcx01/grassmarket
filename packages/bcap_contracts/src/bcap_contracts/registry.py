"""The single key registry — ADR-0001's core mechanism.

There is ONE registry of the legal keys for every dimension the engine names: modules,
subcomponents, powers, business metrics. It is data loaded once at startup, not scattered
literals. Contracts validate against it and (Loop 1) the engine reads it — the *same* object,
so the contract copy and the engine copy cannot drift (drift was defect D1).

**An unknown key is a refusal to score, not a default.** Lookups here are `d[key]` (raising,
re-raised as a typed `UnknownKeyError`) or explicit membership checks that raise. There is no
`.get(key, default)` anywhere on this path. This is the single most important line of defence
against feasibility defects D1–D7 — a key mismatch cannot produce a plausible wrong number
because it cannot produce a number at all.
"""

from __future__ import annotations

import functools
import math
from collections.abc import Set as AbstractSet
from importlib import resources
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.common import PowerLifecycleStage

# --- Closed key-like value sets (ADR-0001: a typo is a load-time refusal, never a default) -----
# These are the legal *values* of the key-like string fields on registry entries. They are closed
# sets: a value outside them is a typo and must refuse to load, exactly as an unknown key does.
# Encoded as Literal types so Pydantic rejects a stray value at construction and the JSON Schema /
# TS mirror carries the enum (schemas win, non-negotiable #4).
MetricDirection = Literal["higher_is_better", "lower_is_better"]
NormalisationMethod = Literal["piecewise_linear", "percentile"]
MetricGroup = Literal["scale", "unit_economics", "momentum"]


class RegistryError(Exception):
    """Base class for every registry failure. Never swallowed."""


class UnknownKeyError(RegistryError):
    """A key that is absent from the registry was used. Refusal to score, not a default."""

    def __init__(self, dimension: str, key: str, legal: AbstractSet[str]) -> None:
        self.dimension = dimension
        self.key = key
        legal_list = ", ".join(sorted(legal)) or "<none registered>"
        super().__init__(
            f"Unknown {dimension} key {key!r}. Legal {dimension} keys: {legal_list}. "
            f"An unknown key is a refusal to score, never a default (ADR-0001)."
        )


class MissingKeyError(RegistryError):
    """A registered key that MUST be covered was not supplied. Refusal to score."""

    def __init__(self, dimension: str, missing: AbstractSet[str]) -> None:
        self.dimension = dimension
        self.missing = missing
        super().__init__(
            f"Coefficient set is missing required {dimension} key(s): "
            f"{', '.join(sorted(missing))}. Every registered key for a populated dimension must "
            f"be covered (ADR-0001) — refusing to validate."
        )


class EmptyDimensionError(RegistryError):
    """A coefficient set was validated against a registry dimension with no entries yet.

    Per ADR-0001 scope note: the loader refuses to validate a coefficient set against an empty
    dimension (it does not pass it). The 9 modules × 51 subcomponents and the business-metric
    register are authored in Loop 1; until then this refusal fires loudly.
    """

    def __init__(self, dimension: str) -> None:
        self.dimension = dimension
        super().__init__(
            f"Refusing to validate against empty registry dimension {dimension!r}: no keys are "
            f"registered yet (Loop 1 content). A coefficient set cannot cover an empty dimension."
        )


# --- Registry entry types ---------------------------------------------------------------


class SubcomponentDef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    name: str
    module_key: str
    description: str | None = None
    critical: bool = False  # critical subcomponents drive the rating gate (§5.2)


class ModuleDef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    name: str
    description: str
    # Populated with the 51-subcomponent draft in GRS-0002 (status draft-pending-ratification).
    # A module with no subcomponents cannot be covered by a coefficient set (EmptyDimensionError).
    subcomponents: tuple[SubcomponentDef, ...] = ()


class PowerDef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    name: str
    lifecycle_stage: PowerLifecycleStage
    description: str


class AnchorPoint(BaseModel):
    """One point in a metric's normalisation curve: a raw value maps to a normalised score in
    [0,1] (Methodology §5.3). Anchor points are documented in the register, never inferred."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    raw: float = Field(description="A raw metric value in the metric's declared unit.")
    normalised: float = Field(ge=0.0, le=1.0, description="Its normalised score in [0,1].")


class NormalisationSpec(BaseModel):
    """The normalisation n_k for a business metric (Methodology §5.3).

    Stage 1 uses documented piecewise-linear anchor points; from Stage 2 (≥10 engagements) this
    becomes percentile-vs-benchmark-population. The prototype's unit-sensitive log heuristic
    (defect D5) is retired — the unit is declared, never inferred."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    method: NormalisationMethod = "piecewise_linear"  # closed set (Stage 2+ adds "percentile")
    anchors: tuple[AnchorPoint, ...] = ()
    note: str | None = None  # provenance / "placeholder pending judgement" markers

    @model_validator(mode="after")
    def _check_anchor_curve(self) -> NormalisationSpec:
        """The anchor curve is a well-formed monotone interpolation table — enforced on the SPEC,
        not on one golden-master test row (review). A malformed curve is a load-time refusal.

        - a ``piecewise_linear`` spec MUST carry anchors (an empty curve cannot normalise anything);
        - raw values are STRICTLY ASCENDING (interpolation needs distinct, ordered breakpoints);
        - normalised values are MONOTONIC (non-decreasing or non-increasing — never a zig-zag). The
          direction they move (up for higher_is_better, down for lower_is_better) is cross-checked
          against ``MetricDef.direction`` on the parent, which is where the direction lives.
        """
        if self.method == "piecewise_linear" and not self.anchors:
            raise RegistryError(
                "A piecewise_linear normalisation must declare at least one anchor."
            )
        if not self.anchors:
            return self
        raws = [a.raw for a in self.anchors]
        if any(b <= a for a, b in zip(raws, raws[1:], strict=False)):
            raise RegistryError(
                f"Normalisation anchors must be strictly ascending by raw; got {raws}."
            )
        norms = [a.normalised for a in self.anchors]
        non_decreasing = all(b >= a for a, b in zip(norms, norms[1:], strict=False))
        non_increasing = all(b <= a for a, b in zip(norms, norms[1:], strict=False))
        if not (non_decreasing or non_increasing):
            raise RegistryError(
                f"Normalisation anchors must be monotonic in normalised value; got {norms}."
            )
        return self


class MetricDef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    name: str
    # A plain-English "what it is and why it matters" for the wizard (GRS-0103). Single-sourced here
    # so the metrics step never renders a bare number without context; required (min length) so a
    # metric with no description is a load-time refusal, not an empty caption (ADR-0001).
    description: str = Field(min_length=1)
    # The declared unit is captured explicitly, never inferred (Methodology §5.3).
    unit: str
    direction: MetricDirection  # closed set: higher_is_better | lower_is_better
    # Metric group for the B index (ADR-0006): a closed set, or None until grouped. B is a
    # group-weighted mean, so collinear scale metrics don't quadruple-count (review B1). The group
    # ASSIGNMENTS are content (GRS-0003); this field + its closed set are registry machinery.
    group: MetricGroup | None = None
    # Required, not defaulted: a metric with no normalisation cannot be scored, so an omitted
    # normalisation is a load-time refusal (ADR-0001), not an empty placeholder that scores wrong.
    normalisation: NormalisationSpec
    # Input-domain bounds (GRS-0144, ADR-0035): a raw outside [min_raw, max_raw] is a nonsensical
    # value (e.g. a negative AUA) and is REFUSED, never clamped into the anchor curve. `None` = no
    # bound on that side, so a legitimately-signed metric (a margin or a growth rate that can go
    # negative) leaves `min_raw` None. A value inside the domain but past the anchors still clamps
    # (a valid-but-extreme firm) — the bound only rejects values that cannot exist for this metric.
    min_raw: float | None = None
    max_raw: float | None = None
    status: str = "settled"  # e.g. "draft-pending-ratification" for the Loop 1 draft register

    @model_validator(mode="after")
    def _bounds_are_sane(self) -> MetricDef:
        if self.min_raw is not None and self.max_raw is not None and self.min_raw > self.max_raw:
            raise RegistryError(
                f"Metric {self.key!r} has min_raw {self.min_raw} > max_raw {self.max_raw}."
            )
        return self

    def domain_violation(self, raw: float) -> str | None:
        """A fail-loud message if `raw` is outside this metric's declared domain, else None. Refuses
        a non-finite value (NaN/inf) and anything past an explicit bound — the engine must never
        score a value this returns non-None for (ADR-0001: refuse, never default/clamp around)."""
        if not math.isfinite(raw):
            return f"{self.name} must be a finite number (got {raw})."
        if self.min_raw is not None and raw < self.min_raw:
            return f"{self.name} can't be below {self.min_raw:g} {self.unit} (got {raw:g})."
        if self.max_raw is not None and raw > self.max_raw:
            return f"{self.name} can't be above {self.max_raw:g} {self.unit} (got {raw:g})."
        return None

    @model_validator(mode="after")
    def _normalisation_agrees_with_direction(self) -> MetricDef:
        """The anchor curve must slope the way ``direction`` says. NormalisationSpec guarantees the
        curve is monotonic; here — where both direction and the curve are visible — we refuse a
        curve whose slope contradicts the declared direction (a higher_is_better metric whose
        normalised score falls as raw rises is a data error, not a default to paper over)."""
        anchors = self.normalisation.anchors
        if len(anchors) < 2:
            return self
        norms = [a.normalised for a in anchors]
        rises = norms[-1] > norms[0]
        falls = norms[-1] < norms[0]
        if self.direction == "higher_is_better" and falls:
            raise RegistryError(
                f"Metric {self.key!r} is higher_is_better but its normalisation descends with raw."
            )
        if self.direction == "lower_is_better" and rises:
            raise RegistryError(
                f"Metric {self.key!r} is lower_is_better but its normalisation ascends with raw."
            )
        return self


class ProfileDef(BaseModel):
    """An operating-model profile (ADR-0025): a validated VIEW over the registry superset. It
    selects which module keys apply to this operating model, optionally adds profile-specific
    subcomponents, and may override a subcomponent's `critical` flag (an exchange need not treat
    `OEMS_*` as critical). The registry stays the superset; retail brokerage is the default profile
    and its view is byte-identical to the full registry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    name: str
    module_keys: tuple[str, ...]  # selected from the superset, in the superset's order at view time
    # Profile-specific subcomponents added into a selected module (globally-unique keys).
    subcomponent_additions: tuple[SubcomponentDef, ...] = ()
    # Override a subcomponent's global `critical` flag for this profile only (key -> critical).
    critical_overrides: dict[str, bool] = {}
    # Per-profile B-index metric selection (GRS-0147, ADR-0035). The B metrics are NOT one-size-
    # fits-all: an exchange isn't scored on AUA/ARPU, nor a wealth manager on take-rate. Two levers,
    # mirroring the module mechanism:
    #  - `metric_keys=None` (default) INHERITS the full superset — retail and exchange unchanged, so
    #    the golden master (which scores the retail view) is byte-identical.
    #  - `metric_keys=(...)` selects EXACTLY those superset metrics (an empty tuple = none of them,
    #    for a profile whose B is entirely its own additions).
    #  - `metric_additions=(...)` are profile-specific metrics not in the shared superset (e.g. the
    #    wealth net-new-money rate) — they live on the profile, never in the superset, so adding a
    #    profile can never change the retail metric set.
    metric_keys: tuple[str, ...] | None = None
    metric_additions: tuple[MetricDef, ...] = ()
    # Per-profile L-infrastructure content (GRS-0147d, ADR-0035). The 9-module taxonomy is
    # brokerage-shaped; a wealth manager's infra is custody, portfolio management, suitability, and
    # adviser tooling — not OEMS/watchlists/time-to-first-trade. To make the Infra Deep Dive read
    # segment-native WITHOUT changing the superset (golden master) or the module KEYS (so
    # scoring/scoreability that address modules by key still resolve), a profile can, per module:
    #  - `subcomponent_selection[module] = (...)` keep ONLY these superset subcomponents (an empty
    #    tuple drops all retail subs, leaving just this profile's `subcomponent_additions`);
    #  - `module_name_overrides[module] = "..."` rename the module for this operating model.
    # Both default empty ⇒ retail/exchange views are unchanged and the golden master is unaffected.
    subcomponent_selection: dict[str, tuple[str, ...]] = {}
    module_name_overrides: dict[str, str] = {}


WidgetRarity = Literal["Common", "Uncommon", "Rare"]


class CSubcomponentDef(BaseModel):
    """A Customer-Proposition (C) subcomponent (ADR-0023). Same shape as an L subcomponent — C rides
    the L aggregation family — but lives in the C keyspace."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    name: str
    module_key: str
    description: str | None = None
    critical: bool = False


class CModuleDef(BaseModel):
    """One of the 10 Phase-E Customer-Proposition modules (ADR-0023)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    name: str
    description: str
    subcomponents: tuple[CSubcomponentDef, ...] = ()


class WidgetDef(BaseModel):
    """One Level-1 customer-proposition widget (ADR-0023 / GRS-0080). The 93-widget checklist is C's
    Level-1 evidence layer: presence + ease/usability/depth per widget, differentiated by RARITY
    (a missing Common widget is a bottleneck; a Rare widget done well scores differentiation).
    `rarity` has no default — a missing/unknown value is a load-time refusal (ADR-0001)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    name: str
    category: str  # one of the 15 checklist categories
    rarity: WidgetRarity
    module_key: str  # the C module this widget informs


class Registry(BaseModel):
    """The whole legal key-space in one immutable object.

    Constructable directly (tests build small in-memory registries) or via
    :func:`load_registry` (reads the canonical YAML). The strict accessors below never default.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    powers: tuple[PowerDef, ...] = ()
    modules: tuple[ModuleDef, ...] = ()
    metrics: tuple[MetricDef, ...] = ()

    # Ratification status of the authored content. Powers are "settled" (Methodology §8); the
    # Loop 1 subcomponent set and metric register ship "draft-pending-ratification" until John
    # ratifies them and the elicitation panel runs (ADR-0001 scope note, GRS-0002 ticket).
    subcomponent_status: str = "settled"
    metric_status: str = "settled"

    # --- Customer-Proposition (C) section (ADR-0023 / GRS-0080). A PARALLEL dimension to B/P/L:
    # the engine's L path never iterates these, so the golden master is untouched (C rides alongside
    # V in Stage 1). The widget taxonomy is scoped to one operating-model profile (retail today).
    c_modules: tuple[CModuleDef, ...] = ()
    c_widgets: tuple[WidgetDef, ...] = ()
    c_status: str = "settled"
    c_widget_profile: str = "retail"  # the profile the widget taxonomy applies to

    # --- Key sets (frozen) ---
    def power_keys(self) -> frozenset[str]:
        return frozenset(p.key for p in self.powers)

    def module_keys(self) -> frozenset[str]:
        return frozenset(m.key for m in self.modules)

    def metric_keys(self) -> frozenset[str]:
        return frozenset(m.key for m in self.metrics)

    def subcomponent_keys(self, module_key: str) -> frozenset[str]:
        return frozenset(s.key for s in self.require_module(module_key).subcomponents)

    def all_subcomponent_keys(self) -> frozenset[str]:
        return frozenset(s.key for m in self.modules for s in m.subcomponents)

    # --- C key sets + accessors ---
    def c_module_keys(self) -> frozenset[str]:
        return frozenset(m.key for m in self.c_modules)

    def all_c_subcomponent_keys(self) -> frozenset[str]:
        return frozenset(s.key for m in self.c_modules for s in m.subcomponents)

    def c_subcomponent_keys(self, module_key: str) -> frozenset[str]:
        return frozenset(s.key for s in self.require_c_module(module_key).subcomponents)

    def widget_keys(self) -> frozenset[str]:
        return frozenset(w.key for w in self.c_widgets)

    def require_c_module(self, key: str) -> CModuleDef:
        for m in self.c_modules:
            if m.key == key:
                return m
        raise UnknownKeyError("c_module", key, self.c_module_keys())

    def widgets_for_profile(self, profile_key: str) -> tuple[WidgetDef, ...]:
        """The Level-1 widgets a profile is assessed against — the retail taxonomy is retail-only
        (ADR-0023). A non-retail profile sees no retail widgets (never scored against them)."""
        return self.c_widgets if profile_key == self.c_widget_profile else ()

    # --- Strict accessors: raise UnknownKeyError, never default ---
    def require_power(self, key: str) -> PowerDef:
        for p in self.powers:
            if p.key == key:
                return p
        raise UnknownKeyError("power", key, self.power_keys())

    def require_module(self, key: str) -> ModuleDef:
        for m in self.modules:
            if m.key == key:
                return m
        raise UnknownKeyError("module", key, self.module_keys())

    def require_metric(self, key: str) -> MetricDef:
        for m in self.metrics:
            if m.key == key:
                return m
        raise UnknownKeyError("metric", key, self.metric_keys())

    def require_subcomponent(self, module_key: str, subcomponent_key: str) -> SubcomponentDef:
        module = self.require_module(module_key)
        for s in module.subcomponents:
            if s.key == subcomponent_key:
                return s
        raise UnknownKeyError(
            f"subcomponent[{module_key}]", subcomponent_key, self.subcomponent_keys(module_key)
        )

    # --- Completeness assertions used by CoefficientSet.validate_against ---
    def assert_covers_keys(self, dimension: str, legal: frozenset[str], supplied: set[str]) -> None:
        """Supplied keys must be EXACTLY the legal set: no unknown key, no missing key, and the
        dimension must not be empty. This is the shared engine of ADR-0001 completeness."""
        if not legal:
            raise EmptyDimensionError(dimension)
        unknown = supplied - legal
        if unknown:
            # Report the first unknown with the full legal set for a helpful failure.
            raise UnknownKeyError(dimension, sorted(unknown)[0], legal)
        missing = legal - supplied
        if missing:
            raise MissingKeyError(dimension, missing)

    # --- Operating-model profile view (ADR-0025) ---
    def for_profile(self, profile: ProfileDef) -> Registry:
        """Return a new Registry that is this superset filtered to `profile`'s operating model:
        only the selected modules (in the superset's order), with any profile subcomponent
        additions and `critical` overrides applied. Powers and metrics (the B/P dimensions) are
        shared across profiles and pass through unchanged. Fail loud on an unknown selected module,
        an addition to an unselected module, or an override of a subcomponent not in the view.

        The retail profile selects every module with no additions/overrides, so its view is
        structurally identical to the full registry — the golden master is byte-identical."""
        unknown_modules = set(profile.module_keys) - set(self.module_keys())
        if unknown_modules:
            raise UnknownKeyError("profile module", sorted(unknown_modules)[0], self.module_keys())
        additions_by_module: dict[str, list[SubcomponentDef]] = {}
        for add in profile.subcomponent_additions:
            additions_by_module.setdefault(add.module_key, []).append(add)
        stray = set(additions_by_module) - set(profile.module_keys)
        if stray:
            raise RegistryError(
                f"Profile {profile.key!r} adds subcomponents to unselected module(s): "
                f"{sorted(stray)}."
            )
        # Per-module subcomponent selection / rename (GRS-0147d) may only target selected modules.
        stray_sel = set(profile.subcomponent_selection) - set(profile.module_keys)
        stray_name = set(profile.module_name_overrides) - set(profile.module_keys)
        if stray_sel or stray_name:
            raise RegistryError(
                f"Profile {profile.key!r} selects/renames subcomponents on unselected module(s): "
                f"{sorted(stray_sel | stray_name)}."
            )
        selected = set(profile.module_keys)
        new_modules: list[ModuleDef] = []
        view_sub_keys: set[str] = set()
        for module in self.modules:  # superset order preserved → retail view is byte-identical
            if module.key not in selected:
                continue
            # Keep either all the module's superset subcomponents, or — if this profile narrows the
            # module — only the selected ones (empty selection drops all retail subs), then append
            # this profile's additions. Fail loud on a selection naming a sub not in the module.
            if module.key in profile.subcomponent_selection:
                keep = set(profile.subcomponent_selection[module.key])
                unknown_sel = keep - {s.key for s in module.subcomponents}
                if unknown_sel:
                    raise UnknownKeyError(
                        f"profile[{profile.key}] subcomponent selection on {module.key}",
                        sorted(unknown_sel)[0],
                        frozenset(s.key for s in module.subcomponents),
                    )
                base_subs = [s for s in module.subcomponents if s.key in keep]
            else:
                base_subs = list(module.subcomponents)
            subs = base_subs + additions_by_module.get(module.key, [])
            resolved = tuple(
                s.model_copy(update={"critical": profile.critical_overrides[s.key]})
                if s.key in profile.critical_overrides
                else s
                for s in subs
            )
            view_sub_keys.update(s.key for s in resolved)
            update: dict[str, object] = {"subcomponents": resolved}
            if module.key in profile.module_name_overrides:
                update["name"] = profile.module_name_overrides[module.key]
            new_modules.append(module.model_copy(update=update))
        bad_overrides = set(profile.critical_overrides) - view_sub_keys
        if bad_overrides:
            raise UnknownKeyError(
                f"profile[{profile.key}] critical override", sorted(bad_overrides)[0], view_sub_keys
            )
        # Per-profile B metrics (GRS-0147): select from the superset (None ⇒ all, so retail/exchange
        # are unchanged) then append the profile's own additions. Superset order is preserved so the
        # retail view stays byte-identical. Fail loud on an unknown selected key or an addition that
        # shadows a superset metric.
        if profile.metric_keys is None:
            base_metrics = self.metrics
        else:
            selected_metrics = set(profile.metric_keys)
            unknown_metrics = selected_metrics - set(self.metric_keys())
            if unknown_metrics:
                raise UnknownKeyError(
                    f"profile[{profile.key}] metric", sorted(unknown_metrics)[0], self.metric_keys()
                )
            base_metrics = tuple(m for m in self.metrics if m.key in selected_metrics)
        addition_clash = {a.key for a in profile.metric_additions} & set(self.metric_keys())
        if addition_clash:
            raise RegistryError(
                f"Profile {profile.key!r} metric addition(s) {sorted(addition_clash)} shadow a "
                f"superset metric key."
            )
        view_metrics = base_metrics + profile.metric_additions
        view = Registry(
            powers=self.powers,
            modules=tuple(new_modules),
            metrics=view_metrics,
            subcomponent_status=self.subcomponent_status,
            metric_status=self.metric_status,
            # The C dimension (ADR-0023) is parallel to B/P/L — the profile selects B/P/L modules
            # only, so C passes through unchanged. The widget taxonomy stays retail-scoped via
            # `c_widget_profile`; a non-retail view won't match it (widgets_for_profile → ()).
            c_modules=self.c_modules,
            c_widgets=self.c_widgets,
            c_status=self.c_status,
            c_widget_profile=self.c_widget_profile,
        )
        _assert_unique_keys(view)  # additions must not clash with the superset (fail loud)
        return view


# --- Canonical loader -------------------------------------------------------------------


def _load_yaml(filename: str) -> Any:
    data_pkg = resources.files("bcap_contracts").joinpath("registry_data")
    with resources.as_file(data_pkg.joinpath(filename)) as path:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)


def _require(mapping: Any, key: str, context: str) -> Any:
    """Bracket-style required access: a missing key is a load-time refusal, never a default.

    This is the datasets' side of ADR-0001's fail-loud rule — the banned species is
    ``mapping.get(key, default)``, which lets an omitted field slip through as a plausible value.
    A dataset that forgets ``status:`` must refuse to load, not silently become ``"settled"``.
    """
    if not isinstance(mapping, dict) or key not in mapping:
        raise RegistryError(
            f"Required field {key!r} is missing from {context}. It must be supplied explicitly "
            f"(no default — ADR-0001)."
        )
    return mapping[key]


@functools.lru_cache(maxsize=1)
def load_registry() -> Registry:
    """Load the canonical registry from ``registry_data/*.yaml``, once, cached.

    Powers are settled content (Methodology §8). Modules ship as harvested structure with empty
    subcomponents; the full subcomponent set and the metric register are Loop 1 content. Loading
    is strict — malformed YAML or a bad entry raises at import-time, never a silent partial load.
    """
    powers_raw = _load_yaml("powers.yaml") or {}
    modules_raw = _load_yaml("modules.yaml") or {}
    metrics_raw = _load_yaml("metrics.yaml") or {}
    c_raw = _load_yaml("registry_c.yaml") or {}
    return _build_registry(powers_raw, modules_raw, metrics_raw, c_raw)


# The default operating-model profile: retail brokerage (the v1 taxonomy, byte-identical).
RETAIL_PROFILE_KEY = "retail"


@functools.lru_cache(maxsize=1)
def load_profiles() -> dict[str, ProfileDef]:
    """Load the operating-model profiles from ``registry_data/profiles.yaml`` (ADR-0025), once,
    cached. `status` and each profile's `name`/`modules` are REQUIRED (fail loud, bracket access);
    additions/overrides are genuinely optional. Profiles are validated against the registry lazily
    at :meth:`Registry.for_profile`, so this stays a pure config load."""
    raw = _load_yaml("profiles.yaml") or {}
    _require(raw, "status", "profiles.yaml")
    profiles_raw = _require(raw, "profiles", "profiles.yaml")
    profiles: dict[str, ProfileDef] = {}
    for key, body in profiles_raw.items():
        ctx = f"profiles.yaml[{key}]"
        profiles[key] = ProfileDef(
            key=key,
            name=_require(body, "name", ctx),
            module_keys=tuple(_require(body, "modules", ctx)),
            subcomponent_additions=tuple(
                SubcomponentDef(**s) for s in body.get("subcomponent_additions", [])
            ),
            critical_overrides=dict(body.get("critical_overrides", {})),
            # Per-profile B metrics (GRS-0147): `metrics` present ⇒ select those superset keys
            # (empty list = none); absent ⇒ None (inherit the full superset). `metric_additions` are
            # parsed exactly like superset metrics so a profile metric is a first-class MetricDef.
            metric_keys=tuple(body["metrics"]) if "metrics" in body else None,
            metric_additions=tuple(_parse_metric(m) for m in body.get("metric_additions", [])),
            # Per-module subcomponent selection + rename (GRS-0147d): make the infra taxonomy
            # segment-native without touching the superset or the module keys.
            subcomponent_selection={
                k: tuple(v) for k, v in body.get("subcomponent_selection", {}).items()
            },
            module_name_overrides=dict(body.get("module_name_overrides", {})),
        )
    if RETAIL_PROFILE_KEY not in profiles:
        raise RegistryError("profiles.yaml must declare the default 'retail' profile.")
    return profiles


def load_profile(key: str) -> ProfileDef:
    """A single operating-model profile, or fail loud on an unknown key (ADR-0001)."""
    profiles = load_profiles()
    if key not in profiles:
        raise UnknownKeyError("profile", key, frozenset(profiles))
    return profiles[key]


def _build_registry(
    powers_raw: dict[str, Any],
    modules_raw: dict[str, Any],
    metrics_raw: dict[str, Any],
    c_raw: dict[str, Any] | None = None,
) -> Registry:
    """Assemble a Registry from parsed YAML mappings. Split out from :func:`load_registry` so the
    fail-loud requirements (required ``status``, closed sets, anchor invariants) are unit-testable
    without round-tripping a temp file. ``status`` is REQUIRED on the module set and the metric
    set — a status-less dataset refuses to load (bracket access, not ``.get(..., "settled")``)."""
    powers = tuple(PowerDef(**p) for p in powers_raw.get("powers", []))
    modules = tuple(
        ModuleDef(
            key=m["key"],
            name=m["name"],
            description=m["description"],
            subcomponents=tuple(
                # module_key is injected from the parent — the YAML nests subcomponents under
                # their module, so it is never repeated per row (and cannot drift from it).
                SubcomponentDef(module_key=m["key"], **s)
                for s in m.get("subcomponents", [])
            ),
        )
        for m in modules_raw.get("modules", [])
    )
    metrics = tuple(_parse_metric(m) for m in metrics_raw.get("metrics", []))

    c_raw = c_raw or {}
    c_modules = tuple(
        CModuleDef(
            key=m["key"],
            name=m["name"],
            description=m["description"],
            subcomponents=tuple(
                CSubcomponentDef(module_key=m["key"], **s) for s in m.get("subcomponents", [])
            ),
        )
        for m in c_raw.get("c_modules", [])
    )
    # WidgetDef.rarity is a closed Literal with no default → a missing/unknown rarity refuses here.
    c_widgets = tuple(WidgetDef(**w) for w in c_raw.get("widgets", []))

    registry = Registry(
        powers=powers,
        modules=modules,
        metrics=metrics,
        subcomponent_status=_require(modules_raw, "status", "modules.yaml"),
        metric_status=_require(metrics_raw, "status", "metrics.yaml"),
        c_modules=c_modules,
        c_widgets=c_widgets,
        c_status=_require(c_raw, "status", "registry_c.yaml") if c_raw else "settled",
        c_widget_profile=c_raw.get("profile", "retail") if c_raw else "retail",
    )
    _assert_unique_keys(registry)
    return registry


def _parse_metric(raw: dict[str, Any]) -> MetricDef:
    key = raw.get("key", "<unknown>")
    norm_raw = _require(raw, "normalisation", f"metric {key!r}")
    normalisation = NormalisationSpec(
        method=norm_raw.get("method", "piecewise_linear"),
        anchors=tuple(AnchorPoint(**a) for a in norm_raw.get("anchors", [])),
        note=norm_raw.get("note"),
    )
    return MetricDef(
        key=raw["key"],
        name=raw["name"],
        description=_require(raw, "description", f"metric {key!r}"),
        unit=raw["unit"],
        direction=raw["direction"],
        group=raw.get("group"),  # optional: None until the metric is grouped (ADR-0006)
        normalisation=normalisation,
        # Input-domain bounds (GRS-0144): optional; absent ⇒ unbounded on that side (signed metric).
        min_raw=raw.get("min_raw"),
        max_raw=raw.get("max_raw"),
        status=_require(raw, "status", f"metric {key!r}"),
    )


def _assert_unique_keys(registry: Registry) -> None:
    """Duplicate keys within a dimension are a load-time error, never a last-wins overwrite."""
    for dimension, keys in (
        ("power", [p.key for p in registry.powers]),
        # B/P/L modules and C modules share one module keyspace (a C module can't shadow an L one).
        ("module", [m.key for m in registry.modules] + [m.key for m in registry.c_modules]),
        ("metric", [m.key for m in registry.metrics]),
    ):
        seen: set[str] = set()
        for k in keys:
            if k in seen:
                raise RegistryError(f"Duplicate {dimension} key {k!r} in registry data.")
            seen.add(k)
    # Subcomponent keys are GLOBALLY unique (not merely unique within a module). Now that every key
    # is fully qualified to <MODULE_KEY>_<LEAF> (GRS-0002a), a collision across modules would signal
    # a naming mistake — and the engine and coefficient sets address subcomponents by key alone, so
    # a global duplicate would let one shadow another. Refuse it at load time. C subcomponents and
    # widgets (ADR-0023) share this global keyspace with the B/P/L subcomponents.
    global_seen: dict[str, str] = {}
    for m in registry.modules:
        for s in m.subcomponents:
            if s.key in global_seen:
                raise RegistryError(
                    f"Duplicate subcomponent key {s.key!r} in module {m.key!r} — already defined "
                    f"in module {global_seen[s.key]!r}. Subcomponent keys must be globally unique."
                )
            global_seen[s.key] = m.key
    for m in registry.c_modules:
        for s in m.subcomponents:
            if s.key in global_seen:
                raise RegistryError(
                    f"Duplicate C subcomponent key {s.key!r} in C module {m.key!r} — already "
                    f"defined in {global_seen[s.key]!r}. Keys must be globally unique (ADR-0023)."
                )
            global_seen[s.key] = m.key
    for w in registry.c_widgets:
        if w.key in global_seen:
            raise RegistryError(
                f"Duplicate widget key {w.key!r} — already defined in {global_seen[w.key]!r}. "
                f"Widget keys must be globally unique (ADR-0023)."
            )
        global_seen[w.key] = f"widget[{w.category}]"
