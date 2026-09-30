"""The group-level register: every organisation Bruntsfield touches, and every person at one.

HC-005, plan D1 and D4. Holy Corner owns this register; the studios point at it.

**Why this is not `CompanyEntity`.** `entities.py` already has a canonical-company type, and it is
for something else: it is the reference data an *assessment subject* resolves to, so that "Revolut"
and "Revolut Ltd" collapse to one scored entity. This is the commercial register - who we have a
contract with, who owes us money, whose founder we back - and an organisation here may never be
assessed at all. Merging them would mean every counterparty acquiring an assessment shape it has no
use for, and every assessed company acquiring contract fields it will never fill. `organisation_id`
and `entity_id` are linked where both exist (Holy Corner's `organisation_links` table), which is the
honest relationship between two registers that overlap without being the same thing.

Nothing here is consumer code. Adding a model to the exported surface is a deliberate step in
``schemas.EXPORTED_MODELS``.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Pillar(StrEnum):
    """A Bruntsfield vertical. Three are live or building; three are names with a plan."""

    ADVISORY = "advisory"  # the Advisory Studio
    FOUNDRY = "foundry"  # the Foundry Studio
    CLIENTS = "clients"  # the client portal, not started
    BRIEFING = "briefing"
    EQUITY = "equity"
    COHORT = "cohort"


class OrganisationType(StrEnum):
    """What kind of organisation this is, from Holy Corner's point of view."""

    BROKERAGE_PLATFORM = "brokerage_platform"
    INFRASTRUCTURE_VENDOR = "infrastructure_vendor"
    DATA_PROVIDER = "data_provider"
    INVESTMENT_FIRM = "investment_firm"
    REGULATOR = "regulator"
    ASSOCIATION = "association"
    PARTNER = "partner"  # a commercial partner we advise or sell for
    CLIENT = "client"
    FOUNDER_VENTURE = "founder_venture"  # a Foundry venture, before and after spin-out
    OTHER = "other"


class OrganisationStatus(StrEnum):
    PROSPECT = "prospect"
    ACTIVE = "active"
    DORMANT = "dormant"
    CLOSED = "closed"


class Organisation(BaseModel):
    """One organisation, whichever pillar met it first.

    `pillar_flags` is a set rather than a single pillar deliberately: an Advisory partner today may
    be a Briefing subject tomorrow and an Equity target after that, and the register has to hold
    that without the record being duplicated once per pillar.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, description="Stable slug, e.g. 'openbb'.")
    canonical_name: str = Field(min_length=1, description="The name as it appears on a contract.")
    type: OrganisationType
    status: OrganisationStatus = OrganisationStatus.ACTIVE
    segment: str | None = Field(
        default=None, description="Coarse sector hint, e.g. 'Neobank' or 'Data infrastructure'."
    )
    countries: tuple[str, ...] = Field(
        default=(),
        description="ISO 3166-1 alpha-2 codes where this organisation operates or is registered.",
    )
    pillar_flags: tuple[Pillar, ...] = Field(
        default=(), description="Which Bruntsfield pillars have a relationship with this one."
    )
    aliases: tuple[str, ...] = Field(
        default=(), description="Other names the same organisation is known by."
    )
    domain: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _countries_look_like_codes(self) -> Organisation:
        for c in self.countries:
            if len(c) != 2 or not c.isalpha() or c != c.upper():
                raise ValueError(
                    f"country {c!r} is not an ISO 3166-1 alpha-2 code. 'US', not 'USA': a "
                    "register that accepts three spellings of one country cannot group by it."
                )
        return self


class RelationshipKind(StrEnum):
    """A typed edge between two organisations. Directional: `source` does this to `target`."""

    USES = "uses"
    OWNS = "owns"
    SUPPLIES = "supplies"
    COMPETES_WITH = "competes_with"
    PARTNERS_WITH = "partners_with"
    PARENT_OF = "parent_of"


class OrganisationRelationship(BaseModel):
    """ "A uses B", "A is the parent of B". Typed, so it can be asked about rather than read."""

    model_config = ConfigDict(extra="forbid")

    source_organisation_id: str = Field(min_length=1)
    target_organisation_id: str = Field(min_length=1)
    kind: RelationshipKind
    note: str | None = None

    @model_validator(mode="after")
    def _not_self_referential(self) -> OrganisationRelationship:
        if self.source_organisation_id == self.target_organisation_id:
            raise ValueError(
                "an organisation cannot have a typed relationship with itself; "
                f"both ends are {self.source_organisation_id!r}"
            )
        return self


class PersonKind(StrEnum):
    """What this person is to Bruntsfield. One person can only be one of these at a time here."""

    STAFF = "staff"
    CONSULTANT = "consultant"  # mirrored from the Advisory Studio
    FOUNDER = "founder"  # mirrored from the Foundry Studio
    CLIENT_CONTACT = "client_contact"
    COHORT = "cohort"


class Person(BaseModel):
    """One person, with every address that is them.

    `emails` is a tuple and not a single field because one person genuinely has several: the
    Managing Partner signs contracts from one address and is an administrator under another, and
    "who is this" must not depend on which one they happened to use.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    emails: tuple[str, ...] = Field(
        default=(), description="Every address that is this same person, lower-cased."
    )
    kind: PersonKind
    organisation_id: str | None = Field(
        default=None, description="The organisation they belong to, where they belong to one."
    )
    title: str | None = None

    @model_validator(mode="after")
    def _emails_are_lowercase_and_unique(self) -> Person:
        seen: set[str] = set()
        for e in self.emails:
            if "@" not in e:
                raise ValueError(f"{e!r} is not an email address")
            if e != e.lower():
                raise ValueError(
                    f"{e!r} must be lower-cased. A register that holds two casings of one address "
                    "holds two people."
                )
            if e in seen:
                raise ValueError(f"{e!r} is listed twice")
            seen.add(e)
        return self
