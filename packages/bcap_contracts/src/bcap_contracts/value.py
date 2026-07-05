"""The value layer — scenario prioritisation (score domain) and the value bridge (currency domain).

ADR-0002 is the whole design here: score-points and currency **never meet in one equation**. This
module keeps them in separate types and separate objects:

- **Scenario prioritisation** (`ScenarioResult`, `UpgradePriority`) lives wholly in the SCORE domain
  — ΔV from full re-scoring, ranked. There is no κ, no LV formula, no score×currency term (that was
  prototype defect D2).
- **The value bridge** (`ValueBridge`) prices in CURRENCY — a cost layer and a lever-NPV layer, both
  `Money`, plus a strategic layer that is **ordinal, never a decimal**. Every `Money` figure is
  traceable to a client-supplied baseline in the `AssumptionRegister`; a bridge whose figures cite a
  missing assumption refuses to construct.

No type in this module carries both a `Score` and a `Money`.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.common import Score, StrengthRating
from bcap_contracts.money import Money

# --- Scenario prioritisation (SCORE domain) ---------------------------------------------


class ScenarioResult(BaseModel):
    """One scenario evaluated by full re-scoring (Methodology §10). Prioritisation is score-domain:
    ΔV is the difference of two `score()` runs, never anything touching currency."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    baseline_v: Score
    scenario_v: Score
    delta_v: float  # signed difference of two [0,1] scores — not itself a Score
    delta_l: float
    delta_b: float
    delta_p: float


class UpgradePriority(BaseModel):
    """A ranked entry in the Upgrade Priority Index — scenarios ordered by ΔV (descending). The
    index RANKS in the score domain; the bridge PRICES in currency; the two are never divided."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    delta_v: float
    rank: int = Field(ge=1)


# --- The value bridge (CURRENCY / ORDINAL domains) --------------------------------------


class Assumption(BaseModel):
    """One client-supplied baseline figure that a value-bridge number is traceable to (Methodology
    §10). Every `Money` in the bridge cites an assumption `ref`; nothing is a bare number."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ref: str = Field(
        min_length=1, description="Stable id a Money.assumption_register_ref points to."
    )
    description: str = Field(min_length=1)
    baseline_value: float = Field(description="The client-supplied baseline in the stated unit.")
    unit: str = Field(min_length=1)
    source: str = Field(min_length=1, description="Where the client-supplied baseline came from.")


class AssumptionRegister(BaseModel):
    """The typed register of client-supplied baselines behind a value bridge. Refs are unique."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entries: tuple[Assumption, ...] = ()

    @model_validator(mode="after")
    def _unique_refs(self) -> AssumptionRegister:
        refs = [a.ref for a in self.entries]
        if len(refs) != len(set(refs)):
            raise ValueError("AssumptionRegister refs must be unique.")
        return self

    def refs(self) -> frozenset[str]:
        return frozenset(a.ref for a in self.entries)

    def get(self, ref: str) -> Assumption:
        for a in self.entries:
            if a.ref == ref:
                return a
        raise KeyError(f"No assumption {ref!r} in the register (traceability is mandatory, §10).")


class LeverKind(StrEnum):
    """The evidenced cash-flow levers an upgrade maps to (Methodology §10, layer 2)."""

    COST_TO_SERVE = "cost_to_serve"
    PROJECT_DRAG = "project_drag"
    INCIDENT_EXPECTED_LOSS = "incident_expected_loss"
    REVENUE_ENABLEMENT = "revenue_enablement"


class CostEstimate(BaseModel):
    """Layer 1 — the hard remediation/upgrade cost, in currency (Methodology §10)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total: Money
    assumption_refs: tuple[str, ...] = Field(min_length=1)
    note: str | None = None


class LeverValuation(BaseModel):
    """Layer 2 — one evidenced lever's risk-adjusted NPV (currency), traceable to its baselines."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lever: LeverKind
    npv: Money
    assumption_refs: tuple[str, ...] = Field(min_length=1)
    note: str | None = None


class StrategicRating(BaseModel):
    """Layer 3 — a moat/durability implication as an ORDINAL rating (never a decimal, ADR-0002)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dimension: str = Field(min_length=1)
    rating: StrengthRating
    rationale: str = Field(min_length=1)


class ValueBridge(BaseModel):
    """The three-layer value bridge (Methodology §10): cost (Money) · levers (Money) · strategic
    (ordinal), sharing one assumption register. Every Money figure must resolve to a register entry
    — a bridge citing a missing assumption refuses to construct (traceability, §10)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subject: str
    assumption_register: AssumptionRegister
    cost: CostEstimate
    levers: tuple[LeverValuation, ...]
    strategic: tuple[StrategicRating, ...]

    @model_validator(mode="after")
    def _every_figure_is_traceable(self) -> ValueBridge:
        legal = self.assumption_register.refs()
        cited: set[str] = set()
        cited.add(self.cost.total.assumption_register_ref)
        cited.update(self.cost.assumption_refs)
        for lever in self.levers:
            cited.add(lever.npv.assumption_register_ref)
            cited.update(lever.assumption_refs)
        missing = cited - legal
        if missing:
            raise ValueError(
                f"Value-bridge figures cite assumptions not in the register: {sorted(missing)}. "
                f"Every currency figure must trace to a client-supplied baseline (Methodology §10)."
            )
        return self

    def total_lever_npv(self) -> Money:
        """Sum the lever NPVs — Money + Money only, never touching a Score (ADR-0002)."""
        if not self.levers:
            raise ValueError("No levers to total.")
        total = self.levers[0].npv
        for lever in self.levers[1:]:
            total = total.add(lever.npv)
        return total
