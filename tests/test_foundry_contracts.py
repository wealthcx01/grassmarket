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


# --- FB-059: the run outcomes a founder is actually shown ----------------------------------------
# The first cut had three outcomes (progress / no-useful-work / error). The Foundry lane
# distinguishes six states and the studio renders them differently, because "it could not get past
# its own review", "it is waiting for your decision" and "it crashed" call for three different
# actions from a founder. Collapsing them into `error` would be the silent failure fountainbridge's
# non-negotiable 10 exists to prevent.


def _report(**over: object) -> RunReport:
    base = {
        "lane_id": "sell",
        "started_at": _now(),
        "ended_at": _now(),
        "trigger": RunTrigger.SCHEDULED,
        "outcome": RunOutcome.PROGRESS,
    }
    base.update(over)
    return RunReport(**base)  # type: ignore[arg-type]


def test_every_lane_state_has_an_outcome_that_keeps_its_meaning() -> None:
    """Each of the lane's terminal states maps to a distinct outcome — no two collapse together."""
    outcomes = {
        RunOutcome.PROGRESS,
        RunOutcome.OPENED_PR,
        RunOutcome.NO_USEFUL_WORK,
        RunOutcome.BLOCKED,
        RunOutcome.AWAITING_APPROVAL,
        RunOutcome.ERROR,
    }
    assert len({o.value for o in outcomes}) == 6
    for outcome in outcomes:
        assert _report(outcome=outcome).outcome is outcome


def test_blocked_is_not_an_error() -> None:
    """A lane that stopped cleanly and wants a human is not a crash, and must not read as one."""
    assert RunOutcome.BLOCKED is not RunOutcome.ERROR
    blocked = _report(
        outcome=RunOutcome.BLOCKED,
        error_detail="Could not get this past its own review in 2 rounds; it needs a human.",
    )
    assert blocked.outcome is RunOutcome.BLOCKED
    assert blocked.error_detail is not None  # blocked owes the founder a reason too


def test_awaiting_approval_carries_finished_work_with_a_held_consequence() -> None:
    report = _report(
        outcome=RunOutcome.AWAITING_APPROVAL,
        summary_md="Drafted the invitation and proposed the send for your approval.",
    )
    assert report.outcome is RunOutcome.AWAITING_APPROVAL
    assert report.error_detail is None  # nothing went wrong


def test_opened_pr_can_carry_the_pull_request_it_refers_to() -> None:
    report = _report(
        outcome=RunOutcome.OPENED_PR, pr_url="https://github.com/wealthcx01/arca/pull/12"
    )
    assert report.pr_url is not None


def test_an_in_flight_run_has_neither_an_end_nor_an_outcome() -> None:
    in_flight = RunReport(
        lane_id="sell", started_at=_now(), trigger=RunTrigger.SCHEDULED, ended_at=None
    )
    assert in_flight.outcome is None
    assert in_flight.ended_at is None


def test_a_run_cannot_have_an_outcome_without_having_ended() -> None:
    """Otherwise the studio shows a finished run as permanently in flight, or the reverse."""
    with pytest.raises(ValidationError):
        RunReport(
            lane_id="sell",
            started_at=_now(),
            ended_at=None,
            trigger=RunTrigger.SCHEDULED,
            outcome=RunOutcome.PROGRESS,
        )
    with pytest.raises(ValidationError):
        RunReport(
            lane_id="sell",
            started_at=_now(),
            ended_at=_now(),
            trigger=RunTrigger.SCHEDULED,
            outcome=None,
        )


def test_in_flight_report_round_trips_both_ways() -> None:
    report = RunReport(lane_id="sell", started_at=_now(), trigger=RunTrigger.SCHEDULED)
    assert RunReport.model_validate(report.model_dump(mode="json")) == report
