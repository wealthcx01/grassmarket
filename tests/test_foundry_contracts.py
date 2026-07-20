"""FB-002 — Foundry Studio contract tests.

Covers the six entities fountainbridge renders: construction, round-trip serialization both
directions (model -> json -> model, and dict -> model -> json), the D7 approval-matrix shape,
and the fail-loud invariants (extra fields forbidden; the founder's workspace_email may never be
a personal consumer mailbox — D3). These are the contracts FB-003's manifests validate against.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from bcap_contracts.foundry import (
    Approval,
    ApprovalKind,
    ApprovalRule,
    ApprovalState,
    Approver,
    ChangeClass,
    Department,
    DepartmentGate,
    FounderIdentity,
    Lane,
    LaneStatus,
    RunOutcome,
    RunReport,
    RunTrigger,
    Ticket,
    TicketStatus,
    Venture,
    VentureStatus,
    VpsBinding,
)
from pydantic import ValidationError


def _now() -> datetime:
    return datetime(2026, 7, 20, 9, 0, tzinfo=UTC)


def _founder() -> FounderIdentity:
    return FounderIdentity(name="Ross", github_login="ross-gh", workspace_email="ross@thereset.com")


def _lane() -> Lane:
    return Lane(
        id="platform",
        venture_id="the-reset",
        repo="thereset-platform",
        tmux="reset:0",
        standing_order="ship platform v0.1 (read-only dashboard)",
        status=LaneStatus.ACTIVE,
    )


def _department() -> Department:
    return Department(
        id="gtm",
        venture_id="the-reset",
        name="GTM",
        repo="thereset-marketing",
        queue_path="docs/tickets",
        connectors=["stripe"],
        gate=DepartmentGate.ACTIVEGRAPH,
    )


def _venture() -> Venture:
    return Venture(
        id="the-reset",
        name="THE RESET",
        status=VentureStatus.DRAFT,
        tier3_ref="THE RESET",
        vps=VpsBinding(host="reset.vps", provider="hetzner", provisioned_at=_now()),
        founder=_founder(),
        approval_matrix=[
            ApprovalRule(change_class=ChangeClass.PRODUCT_VISIBLE, approver=Approver.FOUNDER),
            ApprovalRule(change_class=ChangeClass.PLATFORM_INFRA, approver=Approver.BRUNTSFIELD),
            ApprovalRule(change_class=ChangeClass.HIGH_BLAST_RADIUS, approver=Approver.DUAL),
        ],
        repos=["thereset-platform", "thereset-marketing"],
        lanes=[_lane()],
        departments=[_department()],
        connectors=["stripe", "postmark"],
    )


def _ticket() -> Ticket:
    return Ticket(
        id="FB-001",
        repo="fountainbridge",
        path="docs/tickets/FB-001-scaffold-fountainbridge-repo.md",
        title="Complete fountainbridge repo scaffold",
        phase="0",
        depends_on=[],
        status=TicketStatus.PR_OPEN,
        branch="fb-001-scaffold",
        pr_url="https://github.com/wealthcx01/fountainbridge/pull/1",
        body_md="# FB-001 …",
    )


def _approval() -> Approval:
    return Approval(
        id="appr-1",
        venture_id="the-reset",
        kind=ApprovalKind.PR,
        source_ref="https://github.com/wealthcx01/fountainbridge/pull/1",
        summary="FB-001 scaffold awaiting the engineering gate",
        requested_at=_now(),
        state=ApprovalState.PENDING,
    )


def _run_report() -> RunReport:
    return RunReport(
        lane_id="platform",
        started_at=_now(),
        ended_at=_now(),
        trigger=RunTrigger.SCHEDULED,
        summary_md="Woke against the queue; nothing actionable.",
        tickets_touched=[],
        outcome=RunOutcome.NO_USEFUL_WORK,
    )


ENTITIES = [_venture(), _lane(), _ticket(), _approval(), _department(), _run_report()]


@pytest.mark.parametrize("obj", ENTITIES, ids=[type(o).__name__ for o in ENTITIES])
def test_round_trip_both_directions(obj) -> None:
    """model -> json -> model and dict -> model -> json both reproduce the entity exactly."""
    model_cls = type(obj)

    # Direction 1: model -> json string -> model
    as_json = obj.model_dump_json()
    assert model_cls.model_validate_json(as_json) == obj

    # Direction 2: python dict -> model -> dict (stable)
    as_dict = obj.model_dump(mode="json")
    rebuilt = model_cls.model_validate(as_dict)
    assert rebuilt == obj
    assert rebuilt.model_dump(mode="json") == as_dict


def test_venture_carries_full_d7_matrix_and_nested_entities() -> None:
    v = _venture()
    assert {r.change_class for r in v.approval_matrix} == set(ChangeClass)
    # high-blast-radius is dual-approve (D7)
    hbr = next(r for r in v.approval_matrix if r.change_class is ChangeClass.HIGH_BLAST_RADIUS)
    assert hbr.approver is Approver.DUAL
    assert v.lanes[0].venture_id == v.id
    assert v.departments[0].gate is DepartmentGate.ACTIVEGRAPH


def test_venture_without_vps_is_valid() -> None:
    """A venture exists before FB-011 provisions its box."""
    v = Venture(id="arca", name="ARCA", founder=_founder())
    assert v.vps is None
    assert v.status is VentureStatus.DRAFT  # default


@pytest.mark.parametrize("bad_email", ["ross@gmail.com", "someone@googlemail.com", "no-at-symbol"])
def test_workspace_email_rejects_personal_and_invalid(bad_email: str) -> None:
    """D3: the founder identity must be a venture-domain Workspace account, never personal Gmail."""
    with pytest.raises(ValidationError):
        FounderIdentity(name="X", github_login="x", workspace_email=bad_email)


def test_workspace_email_is_normalized() -> None:
    f = FounderIdentity(name="Ross", github_login="ross", workspace_email="  Ross@TheReset.com ")
    assert f.workspace_email == "ross@thereset.com"


@pytest.mark.parametrize("model_cls", [Venture, Lane, Ticket, Approval, Department, RunReport])
def test_extra_fields_forbidden(model_cls) -> None:
    """extra='forbid' on every entity — a manifest typo fails loud, never silently ignored."""
    payload = {"totally_unknown_field": 1}
    with pytest.raises(ValidationError):
        model_cls.model_validate(payload)


def test_ticket_status_values_match_workflow() -> None:
    assert [s.value for s in TicketStatus] == ["todo", "in-progress", "pr-open", "done"]


def test_run_report_no_useful_work_is_not_an_error() -> None:
    rr = _run_report()
    assert rr.outcome is RunOutcome.NO_USEFUL_WORK
    assert rr.error_detail is None
