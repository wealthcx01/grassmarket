"""ADR-0040 / GRS-0167 — the one-number rule.

The deterministic engine points ride on LiveScore and ARE the quoted scores; finalisation stores
exactly the point the advisor watched, so the headline never moves at the finalise click (the 5/5
staging-persona finding). Scoring itself is untouched — these tests pin the display contract.
"""

from __future__ import annotations

import pytest

from grassmarket.demo.brokerage_showcase import HARGREAVES_LANSDOWN, showcase_document

from .conftest import auth_header


def test_live_points_are_the_deterministic_composite() -> None:
    """v/b/p/l_point equal the deterministic composite — and V recomposes from the parts, so the
    build-up chart finally recomputes to the headline (the Elena finding)."""
    import random

    from grassmarket.assessments.service import deterministic_result, live_score
    from grassmarket.atlas.active import (
        active_uncertainty_model,
        profile_key_of,
        profile_scoring_context,
    )

    doc = showcase_document(HARGREAVES_LANSDOWN)
    registry, coefficients = profile_scoring_context(profile_key_of(doc))
    live = live_score(
        doc, coefficients, registry, active_uncertainty_model(profile_key_of(doc)),
        random.Random(1),
    )
    det = deterministic_result(doc, coefficients, registry).composite
    assert live.v_point == det.v_index
    assert live.b_point == det.b_index
    assert live.p_point == det.p_index
    assert live.l_point == det.l_index
    # The additive build-up recomposes to the headline (within stored rounding).
    assert live.theta_b is not None
    recomposed = (
        live.theta_b * det.b_index + live.theta_p * det.p_index + live.theta_l * det.l_index
    )
    assert live.v_point == pytest.approx(recomposed, abs=0.005)


def test_finalisation_stores_the_watched_point(client, alice) -> None:
    """The end-to-end persona scenario: the live v_point BEFORE finalising equals the locked
    v_index AFTER — the number must not move at the finalise click."""
    headers = auth_header(alice)
    doc = showcase_document(HARGREAVES_LANSDOWN)
    aid = client.post(
        "/assessments", json={"subject": doc.subject, "provenance": "sandbox"}, headers=headers
    ).json()["id"]
    assert (
        client.put(
            f"/assessments/{aid}", json=doc.model_dump(mode="json"), headers=headers
        ).status_code
        == 200
    )
    live = client.get(f"/assessments/{aid}/live-score", headers=headers).json()
    assert live["scoreable"] and live["v_point"] is not None

    assert client.post(f"/assessments/{aid}/finalise", headers=headers).status_code == 200
    entry = client.get("/assessments/portfolio", headers=headers).json()[0]
    assert entry["v_index"] == live["v_point"]  # the watched number IS the locked number
