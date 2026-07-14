"""Bench queue + performance over HTTP (GRS-0026). The priority logic is golden-mastered in
tests/test_bench_scoring.py; here we pin the wiring (the repository assembles the queue from the
caller's real sources) and the scoping (performance is self-only — a foreign id is a 404).
"""

from __future__ import annotations

from tests.conftest import SeededConsultant, auth_header

_SCENARIO = {
    "title": "Meridian discovery",
    "brief": "A mid-market broker exploring its moat.",
    "client_persona": "A guarded CFO.",
    "target_powers": [
        {"power_key": "SCALE_ECONOMIES", "benefit_cues": ["fixed cost"], "barrier_cues": ["moat"]}
    ],
}


def test_a_fresh_advisor_always_has_a_queue(client, alice: SeededConsultant) -> None:
    body = client.get("/bench/queue", headers=auth_header(alice)).json()
    kinds = [i["kind"] for i in body["items"]]
    # No content seeded yet: the next certification step, and the standing research task.
    assert kinds == ["certification", "research"]
    assert [i["priority"] for i in body["items"]] == [1, 2]
    assert body["owner_consultant_id"] == str(alice.stored.id)


def test_the_queue_wires_the_advisors_real_sources(
    client, alice: SeededConsultant, admin: SeededConsultant
) -> None:
    # An admin publishes an arena scenario → it becomes available practice for every advisor.
    client.post("/arena/scenarios", json=_SCENARIO, headers=auth_header(admin))
    # Alice sources a prospect → it becomes her Opportunity Radar research target.
    prospect = client.post(
        "/prospects", json={"company_name": "Acme Broking"}, headers=auth_header(alice)
    ).json()

    body = client.get("/bench/queue", headers=auth_header(alice)).json()
    by_kind = {i["kind"]: i for i in body["items"]}
    assert set(by_kind) == {"certification", "arena", "research"}
    # Priority order holds: certification, then arena, then research.
    assert [i["kind"] for i in body["items"]] == ["certification", "arena", "research"]
    # The research task points at Alice's own prospect (sourcing-credit linkage).
    assert by_kind["research"]["ref_id"] == prospect["id"]


def test_performance_summary_is_self_scoped(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    own = client.get(f"/bench/performance/{alice.stored.id}", headers=auth_header(alice))
    assert own.status_code == 200
    summary = own.json()
    assert summary["owner_consultant_id"] == str(alice.stored.id)
    assert summary["pipeline_conversion_rate"] == 0.0
    assert summary["level"] == "trained"

    # Bob's summary is not visible to Alice — a foreign id is a 404 (not shown to exist).
    foreign = client.get(f"/bench/performance/{bob.stored.id}", headers=auth_header(alice))
    assert foreign.status_code == 404


def test_an_admin_cannot_read_another_advisors_performance_here(
    client, alice: SeededConsultant, admin: SeededConsultant
) -> None:
    # The cross-advisor/admin aggregate is Holy Corner scope — even an admin gets a 404 here.
    resp = client.get(f"/bench/performance/{alice.stored.id}", headers=auth_header(admin))
    assert resp.status_code == 404


def test_admin_bench_views_are_self_scoped_not_org_wide(
    client, alice: SeededConsultant, admin: SeededConsultant
) -> None:
    # The admin is a real consultant with their own pipeline; Alice has a separate one. The bench
    # views must be strictly self-scoped for EVERYONE — the admin-sees-all read must not leak here.
    client.post("/prospects", json={"company_name": "Alice Co"}, headers=auth_header(alice))
    client.post("/prospects", json={"company_name": "Alice Two"}, headers=auth_header(alice))
    admin_prospect = client.post(
        "/prospects", json={"company_name": "Admin Co"}, headers=auth_header(admin)
    ).json()

    # Performance totals reflect ONLY the admin's own records (1 prospect), never the org's (3).
    perf = client.get(f"/bench/performance/{admin.stored.id}", headers=auth_header(admin)).json()
    assert perf["prospects_total"] == 1

    # The queue's research nudge points at the admin's OWN prospect, not Alice's.
    queue = client.get("/bench/queue", headers=auth_header(admin)).json()
    research = next(i for i in queue["items"] if i["kind"] == "research")
    assert research["ref_id"] == admin_prospect["id"]


def test_bench_endpoints_require_authentication(client, alice: SeededConsultant) -> None:
    assert client.get("/bench/queue").status_code == 401
    assert client.get(f"/bench/performance/{alice.stored.id}").status_code == 401
