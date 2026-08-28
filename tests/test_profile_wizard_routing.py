"""GRS-0079 — the operating-model profile routes end-to-end: the registry endpoint serves the
profile VIEW, and an assessment carrying `operating_model` scores against that profile's coefficient
set (its distinct `coefficient_version` proves the round-trip). Retail (default) is unchanged."""

from __future__ import annotations

from fastapi.testclient import TestClient

from grassmarket.atlas.active import profile_key_of, profile_scoring_context
from tests.conftest import SeededConsultant, auth_header


def test_profile_key_of_defaults_to_retail() -> None:
    from bcap_contracts.assessments import AssessmentDocument, BusinessProfile

    assert profile_key_of(AssessmentDocument(subject="x")) == "retail"
    assert profile_key_of(AssessmentDocument(subject="x", profile=BusinessProfile())) == "retail"
    assert (
        profile_key_of(
            AssessmentDocument(subject="x", profile=BusinessProfile(operating_model="exchange"))
        )
        == "exchange"
    )


def test_registry_profiles_lists_retail_first_then_exchange(
    client: TestClient, alice: SeededConsultant
) -> None:
    resp = client.get("/registry/profiles", headers=auth_header(alice))
    assert resp.status_code == 200
    keys = [p["key"] for p in resp.json()]
    assert keys[0] == "retail" and "exchange" in keys


def test_registry_view_reshapes_by_profile(client: TestClient, alice: SeededConsultant) -> None:
    retail = client.get("/registry", headers=auth_header(alice)).json()
    retail_default = client.get("/registry?profile=retail", headers=auth_header(alice)).json()
    exchange = client.get("/registry?profile=exchange", headers=auth_header(alice)).json()
    # Default == retail == the full superset (9 modules).
    assert len(retail["modules"]) == 9 == len(retail_default["modules"])
    exchange_modules = {m["key"] for m in exchange["modules"]}
    assert "CMS" not in exchange_modules  # reshaped: no retail client-management module
    exchange_subs = {s["key"] for m in exchange["modules"] for s in m["subcomponents"]}
    assert "OEMS_MATCHING_ENGINE" in exchange_subs and not any(
        k.startswith("CMS_") for k in exchange_subs
    )


def test_unknown_profile_view_is_404(client: TestClient, alice: SeededConsultant) -> None:
    assert client.get("/registry?profile=bogus", headers=auth_header(alice)).status_code == 404


def _live_score_version(client: TestClient, seeded: SeededConsultant, operating_model) -> str:
    created = client.post(
        "/assessments", json={"subject": "Profiled Co"}, headers=auth_header(seeded)
    ).json()
    doc = {
        "subject": "Profiled Co",
        "subcomponents": [],
        "metrics": [],
        "powers": [],
    }
    if operating_model is not None:
        doc["profile"] = {"operating_model": operating_model}
    client.put(
        f"/assessments/{created['id']}", json=doc, headers=auth_header(seeded)
    ).raise_for_status()
    live = client.get(
        f"/assessments/{created['id']}/live-score", headers=auth_header(seeded)
    ).json()
    return live["coefficient_version"]


def test_live_score_uses_the_profiles_coefficient_set(
    client: TestClient, alice: SeededConsultant
) -> None:
    # The profile round-trips: document.operating_model → live-score's coefficient_version.
    assert _live_score_version(client, alice, None) == "v1-draft-pending-elicitation"
    assert _live_score_version(client, alice, "retail") == "v1-draft-pending-elicitation"
    # Wealth/exchange ACTIVATED (ADR-0037/GRS-0156): they score on the client-usable elicited set.
    assert _live_score_version(client, alice, "exchange") == "exchange-v1-elicited-starter-2026"
    assert _live_score_version(client, alice, "wealth") == "wealth-v1-elicited-starter-2026"


def test_profile_scoring_context_is_the_single_seam() -> None:
    # Retail view is the full registry; exchange view drops CMS. (Guards the helper source.)
    retail_view, _ = profile_scoring_context("retail")
    exchange_view, ex_coeffs = profile_scoring_context("exchange")
    assert len(retail_view.modules) == 9
    assert "CMS" not in {m.key for m in exchange_view.modules}
    assert ex_coeffs.version == "exchange-v1-elicited-starter-2026"  # ACTIVATED (GRS-0156)
    assert ex_coeffs.client_usable is True
