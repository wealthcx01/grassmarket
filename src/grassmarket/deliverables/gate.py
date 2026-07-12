"""The client-usable gate (GRS-0015) — the controlling non-negotiable of Loop 4.

A client-facing pack may **not** be generated from a CoefficientSet with ``client_usable=False``.
That is a runtime refusal, not a convention: until the elicited v1 set (``client_usable=True``,
founder task) lands, the builder may only emit clearly-watermarked "DRAFT — not client-usable"
internal documents. Never silently produce a client pack on draft coefficients.
"""

from __future__ import annotations

from bcap_contracts.assessments import CoefficientSet
from bcap_contracts.deliverables import DeliverableMode


class ClientUsabilityError(Exception):
    """A client-facing document was requested against a coefficient set that is not client-usable.
    A runtime refusal — the fail-safe that keeps a draft-weighted pack away from a client."""


DRAFT_WATERMARK = "DRAFT — not client-usable"


def resolve_mode(coefficients: CoefficientSet, *, client_facing: bool) -> DeliverableMode:
    """Decide the document mode, enforcing the gate.

    - ``client_facing=True`` on a client-usable set → CLIENT.
    - ``client_facing=True`` on a NON-client-usable set → **refusal** (``ClientUsabilityError``).
    - ``client_facing=False`` → DRAFT_INTERNAL (allowed on any set; always watermarked).
    """
    if client_facing:
        if not coefficients.client_usable:
            raise ClientUsabilityError(
                f"Refusing to generate a client-facing deliverable from coefficient set "
                f"'{coefficients.version}' (client_usable=False). Only a client-usable "
                f"(elicited/ratified) set may price a client pack; draft sets may emit "
                f"'{DRAFT_WATERMARK}' internal documents only."
            )
        return DeliverableMode.CLIENT
    return DeliverableMode.DRAFT_INTERNAL
