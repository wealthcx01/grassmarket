"""Product→gap fit map + sell-opportunity contracts (ADR-0039, GRS-0162).

`product_fit.yaml` records which registry gaps (infrastructure modules, C modules, powers) each
represented product addresses — authored commercial judgment as configuration, never runtime
string-matching over course prose. `load_product_fit()` validates the whole map at load (fail
loud, ADR-0001): unknown product, unknown key, a product addressing nothing, or a catalogue
product with no authored fit all refuse to load.

The `SellOpportunity` resources are the API surface of the deterministic sell-from-report join:
per product, the assessed-and-weak targets it addresses (a gap), the targets with no data yet
(never a gap — D9), and the live commission carrot displayed alongside. Ranking is score-track
only; commission never enters the ordering (ADR-0002).
"""

from __future__ import annotations

import functools
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.commissions import ProductCommissionCarrot, load_commission_config
from bcap_contracts.common import MaturityLevel, StrengthRating
from bcap_contracts.registry import load_registry


class ProductFitError(Exception):
    """The product-fit map is incomplete or malformed. Load-time refusal (fail loud)."""


class ProductFit(BaseModel):
    """One product's authored fit: the registry targets it addresses + the one-line pitch."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    modules: tuple[str, ...] = ()
    c_modules: tuple[str, ...] = ()
    powers: tuple[str, ...] = ()
    pitch: str = Field(min_length=1)


class ProductFitMap(BaseModel):
    """The whole map, keyed by product_id. Structural validation here; cross-registry /
    cross-catalogue validation happens in `load_product_fit` (where both are loadable)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = Field(min_length=1)
    products: dict[str, ProductFit]

    @model_validator(mode="after")
    def _every_product_addresses_something(self) -> ProductFitMap:
        for product_id, fit in self.products.items():
            if not (fit.modules or fit.c_modules or fit.powers):
                raise ProductFitError(
                    f"product_fit.yaml: {product_id!r} addresses no modules, c_modules, or "
                    "powers. A product with genuinely no fit must be removed from the catalogue, "
                    "not left silently unmatchable."
                )
        return self


@functools.lru_cache(maxsize=1)
def load_product_fit() -> ProductFitMap:
    """Load + validate the fit map once. Fails loud when a product id is not in the commission
    catalogue, a catalogue product has no authored fit, or any key is unknown to the registry."""
    from bcap_contracts.commissions import _load_yaml  # same registry_data loader

    raw = _load_yaml("product_fit.yaml")
    if not isinstance(raw, dict):
        raise ProductFitError("product_fit.yaml must be a mapping.")
    fit_map = ProductFitMap.model_validate(raw)

    catalogue = set(load_commission_config().products)
    unknown_products = set(fit_map.products) - catalogue
    if unknown_products:
        raise ProductFitError(
            f"product_fit.yaml names products not in commissions.yaml: "
            f"{sorted(unknown_products)}."
        )
    missing_products = catalogue - set(fit_map.products)
    if missing_products:
        raise ProductFitError(
            f"product_fit.yaml is missing catalogue products: {sorted(missing_products)}. "
            "Every represented product needs an authored fit (an explicit decision, ADR-0039)."
        )

    registry = load_registry()
    for product_id, fit in fit_map.products.items():
        # A fit is a SUBSET of the registry (a product addresses some targets, not all), so the
        # check is unknown-key refusal — not the exact-coverage rule coefficient sets use.
        for dimension, legal, supplied in (
            ("modules", registry.module_keys(), fit.modules),
            ("c_modules", registry.c_module_keys(), fit.c_modules),
            ("powers", registry.power_keys(), fit.powers),
        ):
            unknown = set(supplied) - legal
            if unknown:
                raise ProductFitError(
                    f"product_fit.yaml: {product_id!r} {dimension} name unknown registry "
                    f"key(s) {sorted(unknown)}."
                )
    return fit_map


# --- Sell-opportunity API resources (the deterministic join's output) ----------------------------


class GapKind(StrEnum):
    MODULE = "module"
    C_MODULE = "c_module"
    POWER = "power"


class OpportunityGap(BaseModel):
    """One assessed-and-weak target a product addresses. A module gap carries its q_m + gate band;
    a power gap carries the benefit/barrier strengths. Not Assessed never appears here (D9) — it
    is reported on the opportunity's `not_yet_assessed` list instead."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: GapKind
    key: str
    name: str
    q_m: float | None = Field(default=None, ge=0.0, le=1.0)
    gate_band: MaturityLevel | None = None
    benefit: StrengthRating | None = None
    barrier: StrengthRating | None = None


class SellOpportunity(BaseModel):
    """One recommended product: the gaps it addresses in THIS assessment, ranked evidence first,
    with the live commission carrot displayed alongside (never part of the ordering, ADR-0002)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    product_id: str
    name: str
    pitch: str
    gaps: tuple[OpportunityGap, ...]
    # Addressed targets with no data yet — surfaced honestly, never counted as gaps (D9).
    not_yet_assessed: tuple[str, ...] = ()
    carrot: ProductCommissionCarrot


class SellOpportunities(BaseModel):
    """The full advisor-facing answer to "what do I sell against this report?" for one finalised
    assessment. Advisor-facing ONLY — never rendered into a client deliverable (ADR-0039)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assessment_id: UUID
    subject: str
    opportunities: tuple[SellOpportunity, ...]
    fit_version: str
    coefficient_version: str
    schedule_version: str
