"""Calibration session lifecycle + blind-collection tests (GRS-0022, Methodology §9).

The statistics themselves are golden-mastered in tests/test_calibration_stats.py; here we pin the
HTTP/repository lifecycle: facilitator-only open/close, blind collection (results don't exist and a
rater can't see co-raters until close), the flagged-anchor report, and fail-loud on thin data.
"""

from __future__ import annotations

from bcap_contracts.common import MaturityLevel

from tests.conftest import SeededConsultant, auth_header
from tests.dual_rating_helpers import seed_corater

_A = "APP_SERVER_SECURITY_COMPLIANCE"
_B = "APP_SERVER_API_DESIGN"

# Two vignettes, each rating the same two anchors (A and B).
_VIGNETTES = [
    {
        "title": "Meridian — trading platform",
        "excerpt": "A mid-market broker's OMS and security posture …",
        "anchors": [
            {"subcomponent_key": _A, "reference_level": "Advanced"},
            {"subcomponent_key": _B, "reference_level": "Developing"},
        ],
    },
    {
        "title": "Northgate — wealth platform",
        "excerpt": "A wealth manager's custody and API estate …",
        "anchors": [
            {"subcomponent_key": _A, "reference_level": "Frontier"},
            {"subcomponent_key": _B, "reference_level": "Basic"},
        ],
    },
]


def _entries(ratings: dict) -> list[dict]:
    """ratings maps (vignette_index, subcomponent) → MaturityLevel."""
    return [
        {"vignette_index": i, "subcomponent_key": sub, "level": level.value}
        for (i, sub), level in ratings.items()
    ]


def _open_session(client, admin: SeededConsultant) -> str:
    resp = client.post(
        "/calibration/sessions",
        json={"title": "2026 Q3 calibration", "vignettes": _VIGNETTES},
        headers=auth_header(admin),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# Anchor A: all three raters agree per vignette → high kappa → NOT flagged.
# Anchor B: raters scatter across the scale → low kappa → FLAGGED (κ < 0.6).
_ADV, _FRO, _BAS, _DEV = (
    MaturityLevel.ADVANCED,
    MaturityLevel.FRONTIER,
    MaturityLevel.BASIC,
    MaturityLevel.DEVELOPING,
)
_RATER_1 = {(0, _A): _ADV, (1, _A): _FRO, (0, _B): _BAS, (1, _B): _FRO}
_RATER_2 = {(0, _A): _ADV, (1, _A): _FRO, (0, _B): _FRO, (1, _B): _BAS}
_RATER_3 = {(0, _A): _ADV, (1, _A): _FRO, (0, _B): _ADV, (1, _B): _DEV}


def _submit_three(client, sid, raters) -> None:
    for rater, ratings in zip(raters, (_RATER_1, _RATER_2, _RATER_3), strict=True):
        resp = client.post(
            f"/calibration/sessions/{sid}/ratings",
            json={"entries": _entries(ratings)},
            headers=auth_header(rater),
        )
        assert resp.status_code == 200, resp.text


# --- Lifecycle + the flagged-anchor report ----------------------------------------------


def test_full_session_computes_agreement_and_flags_low_anchors(
    client, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    carol = seed_corater(client)
    sid = _open_session(client, admin)
    _submit_three(client, sid, (alice, bob, carol))

    result = client.post(f"/calibration/sessions/{sid}/close", headers=auth_header(admin))
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["n_raters"] == 3
    anchors = {a["subcomponent_key"]: a for a in body["anchors"]}

    # Anchor A: perfect agreement per vignette → kappa 1.0, not flagged.
    assert anchors[_A]["flagged"] is False
    assert anchors[_A]["kappa_w"] > 0.6
    # Anchor B: raters scattered → low agreement → flagged for rewrite (§9).
    assert anchors[_B]["flagged"] is True
    assert anchors[_B]["kappa_w"] < 0.6
    # Coefficients stay in range and AC1 is reported alongside.
    assert all(-1.0 <= a["ac1"] <= 1.0 for a in body["anchors"])


# --- Blind collection (the load-bearing §9 guarantee) -----------------------------------


def test_results_are_blind_until_the_session_closes(
    client, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    carol = seed_corater(client)
    sid = _open_session(client, admin)
    _submit_three(client, sid, (alice, bob, carol))
    # Every rating is in, but while the session is OPEN the distribution/coefficients do not exist.
    blind = client.get(f"/calibration/sessions/{sid}/results", headers=auth_header(alice))
    assert blind.status_code == 409
    assert "blind" in blind.json()["detail"]

    client.post(f"/calibration/sessions/{sid}/close", headers=auth_header(admin))
    assert (
        client.get(f"/calibration/sessions/{sid}/results", headers=auth_header(alice)).status_code
        == 200
    )


def test_a_rater_only_ever_sees_their_own_rating(
    client, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    sid = _open_session(client, admin)
    client.post(
        f"/calibration/sessions/{sid}/ratings",
        json={"entries": _entries(_RATER_1)},
        headers=auth_header(alice),
    )
    # Alice sees her own submitted rating…
    mine = client.get(f"/calibration/sessions/{sid}/my-rating", headers=auth_header(alice))
    assert mine.status_code == 200 and mine.json()["submitted"] is True
    # …but Bob (who has not rated) has no rating to see — never Alice's.
    assert (
        client.get(f"/calibration/sessions/{sid}/my-rating", headers=auth_header(bob)).status_code
        == 404
    )


def test_a_submitted_rating_is_locked(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    sid = _open_session(client, admin)
    body = {"entries": _entries(_RATER_1)}
    assert (
        client.post(
            f"/calibration/sessions/{sid}/ratings", json=body, headers=auth_header(alice)
        ).status_code
        == 200
    )
    again = client.post(
        f"/calibration/sessions/{sid}/ratings", json=body, headers=auth_header(alice)
    )
    assert again.status_code == 409
    assert "locked" in again.json()["detail"]


def test_ratings_are_refused_after_close(
    client, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    carol = seed_corater(client)
    sid = _open_session(client, admin)
    _submit_three(client, sid, (alice, bob, carol))
    client.post(f"/calibration/sessions/{sid}/close", headers=auth_header(admin))
    late = seed_corater(client)
    resp = client.post(
        f"/calibration/sessions/{sid}/ratings",
        json={"entries": _entries(_RATER_1)},
        headers=auth_header(late),
    )
    assert resp.status_code == 409
    assert "closed" in resp.json()["detail"]


# --- Validation + fail-loud -------------------------------------------------------------


def test_an_incomplete_rating_is_refused(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    sid = _open_session(client, admin)
    partial = {"entries": _entries({(0, _A): _ADV})}  # missing the other three anchors
    resp = client.post(
        f"/calibration/sessions/{sid}/ratings", json=partial, headers=auth_header(alice)
    )
    assert resp.status_code == 409
    assert "exactly the session's anchors" in resp.json()["detail"]


def test_closing_with_fewer_than_two_raters_is_refused(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    sid = _open_session(client, admin)
    client.post(
        f"/calibration/sessions/{sid}/ratings",
        json={"entries": _entries(_RATER_1)},
        headers=auth_header(alice),
    )
    resp = client.post(f"/calibration/sessions/{sid}/close", headers=auth_header(admin))
    assert resp.status_code == 409
    assert "submitted" in resp.json()["detail"]


def test_re_closing_is_refused(
    client, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    carol = seed_corater(client)
    sid = _open_session(client, admin)
    _submit_three(client, sid, (alice, bob, carol))
    assert (
        client.post(f"/calibration/sessions/{sid}/close", headers=auth_header(admin)).status_code
        == 200
    )
    assert (
        client.post(f"/calibration/sessions/{sid}/close", headers=auth_header(admin)).status_code
        == 409
    )


# --- Authority (facilitator-only open/close) --------------------------------------------


def test_only_a_facilitator_may_open_and_close(
    client, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    # A non-admin cannot open a session.
    denied = client.post(
        "/calibration/sessions",
        json={"title": "rogue", "vignettes": _VIGNETTES},
        headers=auth_header(alice),
    )
    assert denied.status_code == 403

    # …but any consultant can view sessions and submit their own rating.
    sid = _open_session(client, admin)
    carol = seed_corater(client)
    _submit_three(client, sid, (alice, bob, carol))
    assert client.get(f"/calibration/sessions/{sid}", headers=auth_header(alice)).status_code == 200

    # A non-facilitator cannot close it.
    assert (
        client.post(f"/calibration/sessions/{sid}/close", headers=auth_header(alice)).status_code
        == 403
    )


def test_endpoints_require_authentication(client) -> None:
    assert client.get("/calibration/sessions").status_code == 401


# --- Review-driven: duplicate refusal, org-wide results, single-vignette, list ----------

_SINGLE_VIGNETTE = [
    {
        "title": "Solo case",
        "excerpt": "A single case rating one anchor …",
        "anchors": [{"subcomponent_key": _A, "reference_level": "Advanced"}],
    }
]


def test_a_duplicate_entry_is_refused(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    sid = _open_session(client, admin)
    entries = _entries(_RATER_1)
    entries.append({"vignette_index": 0, "subcomponent_key": _A, "level": "Frontier"})  # dup of A
    resp = client.post(
        f"/calibration/sessions/{sid}/ratings",
        json={"entries": entries},
        headers=auth_header(alice),
    )
    assert resp.status_code == 409
    assert "duplicate" in resp.json()["detail"]


def test_closed_results_are_visible_org_wide_to_a_non_participant(
    client, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    carol = seed_corater(client)
    sid = _open_session(client, admin)
    _submit_three(client, sid, (alice, bob, carol))
    client.post(f"/calibration/sessions/{sid}/close", headers=auth_header(admin))
    # A consultant who never rated this session can still read the (shared) closed result.
    outsider = seed_corater(client)
    resp = client.get(f"/calibration/sessions/{sid}/results", headers=auth_header(outsider))
    assert resp.status_code == 200
    assert resp.json()["n_raters"] == 3


def test_a_single_vignette_anchor_cannot_be_measured(
    client, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    """Agreement over one item is not a reliability measure — an anchor needs ≥2 vignettes (§9), so
    closing a session whose anchor recurs only once is refused, not flagged on one point."""
    resp = client.post(
        "/calibration/sessions",
        json={"title": "single", "vignettes": _SINGLE_VIGNETTE},
        headers=auth_header(admin),
    )
    sid = resp.json()["id"]
    for rater in (alice, bob):
        client.post(
            f"/calibration/sessions/{sid}/ratings",
            json={"entries": [{"vignette_index": 0, "subcomponent_key": _A, "level": "Advanced"}]},
            headers=auth_header(rater),
        )
    result = client.post(f"/calibration/sessions/{sid}/close", headers=auth_header(admin))
    assert result.status_code == 409
    assert "at least two" in result.json()["detail"]


def test_sessions_are_listed_org_wide(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    sid = _open_session(client, admin)
    listed = client.get("/calibration/sessions", headers=auth_header(alice))  # a non-admin
    assert listed.status_code == 200
    assert any(s["id"] == sid for s in listed.json())
