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
from collections.abc import Set as AbstractSet
from importlib import resources
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from bcap_contracts.common import PowerLifecycleStage


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
    critical: bool = False  # critical subcomponents drive the rating gate (§5.2)


class ModuleDef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    name: str
    description: str
    # Subcomponents are Loop 1 content (elicited). Empty until then — a coefficient set cannot
    # validate against a module with no subcomponents (EmptyDimensionError).
    subcomponents: tuple[SubcomponentDef, ...] = ()


class PowerDef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    name: str
    lifecycle_stage: PowerLifecycleStage
    description: str


class MetricDef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    name: str
    # Declared unit is captured in the UI, never inferred (Methodology §5.3). The full metric
    # register with normalisation specs is Loop 1 content.
    direction: str  # "higher_is_better" | "lower_is_better"


class Registry(BaseModel):
    """The whole legal key-space in one immutable object.

    Constructable directly (tests build small in-memory registries) or via
    :func:`load_registry` (reads the canonical YAML). The strict accessors below never default.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    powers: tuple[PowerDef, ...] = ()
    modules: tuple[ModuleDef, ...] = ()
    metrics: tuple[MetricDef, ...] = ()

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


# --- Canonical loader -------------------------------------------------------------------


def _load_yaml(filename: str) -> Any:
    data_pkg = resources.files("bcap_contracts").joinpath("registry_data")
    with resources.as_file(data_pkg.joinpath(filename)) as path:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)


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

    powers = tuple(PowerDef(**p) for p in powers_raw.get("powers", []))
    modules = tuple(
        ModuleDef(
            key=m["key"],
            name=m["name"],
            description=m["description"],
            subcomponents=tuple(SubcomponentDef(**s) for s in m.get("subcomponents", [])),
        )
        for m in modules_raw.get("modules", [])
    )
    metrics = tuple(MetricDef(**m) for m in metrics_raw.get("metrics", []))

    registry = Registry(powers=powers, modules=modules, metrics=metrics)
    _assert_unique_keys(registry)
    return registry


def _assert_unique_keys(registry: Registry) -> None:
    """Duplicate keys within a dimension are a load-time error, never a last-wins overwrite."""
    for dimension, keys in (
        ("power", [p.key for p in registry.powers]),
        ("module", [m.key for m in registry.modules]),
        ("metric", [m.key for m in registry.metrics]),
    ):
        seen: set[str] = set()
        for k in keys:
            if k in seen:
                raise RegistryError(f"Duplicate {dimension} key {k!r} in registry data.")
            seen.add(k)
    for m in registry.modules:
        seen_sub: set[str] = set()
        for s in m.subcomponents:
            if s.key in seen_sub:
                raise RegistryError(f"Duplicate subcomponent key {s.key!r} in module {m.key!r}.")
            seen_sub.add(s.key)
