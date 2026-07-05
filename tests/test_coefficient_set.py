"""CoefficientSet invariant tests (ADR-0001 §3) — the load-time gate that kills D1–D7.

Construction enforces Σθ=1, α∈[0,1], and mandatory provenance. `validate_against` enforces
registry completeness and refuses empty dimensions.
"""

from __future__ import annotations

from datetime import date

import pytest
from bcap_contracts.assessments import CoefficientSet
from bcap_contracts.common import PowerLifecycleStage, WeightMethod
from bcap_contracts.provenance import WeightProvenanceRecord
from bcap_contracts.registry import (
    AnchorPoint,
    MetricDef,
    MissingKeyError,
    ModuleDef,
    NormalisationSpec,
    PowerDef,
    Registry,
    SubcomponentDef,
    UnknownKeyError,
)
from pydantic import ValidationError


def _prov(*families: str) -> dict[str, WeightProvenanceRecord]:
    record = WeightProvenanceRecord(
        set_by="panel-v1",
        set_on=date(2026, 7, 1),
        method=WeightMethod.SWING_WEIGHTING,
        dispersion="IQR 0.04",
        review_due=date(2027, 7, 1),
    )
    return {name: record for name in families}


def test_theta_must_sum_to_one() -> None:
    with pytest.raises(ValidationError):
        CoefficientSet(
            version="v1",
            methodology_version="1.0",
            theta_b=0.4,
            theta_p=0.4,
            theta_l=0.4,  # sums to 1.2
            alpha_l=0.7,
            provenance=_prov("theta", "alpha_l"),
        )


def test_alpha_out_of_range_rejected() -> None:
    # The prototype's seed α = 2.0 (defect D3) is not constructible.
    with pytest.raises(ValidationError):
        CoefficientSet(
            version="v1",
            methodology_version="1.0",
            theta_b=0.34,
            theta_p=0.33,
            theta_l=0.33,
            alpha_l=2.0,
            provenance=_prov("theta", "alpha_l"),
        )


def test_populated_family_without_provenance_rejected() -> None:
    with pytest.raises(ValidationError):
        CoefficientSet(
            version="v1",
            methodology_version="1.0",
            theta_b=0.34,
            theta_p=0.33,
            theta_l=0.33,
            alpha_l=0.7,
            w_power={"SCALE_ECONOMIES": 1.0},  # populated but no 'w_power' provenance
            provenance=_prov("theta", "alpha_l"),
        )


def test_valid_coefficient_set_constructs() -> None:
    cs = _valid_theta_only()
    assert cs.theta_b + cs.theta_p + cs.theta_l == pytest.approx(1.0)


def test_validate_against_full_small_registry_passes() -> None:
    registry = _full_tiny_registry()
    cs = CoefficientSet(
        version="v1",
        methodology_version="1.0",
        theta_b=0.34,
        theta_p=0.33,
        theta_l=0.33,
        alpha_l=0.7,
        alpha_module={"M1": 0.6},
        lambda_loadings={"M1": {"M1_A": 0.5, "M1_B": 0.5}},
        delta={"M1": 1.0},
        critical_modules_for_l=("M1",),
        w_power={"P1": 1.0},
        w_metric={"K1": 1.0},
        provenance=_prov(
            "theta", "alpha_l", "alpha_module", "lambda", "delta", "w_power", "w_metric"
        ),
    )
    cs.validate_against(registry)  # must not raise


def test_validate_against_unknown_module_key_raises() -> None:
    registry = _full_tiny_registry()
    cs = CoefficientSet(
        version="v1",
        methodology_version="1.0",
        theta_b=0.34,
        theta_p=0.33,
        theta_l=0.33,
        alpha_l=0.7,
        delta={"M_TYPO": 1.0},  # the D1 class of bug
        provenance=_prov("theta", "alpha_l", "delta"),
    )
    with pytest.raises(UnknownKeyError):
        cs.validate_against(registry)


def test_validate_against_missing_module_key_raises() -> None:
    registry = _full_tiny_registry(two_modules=True)
    cs = CoefficientSet(
        version="v1",
        methodology_version="1.0",
        theta_b=0.34,
        theta_p=0.33,
        theta_l=0.33,
        alpha_l=0.7,
        delta={"M1": 1.0},  # M2 missing
        provenance=_prov("theta", "alpha_l", "delta"),
    )
    with pytest.raises(MissingKeyError):
        cs.validate_against(registry)


def test_validate_against_real_registry_missing_subcomponents_raises() -> None:
    from bcap_contracts.registry import load_registry

    # GRS-0002 populated the registry, so a coefficient set that covers the 9 modules and 7 powers
    # but leaves each module's λ empty no longer trips EmptyDimensionError — it fails loud with
    # MissingKeyError because the 51 registered subcomponents are not covered. Still a refusal.
    registry = load_registry()
    cs = CoefficientSet(
        version="v1",
        methodology_version="1.0",
        theta_b=0.34,
        theta_p=0.33,
        theta_l=0.33,
        alpha_l=0.7,
        delta={k: 1.0 for k in registry.module_keys()},
        alpha_module={k: 0.6 for k in registry.module_keys()},
        lambda_loadings={k: {} for k in registry.module_keys()},
        w_power={k: 1.0 for k in registry.power_keys()},
        provenance=_prov("theta", "alpha_l", "alpha_module", "lambda", "delta", "w_power"),
    )
    with pytest.raises(MissingKeyError):
        cs.validate_against(registry)


def test_validate_against_real_registry_full_coverage_passes() -> None:
    """A coefficient set that fully and correctly covers every populated registry dimension now
    validates against the real registry — proof the registry is internally consistent and
    coverable. (Uniform weights here; the real elicited weights arrive in GRS-0004.)"""
    from bcap_contracts.registry import load_registry

    registry = load_registry()
    cs = CoefficientSet(
        version="draft-coverage",
        methodology_version="1.0",
        theta_b=0.34,
        theta_p=0.33,
        theta_l=0.33,
        alpha_l=0.7,
        delta={k: 1.0 for k in registry.module_keys()},
        alpha_module={k: 0.6 for k in registry.module_keys()},
        lambda_loadings={
            k: {s: 1.0 for s in registry.subcomponent_keys(k)} for k in registry.module_keys()
        },
        w_power={k: 1.0 for k in registry.power_keys()},
        w_metric={k: 1.0 for k in registry.metric_keys()},
        provenance=_prov(
            "theta", "alpha_l", "alpha_module", "lambda", "delta", "w_power", "w_metric"
        ),
    )
    cs.validate_against(registry)  # must not raise


def _valid_theta_only() -> CoefficientSet:
    return CoefficientSet(
        version="v1",
        methodology_version="1.0",
        theta_b=0.34,
        theta_p=0.33,
        theta_l=0.33,
        alpha_l=0.7,
        provenance=_prov("theta", "alpha_l"),
    )


def _full_tiny_registry(two_modules: bool = False) -> Registry:
    modules = [
        ModuleDef(
            key="M1",
            name="Module 1",
            description="d",
            subcomponents=(
                SubcomponentDef(key="M1_A", name="A", module_key="M1", critical=True),
                SubcomponentDef(key="M1_B", name="B", module_key="M1"),
            ),
        )
    ]
    if two_modules:
        modules.append(
            ModuleDef(
                key="M2",
                name="Module 2",
                description="d",
                subcomponents=(SubcomponentDef(key="M2_A", name="A", module_key="M2"),),
            )
        )
    return Registry(
        powers=(
            PowerDef(
                key="P1",
                name="Power 1",
                lifecycle_stage=PowerLifecycleStage.TAKEOFF,
                description="d",
            ),
        ),
        modules=tuple(modules),
        metrics=(
            MetricDef(
                key="K1",
                name="Metric 1",
                unit="count",
                direction="higher_is_better",
                normalisation=NormalisationSpec(
                    anchors=(
                        AnchorPoint(raw=0, normalised=0.2),
                        AnchorPoint(raw=1, normalised=0.8),
                    )
                ),
            ),
        ),
    )
