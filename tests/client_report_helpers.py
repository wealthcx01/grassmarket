"""Build a deliverable that can actually produce a client report (GRS-0219/0220 wiring tests).

Assembling a report needs a real finalised scoring run, because the report quotes that run's stored
numbers. So these helpers walk the same path an advisor does — contract the prospect, score and
finalise an assessment, open the engagement, generate the deliverable — rather than inserting a
bare row. That is slower, and it is the point: the wiring is what these tests exist to check.
"""

from __future__ import annotations

from bcap_contracts.client_report import SECTION_ORDER
from bcap_contracts.entities import PipelineStage

from tests.conftest import SeededConsultant, auth_header
from tests.founder_review_helpers import submit_and_approve
from tests.test_assessment_lifecycle import _body, _scoreable_partial_doc

_TO_CONTRACTED = (
    PipelineStage.WORKSHOP_SCHEDULED,
    PipelineStage.WORKSHOP_DELIVERED,
    PipelineStage.QUALIFIED,
    PipelineStage.SCOPED,
    PipelineStage.CONTRACTED,
)


def contracted_prospect(client, owner: SeededConsultant, name: str = "Meridian") -> str:
    pid = client.post("/prospects", json={"company_name": name}, headers=auth_header(owner)).json()[
        "id"
    ]
    for stage in _TO_CONTRACTED:
        client.patch(
            f"/prospects/{pid}/stage", json={"stage": stage.value}, headers=auth_header(owner)
        )
    return pid


def finalised_assessment(client, owner: SeededConsultant, founder: SeededConsultant) -> str:
    """A finalised assessment. Production records need the founder's sign-off first (ADR-0041)."""
    aid = client.post(
        "/assessments", json={"subject": "Meridian"}, headers=auth_header(owner)
    ).json()["id"]
    client.put(
        f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(owner)
    )
    submit_and_approve(client, aid, owner, founder)
    response = client.post(f"/assessments/{aid}/finalise", headers=auth_header(owner))
    assert response.status_code == 200, response.text
    return aid


def sandbox_deliverable_with_run(client, owner: SeededConsultant) -> str:
    """The same thing on a SANDBOX record — which self-approves, so no founder is needed (ADR-0029).

    This is the record type GRS-0229 is about: watermarked everywhere, never client-facing, and the
    one an advisor is most likely to share a link for, because it is what they use to preview the
    client experience.
    """
    pid = contracted_prospect(client, owner)
    aid = client.post(
        "/assessments",
        json={"subject": "Meridian", "provenance": "sandbox"},
        headers=auth_header(owner),
    ).json()["id"]
    client.put(
        f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(owner)
    )
    finalised = client.post(f"/assessments/{aid}/finalise", headers=auth_header(owner))
    assert finalised.status_code == 200, finalised.text
    engagement = client.post(
        "/engagements",
        json={"prospect_id": pid, "title": "Sandbox preview", "assessment_ids": [aid]},
        headers=auth_header(owner),
    )
    assert engagement.status_code == 201, engagement.text
    generated = client.post(
        f"/engagements/{engagement.json()['id']}/deliverables",
        json={"client_facing": False},
        headers=auth_header(owner),
    )
    assert generated.status_code in (200, 201), generated.text
    return generated.json()["id"]


def deliverable_with_run(client, owner: SeededConsultant, founder: SeededConsultant) -> str:
    """A generated deliverable bound to a finalised run — what a client report is built from."""
    pid = contracted_prospect(client, owner)
    aid = finalised_assessment(client, owner, founder)
    engagement = client.post(
        "/engagements",
        json={"prospect_id": pid, "title": "Q3 review", "assessment_ids": [aid]},
        headers=auth_header(owner),
    )
    assert engagement.status_code == 201, engagement.text
    engagement_id = engagement.json()["id"]

    generated = client.post(
        f"/engagements/{engagement_id}/deliverables",
        json={"client_facing": False},
        headers=auth_header(owner),
    )
    assert generated.status_code in (200, 201), generated.text
    return generated.json()["id"]


def written_prose() -> dict:
    """Six sections with words in them — enough for the report to assemble.

    Deliberately free of numbers: the content model refuses any figure the prose has not declared,
    and these helpers are about the wiring, not about the declaration rule (which GRS-0211 tests).
    """
    return {
        kind.value: {
            "heading": kind.value.title(),
            "body": [f"What a consultant wrote about {kind.value}."],
            "tier": "engaged",
        }
        for kind in SECTION_ORDER
    }
