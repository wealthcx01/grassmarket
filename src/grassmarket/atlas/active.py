"""The ACTIVE scoring configuration — the single seam the founder/panel-gated activation flips.

Every runtime scoring path resolves its configuration here, so "which set is live" is decided in
exactly one place, not hardcoded at each router. There are TWO client-usability-gated artifacts and
both must flip together per profile, or a client pack would carry a mismatched provenance (elicited
weights, draft uncertainty widths — ADR-0022):

- :func:`profile_scoring_context` / :func:`active_coefficient_set` — the §5 deterministic weights.
- :func:`active_uncertainty_model` — the §7 input-distribution widths (P10/P50/P90, tornado,
  weight-stability).

**ACTIVATION STATE (founder-directed, 2026-07-20, ADR-0037/ADR-0022):**
- **wealth & exchange are ACTIVATED** — they score on their research-validated, client-usable
  ``elicited_{wealth,exchange}_coefficient_set`` (with the ADR-0038 critical-control cap) and the
  client-usable elicited §7 widths. The GRS-0015 gate now lets a client-facing wealth/exchange
  deliverable render. The weights are the engineering STARTER values the founder activated; formal
  panel ratification remains the scheduled review (provenance ``review_due``), not a blocker.
- **retail stays DRAFT** — ``active_coefficient_set`` still returns the draft set (retail's elicited
  set exists but is not activated), so retail is not client-usable and the golden master is intact.

Activation is per-profile and both seams flip together for the activated profile. It remains a
deliberate, recorded change here — no import side effect, no env toggle, no clock.
"""

from __future__ import annotations

from bcap_contracts.assessments import AssessmentDocument, CoefficientSet
from bcap_contracts.registry import (
    RETAIL_PROFILE_KEY,
    Registry,
    load_profile,
    load_registry,
)
from bcap_contracts.uncertainty import UncertaintyModel

from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set
from grassmarket.atlas.elicited_coefficients import (
    elicited_exchange_coefficient_set,
    elicited_wealth_coefficient_set,
)
from grassmarket.atlas.montecarlo import (
    draft_v1_uncertainty_model,
    elicited_v1_uncertainty_model,
)

_EXCHANGE_PROFILE_KEY = "exchange"
_WEALTH_PROFILE_KEY = "wealth"
# The operating-model profiles whose weights the founder has activated (ADR-0037). Their coefficient
# AND uncertainty seams both resolve to the client-usable elicited artifacts.
_ACTIVATED_PROFILES = frozenset({_EXCHANGE_PROFILE_KEY, _WEALTH_PROFILE_KEY})


def profile_key_of(document: AssessmentDocument) -> str:
    """The operating-model profile key an assessment document scores under (ADR-0025/GRS-0079).
    An unset `operating_model` means the retail default (byte-identical to v1)."""
    if document.profile is not None and document.profile.operating_model:
        return document.profile.operating_model
    return RETAIL_PROFILE_KEY


def profile_scoring_context(
    profile_key: str = RETAIL_PROFILE_KEY,
) -> tuple[Registry, CoefficientSet]:
    """Resolve the (registry VIEW, coefficient set) an assessment scores against for an operating-
    model profile (ADR-0025). The retail default view is byte-identical to the full registry, so the
    golden master and every existing retail assessment are unchanged. Retail routes through
    :func:`active_coefficient_set` (the client-usability activation seam); the exchange and wealth
    profiles use their own draft sets with profile-specific criticals + metrics. An unknown profile
    key fails loud (ADR-0001)."""
    view = load_registry().for_profile(load_profile(profile_key))
    if profile_key == _EXCHANGE_PROFILE_KEY:
        return view, elicited_exchange_coefficient_set(view)  # ACTIVATED (ADR-0037), client-usable
    if profile_key == _WEALTH_PROFILE_KEY:
        return view, elicited_wealth_coefficient_set(view)  # ACTIVATED (ADR-0037), client-usable
    return view, active_coefficient_set(view)


def active_coefficient_set(registry: Registry) -> CoefficientSet:
    """Return the coefficient set the platform scores with right now.

    Draft until the panel ratifies the elicited values (ADR-0022). Callers must route every
    scoring/deliverable path through here so the future activation is a single-point change.
    """
    return draft_v1_coefficient_set(registry)


def active_c_coefficient_set(registry: Registry) -> CoefficientSet | None:
    """The C-index coefficient set the platform reports C with today (ADR-0023 Stage 1).

    DRAFT, ``client_usable=False`` — C is reported ALONGSIDE V, never summed into it and never
    priced (that is v1.4 / GRS-0086). Returns None for a registry with no C dimension. This is the
    same single-point activation seam as :func:`active_coefficient_set`: when the θ_C panel ratifies
    the C weights, this returns the elicited C set instead — one reviewed change, no env toggle.
    """
    if not registry.c_modules:
        return None
    return draft_v1_coefficient_set(registry, score_c=True)


def active_uncertainty_model(profile_key: str = RETAIL_PROFILE_KEY) -> UncertaintyModel:
    """Return the §7 uncertainty model the platform draws ranges from right now, for `profile_key`.

    Flips together with the coefficient seam per profile (ADR-0022), so a client pack never mixes
    elicited weights with draft uncertainty widths. An **activated** profile (wealth/exchange) draws
    the client-usable elicited widths; every other profile (retail) draws the draft widths. The two
    models carry identical widths today, so this only moves the client-usability gate — no numerical
    change to any range — but keeping them paired lets the deliverable gate pass a client pack for
    an activated segment and refuse one for a draft segment. Callers pass the assessment's profile.
    """
    if profile_key in _ACTIVATED_PROFILES:
        return elicited_v1_uncertainty_model()
    return draft_v1_uncertainty_model()
