"""The production smoke suite, exercised in-process (GRS-0034).

Two jobs:
1. Prove the `scripts/prod_smoke.py` step logic actually works — run it against a fresh in-process
   app so the smoke script cannot silently rot (a broken endpoint fails CI here, before prod).
2. Prove the ONE thing the live smoke script deliberately cannot: the full synthetic engagement
   end-to-end — created, assessed, dual-rated to consensus, committee-signed-off, finalised, and a
   deliverable generated + downloaded. That lifecycle is governance-gated (needs a second rater and
   a committee member seeded server-side), so it belongs in CI, not in a single-account prod probe.
"""

from __future__ import annotations

import importlib.util
from io import BytesIO
from pathlib import Path

from docx import Document

from tests.conftest import SeededConsultant, auth_header
from tests.test_deliverables import _engagement_with_finalised

# Load the smoke script by path (it lives under scripts/, not an importable package).
_SMOKE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "prod_smoke.py"
_spec = importlib.util.spec_from_file_location("_prod_smoke", _SMOKE_PATH)
assert _spec and _spec.loader
prod_smoke = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prod_smoke)

_PASSWORD = "correct-horse-battery-staple"  # the conftest-seeded password


def test_health_and_read_only_checks_pass_in_process(client, alice: SeededConsultant) -> None:
    smoke = prod_smoke.Smoke(client)
    env = prod_smoke.check_health(smoke)
    assert env  # /health reported an environment
    token = prod_smoke.login(smoke, alice.stored.email, _PASSWORD)
    prod_smoke.read_only_checks(smoke, token)
    assert smoke.failures == []


def test_write_lifecycle_is_reversible_and_green(client, alice: SeededConsultant) -> None:
    smoke = prod_smoke.Smoke(client)
    token = prod_smoke.login(smoke, alice.stored.email, _PASSWORD)
    prod_smoke.write_lifecycle(smoke, token)
    assert smoke.failures == []


def test_run_orchestrator_returns_zero_when_healthy(client, alice: SeededConsultant) -> None:
    smoke = prod_smoke.Smoke(client)
    code = prod_smoke.run(smoke, email=alice.stored.email, password=_PASSWORD, do_writes=True)
    assert code == 0
    assert smoke.failures == []


def test_login_failure_is_reported_not_raised_past_the_runner(
    client, alice: SeededConsultant
) -> None:
    # A wrong password must surface as a 401 smoke failure, not a hollow pass.
    smoke = prod_smoke.Smoke(client)
    try:
        prod_smoke.login(smoke, alice.stored.email, "wrong-password")
    except prod_smoke.SmokeError:
        pass
    assert smoke.failures  # recorded the failure


def test_build_scoreable_document_matches_live_registry(client, alice: SeededConsultant) -> None:
    registry = client.get("/registry", headers=auth_header(alice)).json()
    doc = prod_smoke.build_scoreable_document(registry, subject="X")
    # All powers graded (the registry requires every power), one metric, one subcomponent.
    assert len(doc["powers"]) == len(registry["powers"])
    assert doc["metrics"][0]["metric_key"] == registry["metrics"][0]["key"]
    assert doc["subcomponents"][0]["module_key"] == registry["modules"][0]["key"]


def test_full_engagement_lifecycle_finalise_and_deliverable(
    client, alice: SeededConsultant
) -> None:
    """The ticket's synthetic engagement end-to-end: created -> assessed -> finalised -> deliverable
    generated + downloaded. This is what the live smoke script cannot do solo (governance-gated)."""
    eid = _engagement_with_finalised(client, alice)  # contracted prospect + finalised assessment
    created = client.post(
        f"/engagements/{eid}/deliverables",
        json={"client_facing": False},
        headers=auth_header(alice),
    )
    assert created.status_code == 201, created.text
    did = created.json()["id"]
    assert created.json()["mode"] == "draft_internal"

    download = client.get(f"/deliverables/{did}/download", headers=auth_header(alice))
    assert download.status_code == 200
    assert download.content[:2] == b"PK"  # a real .docx
    # And it renders as a document (not a truncated stub).
    Document(BytesIO(download.content))
