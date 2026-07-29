"""Routes retired under ADR-0041 (the founder review gate, GRS-0188).

Peer rating requests, Rating Committee sign-off and calibration sessions were built for a network
larger than this one. The founder signs what goes out instead. The machinery behind these routes —
the repository sections, the tables, the kappa/AC1 stats engine — is untouched and still unit
tested, so reversing this is re-mounting the routers, not rebuilding the feature.

A retired route answers **410 Gone**, not 404. A stale client deserves to be told the feature was
withdrawn and why, rather than left to guess whether it mistyped a URL.
"""

from __future__ import annotations

from fastapi import HTTPException, status

RETIRED_DETAIL = (
    "Retired under ADR-0041 (founder review gate). Peer rating, committee sign-off and calibration "
    "are dormant, not deleted; client drafts are approved by the founder reviewer instead."
)


def retired_route() -> None:
    """A router-level dependency: every route under it refuses before any handler runs."""
    raise HTTPException(status_code=status.HTTP_410_GONE, detail=RETIRED_DETAIL)
