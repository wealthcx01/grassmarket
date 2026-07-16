"""The ACTIVE scoring configuration — the single seam the panel-gated activation flips (GRS-0033).

Every runtime scoring path resolves its configuration here, so "which set is live" is decided in
exactly one place, not hardcoded at each router. There are TWO client-usability-gated artifacts and
both must flip together, or a client pack would carry a mismatched provenance (elicited weights,
draft uncertainty widths — ADR-0022):

- :func:`active_coefficient_set` — the §5 deterministic weights.
- :func:`active_uncertainty_model` — the §7 input-distribution widths (P10/P50/P90, tornado,
  weight-stability).

Both return the DRAFT (``client_usable=False``) artifact today: the engine runs and watermarked
internal drafts render, but the GRS-0015 gate keeps a client pack from being priced on placeholder
weights OR draft uncertainty widths.

Activating the elicited configuration (ADR-0022) is a one-line change to EACH function here — return
the ``elicited_v1_*`` artifact — gated on the weight-elicitation panel ratifying its values. It is a
deliberate, recorded flip, never automatic: no import side effect, no env toggle, no clock. Both
elicited artifacts already construct client-usable with full provenance and pass their golden
masters; the only thing missing is the panel's sign-off on the numbers. Flip both in one commit.
"""

from __future__ import annotations

from bcap_contracts.assessments import CoefficientSet
from bcap_contracts.registry import (
    RETAIL_PROFILE_KEY,
    Registry,
    load_profile,
    load_registry,
)
from bcap_contracts.uncertainty import UncertaintyModel

from grassmarket.atlas.draft_coefficients import (
    draft_exchange_coefficient_set,
    draft_v1_coefficient_set,
)
from grassmarket.atlas.montecarlo import draft_v1_uncertainty_model

_EXCHANGE_PROFILE_KEY = "exchange"


def profile_scoring_context(
    profile_key: str = RETAIL_PROFILE_KEY,
) -> tuple[Registry, CoefficientSet]:
    """Resolve the (registry VIEW, coefficient set) an assessment scores against for an operating-
    model profile (ADR-0025). The retail default view is byte-identical to the full registry, so the
    golden master and every existing retail assessment are unchanged. Retail routes through
    :func:`active_coefficient_set` (the client-usability activation seam); the exchange profile uses
    its own draft set with exchange criticals. An unknown profile key fails loud (ADR-0001)."""
    view = load_registry().for_profile(load_profile(profile_key))
    if profile_key == _EXCHANGE_PROFILE_KEY:
        return view, draft_exchange_coefficient_set(view)
    return view, active_coefficient_set(view)


def active_coefficient_set(registry: Registry) -> CoefficientSet:
    """Return the coefficient set the platform scores with right now.

    Draft until the panel ratifies the elicited values (ADR-0022). Callers must route every
    scoring/deliverable path through here so the future activation is a single-point change.
    """
    return draft_v1_coefficient_set(registry)


def active_uncertainty_model() -> UncertaintyModel:
    """Return the §7 uncertainty model the platform draws ranges from right now.

    Draft until the panel ratifies the elicited widths (ADR-0022) — flipped in the same reviewed
    commit as :func:`active_coefficient_set`, so a client pack never mixes elicited weights with
    draft uncertainty widths. Callers must route every uncertainty/deliverable path through here.
    """
    return draft_v1_uncertainty_model()
