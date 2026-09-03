"""The one needs-you queue (GRS-0253, Backend Request R1, gap G5).

`GET /queue` answers a single question — *what is waiting on me?* — for the caller, oldest first.

Before this, four surfaces each composed the same merge across separate endpoints, which meant the
rail badge could show a different number from the page it linked to. There is now one list, one
order, and one count, all derived on read so none of them can go stale.

**It never refuses on behalf of a source the caller has no role in.** A source that is not the
caller's business contributes nothing; it does not fail the request. Everyone may ask what is
waiting on them, and for most advisors the honest answer is simply short.
"""

from __future__ import annotations

from datetime import UTC, datetime

from bcap_contracts.needs_you import NeedsYouQueue
from fastapi import APIRouter, Depends

from grassmarket.data.repository import Principal, Repository
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("", response_model=NeedsYouQueue)
def needs_you_queue(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> NeedsYouQueue:
    """Everything waiting on the caller, oldest first, plus what this queue cannot currently see.

    `dormant` is not padding. Peer rating is retired under ADR-0041, and a queue that silently
    omitted it would make "that source is switched off" look identical to "you are up to date".
    """
    return repo.get_needs_you_queue(principal, now=datetime.now(UTC))
