"""Engine result types — the full two-track output (Methodology v1.1 §5).

Every stored continuous value is rounded to 6 dp at the boundary (the display convention, ADR-0001
§4); the engine computes with full precision and rounds only here, so downstream terms (L from
q_m, V from B/P/L) never accumulate rounding. These models mirror the golden-master fixture field
for field — the fixture is the oracle the engine reproduces exactly (GRS-0004).
"""

from __future__ import annotations

from bcap_contracts.common import Score
from pydantic import BaseModel, ConfigDict


class SubcomponentRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    critical: bool
    level: str | None  # the maturity label if assessed, else None
    index: float | None  # the maturity index (0.2/0.5/0.8/1.0) if assessed, else None
    evidence: str | None
    state: str | None  # "Not Applicable" / "Not Assessed" if a non-score state, else None


class ModuleResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    name: str
    subcomponents: tuple[SubcomponentRow, ...]
    n_applicable: int
    n_assessed: int
    n_not_applicable: int
    coverage: float | None  # assessed / applicable; None if nothing applicable
    alpha: float
    weighted_avg: float | None
    min_term: float | None
    bottleneck_subcomponent: str | None
    q_m: Score | None  # None if the module has no assessed subcomponent — never 0.0 (D9)
    gate_band: str
    gate_blocked: bool
    gate_note: str


class LResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    weighted_term: Score
    min_term: Score
    value: Score


class CustomerResult(BaseModel):
    """The C-index (Customer Proposition, ADR-0023) — the L-shaped aggregation over the separate C
    registry dimension. `weighted_term` / `min_term` / `value` mirror `LResult`; `modules` carries
    the per-C-module detail (the proposition-heatmap source, GRS-0085). Present on an `AtlasResult`
    only when the coefficient set scores C. Stage 1: reported alongside V, never summed into it
    (that is v1.4 / GRS-0086)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    weighted_term: Score
    min_term: Score
    value: Score
    modules: tuple[ModuleResult, ...]


class MetricRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    raw: float | None
    unit: str
    direction: str
    group: str | None
    state: str | None
    n_k: Score | None


class BusinessResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metrics: tuple[MetricRow, ...]
    group_means: dict[str, Score]
    b_index: Score


class PowerRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    benefit: str
    barrier: str
    strength: str  # the weaker side (Helmer both-required)
    value: Score


class PowersResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    powers: tuple[PowerRow, ...]
    p_index: Score


class TriadDimensionResult(BaseModel):
    """Ordinal out (ADR-0002): `rating` is what a client sees; `score` is audit-only.

    `rating`/`score` are None when the dimension has no assessed source (e.g. Economic Value when
    no scale/unit-economics metric was entered) — Not Assessed, never a "None" moat floor. This
    mirrors the D9 discipline on `q_m`: unassessed is excluded, never zero-filled."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rating: str | None
    score: Score | None


class TriadResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    economic_value: TriadDimensionResult
    perceived_value: TriadDimensionResult
    defence_value: TriadDimensionResult


class CompositeResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    b_index: Score
    p_index: Score
    l_index: Score
    v_index: Score
    # C-index (ADR-0023 Stage 1): REPORTED alongside V, never summed into it until v1.4. None on a
    # B/P/L-only run — a missing C is first-class absence, never a zero (D9 discipline).
    c_index: Score | None = None


class AtlasResult(BaseModel):
    """The complete scoring output. `v_display_0_100` is the STORED (rounded) V × 100 — the display
    layer only ever scales the stored score (ADR-0001 §4)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    engine_version: str
    methodology_version: str
    coefficient_version: str
    modules: tuple[ModuleResult, ...]
    l_index: LResult
    business: BusinessResult
    powers: PowersResult
    triad: TriadResult
    # C-index detail (ADR-0023 Stage 1). None on a B/P/L-only run; present when the coefficient set
    # scores C. Reported alongside V — the composite V sum is unchanged (v1.4/GRS-0086 folds it in).
    customer: CustomerResult | None = None
    composite: CompositeResult
    gate_bands: dict[str, str]  # module_key → headline band (the two-track headline)
    v_display_0_100: float
