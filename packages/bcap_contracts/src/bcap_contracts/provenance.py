"""Weight Provenance Records (Methodology §6).

Every number that is not a client input — λ, δ, w, α, α_L, θ, critical-module sets — carries a
provenance record: who set it, when, by what method, with what dispersion, and when it is next
reviewed. A coefficient without provenance is not loadable (ADR-0001 §3). This is what lets the
methods appendix state "weights expert-elicited [date], review due [date]" for every figure.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from bcap_contracts.common import WeightMethod


class WeightProvenanceRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    set_by: str = Field(min_length=1, description="Who set the weight (panel id or named expert).")
    set_on: date = Field(description="When it was set.")
    method: WeightMethod = Field(description="Elicitation method (§6).")
    dispersion: str = Field(
        min_length=1,
        description="Recorded dispersion across the panel (e.g. 'IQR 0.04', 'CR 0.07', "
        "'κ_w 0.81') — the spread that the stability interval (§7) is drawn from.",
    )
    review_due: date = Field(description="When this weight is next reviewed (§6 publication).")
    notes: str | None = Field(default=None, description="Optional rationale / dissent summary.")
