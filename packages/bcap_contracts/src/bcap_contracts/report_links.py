"""Shared client-report links and their read events (GRS-0220).

The founder asked for the review "as a PDF and as an interactive web page", and "ideally we can
track interaction from clients here too". This is the typed half of that: one unguessable link per
deliverable per client, no login, revocable, with an expiry the advisor sets — plus the per-section
read events it collects.

**The link is the credential, so it is treated like one.** Only a HASH of the token is stored. A
leaked database backup then yields no working links, the same reason a password column stores a
hash. The plaintext token exists exactly once, in the response that creates it; if the advisor loses
it they issue a new link rather than recovering the old one.

**Tracking is disclosed, never covert.** `ReportReadEvent` records the section and dwell time and
nothing else — no IP, no user agent, no fingerprint, no third party. The page tells the reader that
the sender can see which sections were opened. That notice is a product requirement, and the
narrowness of this model is what makes it truthful.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.base import OwnedResource
from bcap_contracts.client_report import ReportSectionKind


def _as_utc(moment: datetime) -> datetime:
    """Treat a naive timestamp as UTC before comparing it.

    Everything is stored in UTC, but the two backing stores disagree about saying so: Postgres
    returns an aware datetime and SQLite (local dev and CI) returns a naive one. Comparing the two
    raises `TypeError`, which would make an expiry check crash rather than expire — the link would
    fail closed here, but only because the whole request 500s, and a security control that works by
    crashing is not a control. Normalising makes the comparison mean what it says on both stores.
    """
    return moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment


class LinkState(StrEnum):
    """Why a link does or does not currently resolve."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ClientReportLink(OwnedResource):
    """One shareable link to one deliverable's client report.

    Scoped to exactly one deliverable and carrying no session: possessing the token grants sight of
    that report and nothing else. There is no widening from here to a client portal — that is
    explicitly out of scope, and the model's shape is what keeps it out.
    """

    model_config = ConfigDict(extra="forbid")

    deliverable_id: UUID
    engagement_id: UUID
    #: SHA-256 of the token. The plaintext is returned once, at creation, and never stored.
    token_hash: str = Field(min_length=64, max_length=64)
    #: Who the advisor sent it to. Free text — this is a label for the advisor, not an account.
    recipient_label: str = Field(min_length=1, max_length=200)
    expires_at: datetime
    revoked_at: datetime | None = None
    last_viewed_at: datetime | None = None

    def state(self, *, now: datetime) -> LinkState:
        """Revocation beats expiry: a revoked link is revoked whatever the clock says."""
        if self.revoked_at is not None:
            return LinkState.REVOKED
        if _as_utc(now) >= _as_utc(self.expires_at):
            return LinkState.EXPIRED
        return LinkState.ACTIVE

    def is_usable(self, *, now: datetime) -> bool:
        return self.state(now=now) is LinkState.ACTIVE


class ReportReadEvent(BaseModel):
    """One section of one shared report, seen for a measured time.

    Deliberately narrow. Section and dwell are what let an advisor prepare for a follow-up call;
    anything more would be surveillance the page's own notice does not admit to.
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID
    link_id: UUID
    section: ReportSectionKind
    #: Milliseconds the section was actually on screen. Never negative, and capped by the caller.
    dwell_ms: int = Field(ge=0, le=6 * 60 * 60 * 1000)
    occurred_at: datetime

    @model_validator(mode="after")
    def _dwell_is_plausible(self) -> ReportReadEvent:
        # A tab left open overnight is not reading. The cap keeps a stray total from telling the
        # advisor a client studied the appendix for nine hours.
        if self.dwell_ms > 6 * 60 * 60 * 1000:  # pragma: no cover - Field(le=) covers it
            raise ValueError("dwell_ms exceeds the plausible cap")
        return self


class SectionReadSummary(BaseModel):
    """What the advisor sees for one section: was it opened, and for how long in total."""

    model_config = ConfigDict(extra="forbid")

    section: ReportSectionKind
    views: int = Field(ge=0)
    total_dwell_ms: int = Field(ge=0)
    first_viewed_at: datetime | None = None
    last_viewed_at: datetime | None = None


class ReportReadReport(BaseModel):
    """The whole read picture for one link, as the advisor's deliverable page shows it."""

    model_config = ConfigDict(extra="forbid")

    link_id: UUID
    recipient_label: str
    state: LinkState
    sections: list[SectionReadSummary]

    @property
    def opened(self) -> bool:
        """Whether the recipient opened the report at all — the first thing an advisor asks."""
        return any(summary.views > 0 for summary in self.sections)
