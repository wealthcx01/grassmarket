"""Foundry Studio contracts (FB-002) — the entities the **fountainbridge** studio renders.

Decision D4: `bcap-contracts` is the shared type system where studios meet Holy Corner.
grassmarket (Advisory Studio) already consumes this package; fountainbridge (Foundry Studio)
renders these six entities. Scope is deliberately a type system, not a platform build.

These are **configuration / studio** entities, not consultant-scoped grassmarket resources, so
they do NOT extend `ResourceBase`/`OwnedResource` (which mandate a UUID id + audit timestamps).
Their ids are human, git-native slugs — a venture is ``the-reset``, a ticket is ``FB-001`` — so
each is a plain ``extra="forbid"`` model keyed by a string id. Venture isolation is enforced
server-side in the studio (fountainbridge CLAUDE.md), never by these shapes alone.

Nothing here is consumer code (no fountainbridge/grassmarket logic) — just the contracts. Adding
one to the exported schema surface is a deliberate step in ``schemas.EXPORTED_MODELS``.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Consumer-account email domains that a founder's venture identity must never be. D3/D6: the
# founder's studio login + agent send identity is a Bruntsfield-assigned account on the venture's
# Google Workspace domain (e.g. ross@thereset.com), never a personal consumer mailbox — that is
# what makes Google's internal-app OAuth exemption apply and keeps the founder's personal identity
# out of the blast radius (docs/research-gtm.md §1).
_CONSUMER_EMAIL_DOMAINS = frozenset({"gmail.com", "googlemail.com"})


# --------------------------------------------------------------------------- #
# Enumerations
# --------------------------------------------------------------------------- #
class VentureStatus(StrEnum):
    """Lifecycle of a venture in the studio."""

    DRAFT = "draft"  # manifest exists, not yet live (e.g. the-reset drafted from its deck)
    ACTIVE = "active"  # in the studio, running day-to-day
    PAUSED = "paused"  # temporarily halted, box may still exist
    ARCHIVED = "archived"  # wound down; kept for the record


class LaneStatus(StrEnum):
    """Health of a workshop lane (a Claude Code lane on the venture's VPS)."""

    ACTIVE = "active"  # working its queue
    IDLE = "idle"  # no work in flight, healthy
    STALE = "stale"  # no activity past the lane's staleness window (FB-008 flags this)
    ARCHIVED = "archived"


class TicketStatus(StrEnum):
    """Where a ticket sits in the one-ticket-one-branch-one-PR flow (FB-002 spec)."""

    TODO = "todo"
    IN_PROGRESS = "in-progress"
    PR_OPEN = "pr-open"
    DONE = "done"


class ApprovalKind(StrEnum):
    """What produced an approval item. Extensible pending FB-012's external-gate design — new
    kinds are additive, so the attention queue never needs a rewrite (FB-007)."""

    PR = "pr"  # an open pull request awaiting the human engineering gate
    ACTIVEGRAPH_POLICY = "activegraph_policy"  # an external-action approval event (email/social/…)


class ApprovalState(StrEnum):
    """Where an approval sits. Absence of a decision is ``pending``."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DepartmentGate(StrEnum):
    """How a department's actions are gated. GTM/external gates firm up post-FB-012."""

    PR = "pr"  # repo work — the proven PR gate
    ACTIVEGRAPH = "activegraph"  # external actions — recorded ActiveGraph approval events
    TBD_FB012 = "tbd-fb012"  # gate design still pending FB-012 ratification for this department


class RunTrigger(StrEnum):
    """What woke a lane for a run."""

    MANUAL = "manual"  # a human (SSH / studio) started it
    SCHEDULED = "scheduled"  # the per-venture scheduler woke it (Phase 2)


class RunOutcome(StrEnum):
    """How a lane run ended. ``no-useful-work`` is a first-class outcome — the pre-check that
    decides not to burn a session is a success, not a failure (Phase 2 scheduler)."""

    PROGRESS = "progress"
    NO_USEFUL_WORK = "no-useful-work"
    ERROR = "error"


class ChangeClass(StrEnum):
    """The blast-radius classes the D7 approval matrix routes on."""

    PRODUCT_VISIBLE = "product-visible"  # founder authority
    PLATFORM_INFRA = "platform-infra"  # Bruntsfield authority
    HIGH_BLAST_RADIUS = "high-blast-radius"  # migrations, auth, payments, secrets, external sends


class Approver(StrEnum):
    """Who must sign off a change class (D7). ``dual`` = both founder and Bruntsfield."""

    FOUNDER = "founder"
    BRUNTSFIELD = "bruntsfield"
    DUAL = "dual"


# --------------------------------------------------------------------------- #
# Sub-models
# --------------------------------------------------------------------------- #
class VpsBinding(BaseModel):
    """The venture's own VPS (Decision D1: one box per venture). Fields are populated by FB-011
    provisioning, so an un-provisioned venture carries ``vps=None`` and a provisioned one may
    still have ``provisioned_at=None`` until the runbook records it."""

    model_config = ConfigDict(extra="forbid")

    host: str = Field(min_length=1, description="Hostname or IP of the venture's VPS.")
    provider: str = Field(min_length=1, description="Infra provider, e.g. 'hetzner'.")
    provisioned_at: datetime | None = Field(
        default=None, description="When the box was provisioned; None until FB-011 records it."
    )


class FounderIdentity(BaseModel):
    """The human founder's identity across GitHub and Google Workspace.

    ``workspace_email`` is a Bruntsfield-assigned account on the venture's Workspace domain,
    managed by the founder — it is the studio login (Google OAuth) and the venture-scoping key
    (D6), never a personal consumer mailbox (D3). The validator refuses consumer domains so a
    misconfigured manifest fails loud instead of leaking the founder's personal identity into the
    send/auth path."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, description="The founder's human name.")
    github_login: str = Field(
        min_length=1, description="The founder's own GitHub account (D2: added as a collaborator)."
    )
    workspace_email: EmailStr = Field(
        description="Bruntsfield-assigned venture-domain Google Workspace account "
        "(e.g. ross@thereset.com). Never a personal @gmail.com.",
    )

    @field_validator("workspace_email")
    @classmethod
    def _reject_consumer_email(cls, value: str) -> str:
        # EmailStr has already validated the address shape; normalize and refuse consumer domains.
        email = value.strip().lower()
        domain = email.rsplit("@", 1)[1]
        if domain in _CONSUMER_EMAIL_DOMAINS:
            raise ValueError(
                "workspace_email must be a venture-domain Google Workspace account, "
                f"never a personal consumer mailbox (got {domain!r}). See D3 / research-gtm §1."
            )
        return email


class ApprovalRule(BaseModel):
    """One row of the D7 approval matrix: a change class and who must approve it."""

    model_config = ConfigDict(extra="forbid")

    change_class: ChangeClass
    approver: Approver


# --------------------------------------------------------------------------- #
# Entities (FB-002)
# --------------------------------------------------------------------------- #
class Lane(BaseModel):
    """A workshop lane bound to one venture repo (a Claude Code + tmux lane on the venture VPS)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, description="Lane id, unique within the venture.")
    venture_id: str = Field(min_length=1, description="The owning venture's id.")
    repo: str = Field(min_length=1, description="Repo this lane builds (slug or full name).")
    tmux: str = Field(min_length=1, description="tmux session/window binding on the VPS.")
    standing_order: str = Field(
        min_length=1, description="The lane's durable standing order (its brief between sessions)."
    )
    status: LaneStatus = LaneStatus.IDLE


class Department(BaseModel):
    """A venture department (engineering, GTM, ops, …) with its own repo/queue and gate."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, description="Department id, unique within the venture.")
    venture_id: str = Field(min_length=1, description="The owning venture's id.")
    name: str = Field(min_length=1, description="Human-readable department name.")
    repo: str = Field(min_length=1, description="Repo backing this department's work.")
    queue_path: str = Field(
        min_length=1, description="Path (in the repo) to the department's work queue."
    )
    connectors: list[str] = Field(
        default_factory=list, description="Connector names this department uses (e.g. 'stripe')."
    )
    gate: DepartmentGate


class Venture(BaseModel):
    """A co-created Foundry venture — the root config object the studio scopes everything to.

    Everything venture-specific lives here (venture-as-config); the studio core stays generic.
    ``vps`` and identities may be unset before FB-011 provisioning. The ``approval_matrix`` is the
    D7 governance record: which change class routes to which approver(s)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, description="Venture slug, e.g. 'the-reset' or 'arca'.")
    name: str = Field(min_length=1, description="Human-readable venture name, e.g. 'THE RESET'.")
    status: VentureStatus = VentureStatus.DRAFT
    tier3_ref: str | None = Field(
        default=None, description="Reference into the Tier 3 venture pack, if any."
    )
    vps: VpsBinding | None = Field(
        default=None, description="The venture's VPS binding; None until FB-011 provisions it."
    )
    founder: FounderIdentity
    approval_matrix: list[ApprovalRule] = Field(
        default_factory=list,
        description="D7: rules mapping each change class to its required approver(s).",
    )
    repos: list[str] = Field(default_factory=list, description="Repo slugs owned by this venture.")
    lanes: list[Lane] = Field(default_factory=list, description="Workshop lanes for this venture.")
    departments: list[Department] = Field(
        default_factory=list, description="Departments for this venture."
    )
    connectors: list[str] = Field(
        default_factory=list, description="Connector names available to the venture."
    )


class Ticket(BaseModel):
    """A work item, rendered from a ``docs/tickets/`` markdown file (git is the source of truth,
    D2). Parsed by FB-004; PR-derived status inference lands in FB-007."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, description="Ticket id, e.g. 'FB-001'.")
    repo: str = Field(min_length=1, description="Repo the ticket lives in.")
    path: str = Field(min_length=1, description="Path to the ticket file within the repo.")
    title: str = Field(min_length=1, description="Ticket title.")
    phase: str | None = Field(default=None, description="Phase label, if the ticket declares one.")
    depends_on: list[str] = Field(
        default_factory=list, description="Ids of tickets this one depends on."
    )
    status: TicketStatus = TicketStatus.TODO
    branch: str | None = Field(default=None, description="Branch name (fb-XXX-slug), if known.")
    pr_url: str | None = Field(default=None, description="URL of the open/merged PR, if any.")
    body_md: str = Field(default="", description="Rendered markdown body of the ticket.")


class Approval(BaseModel):
    """One item in the attention queue: something awaiting a recorded human decision (FB-007).

    v0 is engineering only (``kind=pr`` — every open workshop PR is by definition awaiting a
    human). External-action kinds join additively once FB-012's gate design lands."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, description="Approval id, unique within the venture.")
    venture_id: str = Field(min_length=1, description="The owning venture's id.")
    kind: ApprovalKind
    source_ref: str = Field(
        min_length=1, description="Reference to the thing being approved (PR url, event id, …)."
    )
    summary: str = Field(min_length=1, description="Plain-language summary of what needs a human.")
    requested_at: datetime
    state: ApprovalState = ApprovalState.PENDING
    decided_by: str | None = Field(
        default=None, description="Who decided (approver identity); None while pending."
    )
    decided_at: datetime | None = Field(
        default=None, description="When it was decided; None while pending."
    )


class RunReport(BaseModel):
    """The record a lane writes back after a run (Phase 2 scheduler; surfaced in the studio).

    Keyed by ``lane_id`` + ``started_at`` — a run has no separate id. ``no-useful-work`` is a
    legitimate outcome, not a failure, so nothing fails silently (fountainbridge non-negotiable)."""

    model_config = ConfigDict(extra="forbid")

    lane_id: str = Field(min_length=1, description="The lane this run belongs to.")
    started_at: datetime
    ended_at: datetime | None = Field(
        default=None, description="When the run ended; None while in flight."
    )
    trigger: RunTrigger
    summary_md: str = Field(default="", description="Plain-language markdown summary of the run.")
    tickets_touched: list[str] = Field(
        default_factory=list, description="Ids of tickets this run touched."
    )
    outcome: RunOutcome
    error_detail: str | None = Field(
        default=None, description="Failure detail when outcome is 'error'; None otherwise."
    )
