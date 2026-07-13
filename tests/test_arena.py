"""Practice Arena tests (GRS-0025, PRD §6).

The scorer itself is golden-mastered in tests/test_arena_scoring.py; here we pin the exit criteria
over HTTP: a full session runs end-to-end (start → submit → deterministic score against the same
fixture), feedback is labelled AI-drafted, and scores persist + appear in the advisor's history.
"""

from __future__ import annotations

from bcap_contracts.arena import AI_DRAFTED_LABEL

from tests.conftest import SeededConsultant, auth_header

_SCENARIO = {
    "title": "Meridian discovery",
    "brief": "A mid-market broker exploring its moat.",
    "client_persona": "A guarded CFO who answers narrowly.",
    "target_powers": [
        {
            "power_key": "SCALE_ECONOMIES",
            "benefit_cues": ["fixed cost", "unit cost"],
            "barrier_cues": ["scale advantage", "hard to replicate"],
        },
        {
            "power_key": "NETWORK_ECONOMIES",
            "benefit_cues": ["network effect", "more users"],
            "barrier_cues": ["lock-in", "switching"],
        },
    ],
    "target_modules": [
        {"module_key": "APP_SERVER", "cues": ["hosting", "uptime"]},
        {"module_key": "OEMS", "cues": ["order management", "execution"]},
    ],
    "evidence_cues": ["can you show", "do you have data", "what evidence"],
}

# The same transcript as the golden master → completeness 0.625, SCALE fully, NETWORK benefit-only,
# APP_SERVER evidenced, OEMS not, 1 evidence question.
_TRANSCRIPT = [
    {"speaker": "client", "text": "We run a lean broker."},
    {"speaker": "advisor", "text": "How does your fixed cost behave as volume grows?"},
    {"speaker": "advisor", "text": "Is that scale advantage hard to replicate for a rival?"},
    {"speaker": "advisor", "text": "Do you see network effects as more users join the venue?"},
    {"speaker": "advisor", "text": "Can you show me the uptime data for your hosting?"},
]


def _scenario_id(client, admin: SeededConsultant) -> str:
    resp = client.post("/arena/scenarios", json=_SCENARIO, headers=auth_header(admin))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# --- A full session runs end-to-end and scores deterministically ------------------------


def test_a_full_arena_session_runs_and_scores(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    scenario_id = _scenario_id(client, admin)
    session = client.post(f"/arena/scenarios/{scenario_id}/sessions", headers=auth_header(alice))
    assert session.status_code == 201
    assert session.json()["status"] == "in_progress" and session.json()["score"] is None
    session_id = session.json()["id"]

    scored = client.post(
        f"/arena/sessions/{session_id}/submit",
        json={"transcript": _TRANSCRIPT},
        headers=auth_header(alice),
    )
    assert scored.status_code == 200
    body = scored.json()
    assert body["status"] == "scored"

    # The deterministic score matches the golden master.
    score = body["score"]
    assert score["completeness"] == 0.625
    probes = {p["power_key"]: p for p in score["powers"]}
    scale = probes["SCALE_ECONOMIES"]
    assert scale["benefit_probed"] and scale["barrier_probed"]
    network = probes["NETWORK_ECONOMIES"]
    assert network["benefit_probed"] and not network["barrier_probed"]
    assert set(score["modules_evidenced"]) == {"APP_SERVER"}
    assert score["evidence_questions"] == 1

    # Feedback is AI-drafted and labelled as such (#8).
    assert body["feedback_is_ai_drafted"] is True
    assert body["feedback"].startswith(AI_DRAFTED_LABEL)
    assert body["drafter_version"]


def test_scores_persist_and_appear_in_the_advisors_history(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    scenario_id = _scenario_id(client, admin)
    session_id = client.post(
        f"/arena/scenarios/{scenario_id}/sessions", headers=auth_header(alice)
    ).json()["id"]
    client.post(
        f"/arena/sessions/{session_id}/submit",
        json={"transcript": _TRANSCRIPT},
        headers=auth_header(alice),
    )
    # It is in Alice's history, with its score.
    history = client.get("/arena/sessions", headers=auth_header(alice)).json()
    assert [s["id"] for s in history] == [session_id]
    assert history[0]["score"]["completeness"] == 0.625


def test_a_session_cannot_be_submitted_twice(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    scenario_id = _scenario_id(client, admin)
    session_id = client.post(
        f"/arena/scenarios/{scenario_id}/sessions", headers=auth_header(alice)
    ).json()["id"]
    body = {"transcript": _TRANSCRIPT}
    assert (
        client.post(
            f"/arena/sessions/{session_id}/submit", json=body, headers=auth_header(alice)
        ).status_code
        == 200
    )
    again = client.post(
        f"/arena/sessions/{session_id}/submit", json=body, headers=auth_header(alice)
    )
    assert again.status_code == 409
    assert "already been scored" in again.json()["detail"]


# --- Scoping ----------------------------------------------------------------------------


def test_only_an_admin_authors_scenarios_but_all_read_them(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    denied = client.post("/arena/scenarios", json=_SCENARIO, headers=auth_header(alice))
    assert denied.status_code == 403
    scenario_id = _scenario_id(client, admin)
    # Any advisor can read the shared scenario library.
    assert any(
        s["id"] == scenario_id
        for s in client.get("/arena/scenarios", headers=auth_header(alice)).json()
    )


def test_a_session_is_owner_scoped(
    client, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    scenario_id = _scenario_id(client, admin)
    session_id = client.post(
        f"/arena/scenarios/{scenario_id}/sessions", headers=auth_header(alice)
    ).json()["id"]
    # Bob cannot submit or read Alice's session, and it is not in his history.
    assert (
        client.post(
            f"/arena/sessions/{session_id}/submit",
            json={"transcript": _TRANSCRIPT},
            headers=auth_header(bob),
        ).status_code
        == 404
    )
    assert client.get(f"/arena/sessions/{session_id}", headers=auth_header(bob)).status_code == 404
    assert client.get("/arena/sessions", headers=auth_header(bob)).json() == []


def test_starting_a_session_on_an_unknown_scenario_is_404(client, alice: SeededConsultant) -> None:
    from uuid import uuid4

    resp = client.post(f"/arena/scenarios/{uuid4()}/sessions", headers=auth_header(alice))
    assert resp.status_code == 404


def test_endpoints_require_authentication(client) -> None:
    from uuid import uuid4

    sid = uuid4()
    assert client.get("/arena/scenarios").status_code == 401
    assert client.get("/arena/sessions").status_code == 401
    assert client.post("/arena/scenarios", json=_SCENARIO).status_code == 401
    assert client.post(f"/arena/scenarios/{sid}/sessions").status_code == 401
    submit = client.post(f"/arena/sessions/{sid}/submit", json={"transcript": _TRANSCRIPT})
    assert submit.status_code == 401
