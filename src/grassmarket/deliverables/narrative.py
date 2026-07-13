"""AI narrative drafting (GRS-0017, ADR-0009). AI proposes; a human approves every word later.

The service depends on a `NarrativeDrafter` *port*, never on a concrete model SDK. The shipped
drafter, `TemplateNarrativeDrafter`, is deterministic and offline: it renders versioned in-repo
templates against facts derived from the finalised scoring run, so the whole flow is exercised in CI
with no live calls (CLAUDE.md: no live calls in CI). A Claude Agent SDK adapter can implement the
same Protocol later without touching feature code (ADR-0009).

Nothing here approves anything — a draft is only ever a PROPOSAL. Approval (human sign-off + edit
diff) is recorded through the repository; the client-usable gate refuses unapproved narratives.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import Protocol

from bcap_contracts.narratives import NarrativeSection

from grassmarket.atlas.results import AtlasResult
from grassmarket.deliverables.uncertainty_text import to_display

DRAFTER_VERSION = "template-drafter-v1"
PROMPT_TEMPLATE_VERSION = "narrative-templates-v1"


@dataclass(frozen=True)
class NarrativeContext:
    """The run-derived facts a drafter needs, on the 0–100 display scale. Score-domain only — a
    narrative interprets the assessment; it never prices (currency lives in the value bridge)."""

    subject: str
    v_index: float
    b_index: float
    p_index: float
    l_index: float
    economic_value: str
    perceived_value: str
    defence_value: str


def context_from_result(result: AtlasResult, subject: str) -> NarrativeContext:
    """Derive the drafting context from an immutable stored result — reproducible by design."""
    triad = result.triad
    composite = result.composite
    return NarrativeContext(
        subject=subject,
        v_index=to_display(composite.v_index),
        b_index=to_display(composite.b_index),
        p_index=to_display(composite.p_index),
        l_index=to_display(composite.l_index),
        economic_value=str(triad.economic_value.rating),
        perceived_value=str(triad.perceived_value.rating),
        defence_value=str(triad.defence_value.rating),
    )


class NarrativeDrafter(Protocol):
    """The port. An implementation turns run facts into proposed prose for one section. The output
    is always a PROPOSAL — approval is a separate, human step (ADR-0009)."""

    version: str
    prompt_template_version: str

    def draft(self, section: NarrativeSection, context: NarrativeContext) -> str: ...


# Versioned in-repo prompt templates. They double as the deterministic offline draft: a Claude Agent
# SDK adapter would send these as the prompt; the template drafter renders them directly.
_TEMPLATES: dict[NarrativeSection, str] = {
    NarrativeSection.INTERPRETATION: (
        "For {subject}, platform value V stands at {v_index:.1f} on the 0–100 scale, built from "
        "business performance B={b_index:.1f}, competitive powers P={p_index:.1f}, and platform "
        "infrastructure L={l_index:.1f}. The lowest of these is the binding constraint on V and is "
        "where remediation moves the headline number most."
    ),
    NarrativeSection.COMMENTARY: (
        "On the Platform Power triad, {subject} rates {economic_value} on Economic Value, "
        "{perceived_value} on Perceived Value, and {defence_value} on Defence Value. These are "
        "ordinal ratings — the words a client sees — read alongside, not divided into, the "
        "value-bridge pricing."
    ),
    NarrativeSection.RECOMMENDATION: (
        "The priority for {subject} is to lift the binding constraint behind V={v_index:.1f}: "
        "sequence the interventions with the highest Upgrade Priority Index first, and pair each "
        "with its value-bridge cost so the client sees priority and price side by side. This draft "
        "is a proposal for consultant review; it is not advice until approved."
    ),
}


class TemplateNarrativeDrafter:
    """The default, deterministic drafter (ADR-0009). Same context → same prose, every time — so a
    deliverable regenerates identically and CI needs no live model call."""

    version = DRAFTER_VERSION
    prompt_template_version = PROMPT_TEMPLATE_VERSION

    def draft(self, section: NarrativeSection, context: NarrativeContext) -> str:
        template = _TEMPLATES[section]  # subscript: an unknown section fails loud, never a default
        return template.format(
            subject=context.subject,
            v_index=context.v_index,
            b_index=context.b_index,
            p_index=context.p_index,
            l_index=context.l_index,
            economic_value=context.economic_value,
            perceived_value=context.perceived_value,
            defence_value=context.defence_value,
        )


def edit_summary(proposed: str, final: str) -> str:
    """A human-readable summary of the consultant's edits from the proposal to the approved text.
    Empty edits read as 'approved without edits' — the trail is explicit either way (§5)."""
    if proposed == final:
        return "approved without edits"
    diff = difflib.unified_diff(
        proposed.splitlines(),
        final.splitlines(),
        fromfile="proposed",
        tofile="final",
        lineterm="",
    )
    return "\n".join(diff)
