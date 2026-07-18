"""AI-assisted wizard input (GRS-0101, ADR-0032).

A `WizardSuggestion` is a PROPOSAL the advisor sees while filling the assessment wizard — a nudge, a
consistency check, or a conservative prefill. It is never committed on its own: a `GUIDANCE`
suggestion carries no value, and a `PREFILL` value is applied only when the advisor explicitly
accepts (or edits) it, after which it is an ordinary document value that flows through the normal
§9/§8 gates. Every proposal references registry-valid keys (fail-loud) and the response is stamped
with the suggester version that produced it, mirroring the drafter-versioning on AI narratives
(ADR-0009).
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from bcap_contracts.common import MaturityLevel


class WizardSuggestionKind(StrEnum):
    """GUIDANCE points at a field to reconsider (no value); PREFILL proposes a concrete starting
    value the advisor accepts or edits."""

    GUIDANCE = "guidance"
    PREFILL = "prefill"


class WizardSuggestion(BaseModel):
    """One AI-proposed suggestion on a wizard input step. `id` is a stable key (so the UI can
    dismiss or de-dupe it). A PREFILL carries `proposed_level` for the (module_key,
    subcomponent_key) it targets; a GUIDANCE carries only the pointer + rationale."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    kind: WizardSuggestionKind
    step: str = Field(
        min_length=1, description="Wizard step key, e.g. 'powers' or 'infrastructure'."
    )
    title: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    # Target coordinates — all registry-valid. A PREFILL sets module_key + subcomponent_key +
    # proposed_level; a power consistency nudge sets power_key.
    module_key: str | None = None
    subcomponent_key: str | None = None
    power_key: str | None = None
    proposed_level: MaturityLevel | None = None


class WizardSuggestions(BaseModel):
    """The suggestion set for one assessment, stamped with the suggester version that produced it
    (so a suggestion is always attributable — the audit seam ADR-0009 established for AI output)."""

    model_config = ConfigDict(extra="forbid")

    assessment_id: UUID
    suggester_version: str = Field(min_length=1)
    suggestions: tuple[WizardSuggestion, ...] = ()
