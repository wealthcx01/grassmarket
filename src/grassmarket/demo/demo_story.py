"""The demo account's coherent story (GRS-0208 scope 1).

The founder's complaint was that they *cannot follow a single example client through the platform
end to end*. The brokerage showcase (GRS-0159/GRS-0236) already gives one owner three fully scored
firms with deliverables, example reports and commission lines — but three finalised assessments and
three contracted prospects is not a *pipeline*. Every card sits in one column, nothing is in flight,
and no workshop ever happened. A first-time user sees a filing cabinet rather than a business.

This module adds what the showcase does not produce, on the same account:

- **prospects at every pipeline stage**, so the board has columns rather than a single stack;
- **one assessment in progress**, so the wizard has something to resume and the portfolio shows a
  state other than finalised;
- **workshops with real stage history**, because the workshop is the step that turns a prospect into
  an engagement and the demo had no example of it.

It **adds to** the showcase rather than replacing it. The showcase's three firms are the part with
real scored data behind them; recreating that here would mean two sources of truth for the same
story. What this owns is the surrounding shape.

Idempotent, like everything else in the seed: it keys on the prospect's company name, so re-running
leaves the counts identical (GRS-0177).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from bcap_contracts.entities import PipelineStage


@dataclass(frozen=True)
class StoryProspect:
    """One prospect and the stage it should come to rest in.

    `path` is the stage sequence to walk, not just the destination: the pipeline validates
    transitions, and a card that teleported to `delivered` would carry no time-in-stage history —
    which is precisely the thing the board's flags are computed from. Walking the path is what makes
    the demo board show ageing cards rather than a wall of identical timestamps.
    """

    company_name: str
    path: tuple[PipelineStage, ...]
    note: str


# One prospect per stage the board can show. The names are plausible mid-market UK and EU firms and
# are deliberately NOT the showcase three — a first-time user should be able to tell at a glance
# which records carry a real scored assessment behind them and which are pipeline colour.
STORY_PROSPECTS: tuple[StoryProspect, ...] = (
    StoryProspect(
        "Calderwood Securities",
        (PipelineStage.PROSPECT,),
        "Cold, sourced from the T+1 readiness list. Nothing has happened yet, and the board should "
        "show that honestly rather than hiding untouched work.",
    ),
    StoryProspect(
        "Northgate Wealth",
        (PipelineStage.WORKSHOP_SCHEDULED,),
        "Workshop booked. This is the card an advisor is most likely to be looking at on a Monday.",
    ),
    StoryProspect(
        "Tay Bridge Capital",
        (PipelineStage.WORKSHOP_SCHEDULED, PipelineStage.WORKSHOP_DELIVERED),
        "Workshop delivered, output written, decision pending — the moment the recovery fee "
        "exists.",
    ),
    StoryProspect(
        "Lothian Markets",
        (
            PipelineStage.WORKSHOP_SCHEDULED,
            PipelineStage.WORKSHOP_DELIVERED,
            PipelineStage.QUALIFIED,
        ),
        "Qualified off the workshop. A real gap was found and the client agreed it is worth "
        "sizing.",
    ),
    StoryProspect(
        "Fettes Clearing",
        (
            PipelineStage.WORKSHOP_SCHEDULED,
            PipelineStage.WORKSHOP_DELIVERED,
            PipelineStage.QUALIFIED,
            PipelineStage.SCOPED,
        ),
        "Scoped: the engagement has a shape and a number, and is waiting on their side.",
    ),
    StoryProspect(
        "Dalkeith Asset Management",
        (
            PipelineStage.WORKSHOP_SCHEDULED,
            PipelineStage.WORKSHOP_DELIVERED,
            PipelineStage.QUALIFIED,
            PipelineStage.SCOPED,
            PipelineStage.CONTRACTED,
            PipelineStage.ACTIVE,
        ),
        "Live engagement. The assessment in progress belongs to this one, so the wizard has "
        "something to resume.",
    ),
    StoryProspect(
        "Granton Exchange Services",
        (
            PipelineStage.WORKSHOP_SCHEDULED,
            PipelineStage.WORKSHOP_DELIVERED,
            PipelineStage.QUALIFIED,
            PipelineStage.SCOPED,
            PipelineStage.CONTRACTED,
            PipelineStage.ACTIVE,
            PipelineStage.DELIVERED,
        ),
        "Delivered. The work is done and the invoice is the only thing left.",
    ),
    StoryProspect(
        "Corstorphine Brokers",
        (PipelineStage.NURTURE,),
        "Nurtured, not lost. Section 7 of the doctrine course is about exactly this card.",
    ),
    StoryProspect(
        "Bruntsfield Links Trading",
        (
            PipelineStage.WORKSHOP_SCHEDULED,
            PipelineStage.WORKSHOP_DELIVERED,
            PipelineStage.QUALIFIED,
            PipelineStage.CLOSED,
        ),
        "Closed without a sale. A demo with no losses in it teaches an advisor to expect the wrong "
        "thing.",
    ),
)

# The prospect whose assessment is left IN PROGRESS. Named here rather than inferred so the
# relationship is a decision in the source, not an accident of ordering.
IN_PROGRESS_SUBJECT = "Dalkeith Asset Management"

# Prospects that get a workshop record. Anything that has passed WORKSHOP_DELIVERED must have one,
# or the stage history claims a workshop happened and no workshop exists to show for it — the kind
# of quiet inconsistency a demo is worst placed to survive, because it is exactly what a careful
# viewer checks.
WORKSHOP_SUBJECTS: tuple[str, ...] = tuple(
    p.company_name for p in STORY_PROSPECTS if PipelineStage.WORKSHOP_DELIVERED in p.path
)


def workshop_dates(today: date, offset_days: int) -> tuple[date, date]:
    """(scheduled_for, delivered_on) for a workshop, spread backwards from today.

    Spread rather than identical: the pipeline's time-in-stage flags are computed from transition
    timestamps, and a demo where every card entered its stage on the same afternoon shows no ageing
    at all — which makes the board's most useful signal look broken.
    """
    delivered = today - timedelta(days=offset_days)
    return delivered - timedelta(days=7), delivered
