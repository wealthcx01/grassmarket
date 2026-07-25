"""Influencer maps for a GTM target (GRS-0194, ADR-0045).

The Barclays Live exercise proved the method: LSEG/I-B-E-S contributor records reconstruct a bank's
research organisation into a ranked influence map with a named path to the platform's owners. This
is that artifact, made repeatable for any target with a curated contributor id.

The artifact is deliberately **two-source**, and the split is visible in the types rather than left
to a convention. `InfluencerRank` rows come from LSEG and are never verified, because the
contributor-to-institution mapping is inferred from email domains (GRS-0200 method fact 2).
`InfluencerOwner` rows are the ownership and leadership layer, which a human established by web
research and which carries its own verification status. An unverified owner row renders flagged and
is never presented as confirmed.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

# Rendered on every generated map. Sell-side research sits behind compliance controls, so an
# advisor needs the posture in front of them at the moment they read the names, not in a policy
# document somewhere else.
INFLUENCER_MAP_CAVEAT = (
    "Communications to sell-side research staff are compliance-logged by their firm, so treat "
    "every name here as a route to an introduction rather than a cold-outreach list. A warm "
    "referral through the ownership path below reaches the platform owner far more reliably than "
    "an unsolicited email to an analyst, and it does not put the recipient in an awkward position."
)


class InfluencerRank(BaseModel):
    """One ranked analyst, reconstructed from the LSEG roster fields for the sampled tickers."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1)
    full_name: str = Field(min_length=1)
    job_role: str | None = None
    email: str | None = None
    phone: str | None = None
    covered_rics: tuple[str, ...] = Field(
        default=(), description="Sampled tickers this analyst was returned against."
    )
    estimate_rating: int | None = Field(
        default=None, ge=0, le=100, description="TR.OverallAnalystEstimateRating, 0-100."
    )
    recommendation_rating: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="TR.OverallAnalystRecommendationRatingT24M, 0-100, epoch-decoded on ingest.",
    )
    tenure_start: date | None = Field(
        default=None, description="TR.AnalystCreateDate — the tenure signal, not a hire date."
    )
    verified: bool = Field(
        default=False,
        description="Always false for an LSEG-derived row: the institution is inferred, not "
        "confirmed. The field exists so the renderer treats both layers identically.",
    )


class InfluencerOwner(BaseModel):
    """One row of the ownership and leadership layer, established by human web research."""

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=1)
    job_role: str | None = None
    verified: bool = Field(
        default=False,
        description="True only where a human confirmed the person and role against a named "
        "source. Anything partial or unconfirmed stays false and renders flagged.",
    )
    source: str = Field(min_length=1)


class InfluencerMapProvenance(BaseModel):
    """What this map was built from, so a reader can judge and reproduce it."""

    model_config = ConfigDict(extra="forbid")

    generated_on: date
    ctb_id: int = Field(description="The LSEG contributor id the roster was filtered to.")
    sample_rics: tuple[str, ...] = Field(min_length=1)
    connector: str = Field(min_length=1, description="Connector and version used for the pull.")
    rows_returned: int = Field(ge=0)
    rows_for_contributor: int = Field(ge=0)


class InfluencerMap(BaseModel):
    """The three-tab artifact: the ranked influencers, the ownership path, and the raw rows.

    `raw_rows` is retained because the ranking is a judgement built on top of the pull, and a
    reader who disagrees with the ranking must be able to see what it was computed from.
    """

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    provenance: InfluencerMapProvenance
    influencers: tuple[InfluencerRank, ...] = ()
    owners: tuple[InfluencerOwner, ...] = ()
    raw_rows: tuple[dict[str, str | None], ...] = ()
    caveat: str = INFLUENCER_MAP_CAVEAT
