"""Test helpers for the dual-rating governance workflow (GRS-0020, Methodology §9).

Finalisation now refuses a solo-rated assessment, so any test that needs a *finalised* assessment
must first take each assessed module through dual rating → consensus. `reach_consensus` drives that
over the HTTP API exactly as a human would: assign two raters, both submit blind, the lead resolves.

The mandatory second rater is seeded directly against the running app's engine (the same invite-free
bootstrap the conftest fixtures use), so callers of the shared finalise helpers need not thread a
co-rater through — the helper supplies one.
"""

from __future__ import annotations

from uuid import uuid4

from bcap_contracts.common import (
    AssessorLevel,
    ConsultantTier,
    EvidenceGrade,
    MaturityLevel,
    Role,
)

from grassmarket.auth.security import create_access_token, hash_password
from grassmarket.data.repository import Principal, Repository
from tests.conftest import SeededConsultant, auth_header

_E3 = EvidenceGrade.E3_ARTIFACT


def seed_corater(client, *, email: str | None = None) -> SeededConsultant:
    """Seed one extra consultant (Certified Lead) + bearer token against the app's engine — the
    second independent rater a deliverable-bearing assessment requires (§9)."""
    factory = client.app.state.session_factory
    settings = client.app.state.settings
    email = email or f"corater-{uuid4().hex[:10]}@bruntsfieldcapital.com"
    session = factory()
    try:
        repo = Repository(session)
        stored = repo.create_consultant(
            email=email,
            full_name=email.split("@")[0].title(),
            hashed_password=hash_password("correct-horse-battery-staple"),
            role=Role.CONSULTANT,
            tier=ConsultantTier.CONSULTANT,
            assessor_level=AssessorLevel.CERTIFIED_LEAD,
        )
        session.commit()
    finally:
        session.close()
    token = create_access_token(
        settings,
        consultant_id=stored.id,
        email=stored.email,
        role=stored.role,
        tier=stored.tier,
        assessor_level=stored.assessor_level,
    )
    return SeededConsultant(
        stored=stored,
        principal=Principal(consultant_id=stored.id, role=stored.role),
        token=token,
    )


def _rating_json(module_key: str, subcomponent_key: str, level: MaturityLevel) -> dict:
    return {
        "module_key": module_key,
        "subcomponent_key": subcomponent_key,
        "level": level.value,
        "evidence_grade": _E3.value,
    }


def assign_rater(client, aid: str, lead: SeededConsultant, module_key: str, rater_id) -> None:
    resp = client.post(
        f"/assessments/{aid}/modules/{module_key}/raters",
        json={"rater_consultant_id": str(rater_id)},
        headers=auth_header(lead),
    )
    assert resp.status_code == 201, resp.text


def submit_ratings(
    client,
    aid: str,
    rater: SeededConsultant,
    module_key: str,
    subs: list[tuple[str, MaturityLevel]],
) -> None:
    ratings = [_rating_json(module_key, key, level) for key, level in subs]
    put = client.put(
        f"/assessments/{aid}/modules/{module_key}/my-rating",
        json={"ratings": ratings},
        headers=auth_header(rater),
    )
    assert put.status_code == 200, put.text
    submitted = client.post(
        f"/assessments/{aid}/modules/{module_key}/my-rating/submit",
        headers=auth_header(rater),
    )
    assert submitted.status_code == 200, submitted.text


def reach_consensus(
    client,
    aid: str,
    lead: SeededConsultant,
    module_key: str,
    subs: list[tuple[str, MaturityLevel]],
    *,
    co_rater: SeededConsultant | None = None,
) -> SeededConsultant:
    """Take one module through the full §9 workflow to an agreed consensus (both raters give the
    same level → consensus=True, no dissent). Returns the co-rater used. `subs` is a list of
    (subcomponent_key, level) — every assessed subcomponent the module should carry afterwards."""
    co = co_rater or seed_corater(client)
    assign_rater(client, aid, lead, module_key, lead.principal.consultant_id)
    assign_rater(client, aid, lead, module_key, co.principal.consultant_id)
    submit_ratings(client, aid, lead, module_key, subs)
    submit_ratings(client, aid, co, module_key, subs)
    resolved = [_rating_json(module_key, key, level) for key, level in subs]
    res = client.post(
        f"/assessments/{aid}/modules/{module_key}/consensus",
        json={"resolved": resolved},
        headers=auth_header(lead),
    )
    assert res.status_code == 200, res.text
    return co
