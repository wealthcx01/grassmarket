"""The peer-governance routes are retired (GRS-0188, ADR-0041).

Peer rating requests, Rating Committee sign-off and calibration sessions were built for a network
larger than this one. The founder signs what goes out instead.

**410 Gone, not 404.** A stale client deserves to be told the feature was withdrawn and why, rather
than left to wonder whether it mistyped a URL. Every one of these asserts the reason travels with
the status, because a bare 410 is only marginally better than a 404.

The machinery behind these routes is dormant, not deleted: the repository sections, the tables and
the kappa/AC1 stats engine are all still in place. Reversing this is re-mounting the routers.
`tests/test_calibration_stats.py` still exercises the agreement maths directly, and
`tests/committee_helpers.py` still builds the approved-decision tuple the dormant
`assert_committee_approved` unit tests need.

Coverage note, stated rather than buried: the calibration, committee and dual-rating suites that
these replace were HTTP-level end to end, so retiring the routes retired that coverage with them.
GRS-0224 tracks rebuilding it at the repository layer if the peer machinery is ever re-mounted.
That is a real gap on dormant code, and it is written down rather than left to be discovered.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from tests.conftest import SeededConsultant, auth_header

RETIRED_MARKER = "ADR-0041"

_ASSESSMENT = str(uuid4())
_SESSION = str(uuid4())

_MODULE = "APP_SERVER"

_GET_ROUTES = [
    f"/assessments/{_ASSESSMENT}/committee",
    "/committee/queue",
    "/calibration/sessions",
    f"/calibration/sessions/{_SESSION}",
    # Dual rating (Methodology §9) goes with the rest — "solo ratings are drafts" was the peer
    # discipline, and the founder gate is the discipline now.
    "/assessments/rating-requests",
    f"/assessments/{_ASSESSMENT}/modules/{_MODULE}/my-rating",
    f"/assessments/{_ASSESSMENT}/modules/{_MODULE}/ratings",
]

_POST_ROUTES = [
    (f"/assessments/{_ASSESSMENT}/committee/decide", {}),
    ("/calibration/sessions", {}),
    (f"/calibration/sessions/{_SESSION}/ratings", {}),
    (f"/calibration/sessions/{_SESSION}/close", {}),
    (f"/assessments/{_ASSESSMENT}/modules/{_MODULE}/consensus", {"resolved": []}),
]


@pytest.mark.parametrize("path", _GET_ROUTES)
def test_a_retired_get_route_is_gone_with_a_reason(
    client, alice: SeededConsultant, path: str
) -> None:
    resp = client.get(path, headers=auth_header(alice))
    assert resp.status_code == 410, f"{path} answered {resp.status_code}"
    assert RETIRED_MARKER in resp.json()["detail"]


@pytest.mark.parametrize("path,body", _POST_ROUTES)
def test_a_retired_post_route_is_gone_with_a_reason(
    client, alice: SeededConsultant, path: str, body: dict
) -> None:
    resp = client.post(path, json=body, headers=auth_header(alice))
    assert resp.status_code == 410, f"{path} answered {resp.status_code}"
    assert RETIRED_MARKER in resp.json()["detail"]


def test_retirement_refuses_before_the_handler_and_before_validation(
    client, alice: SeededConsultant
) -> None:
    """The refusal is a router-level dependency, so a retired route never reaches its handler and
    never validates a body. An empty POST would otherwise be a 422, and a 422 would imply the
    endpoint still exists and merely disliked the input."""
    resp = client.post("/calibration/sessions", json={}, headers=auth_header(alice))
    assert resp.status_code == 410


def test_a_retired_route_is_gone_even_without_a_token(client) -> None:
    """Retirement outranks authentication. A signed-out client asking for a withdrawn feature
    should hear that it is withdrawn, not be sent to log in for something that no longer exists."""
    resp = client.get("/committee/queue")
    assert resp.status_code == 410
