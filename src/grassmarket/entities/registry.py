"""The entity registry port + the shipped stub (GRS-0100, ADR-0033).

`EntityRegistry` is the injectable seam. `StubEntityRegistry` is a small, seeded, in-repo list of
well-known finance/fintech firms with ranked case-insensitive matching (exact > prefix > alias /
substring). It only ever PROPOSES candidates — it never auto-resolves a typed string to one entity
(the human picks; fail loud on ambiguity, CLAUDE.md #3). A real registry adapter drops in behind the
same port later without touching the endpoint, the storage, or the UI.
"""

from __future__ import annotations

from typing import Protocol

from bcap_contracts.entities import CompanyEntity, RegistryTarget


class EntityRegistry(Protocol):
    """The port the entity-lookup endpoint depends on — never a concrete data source."""

    def search(self, query: str, *, limit: int = 8) -> list[CompanyEntity]: ...

    def get(self, entity_id: str) -> CompanyEntity | None: ...


# The seed. Deliberately small — an uncovered subject is a first-class manual record, not an error;
# breadth arrives with the real registry adapter. (entity_id, name, aliases, domain, segment)
_SEED: tuple[CompanyEntity, ...] = (
    CompanyEntity(
        entity_id="revolut",
        name="Revolut",
        aliases=("Revolut Ltd", "Revolut Group"),
        domain="revolut.com",
        segment="Neobank",
    ),
    CompanyEntity(
        entity_id="monzo",
        name="Monzo",
        aliases=("Monzo Bank", "Monzo Bank Ltd"),
        domain="monzo.com",
        segment="Neobank",
    ),
    CompanyEntity(
        entity_id="starling",
        name="Starling Bank",
        aliases=("Starling",),
        domain="starlingbank.com",
        segment="Neobank",
    ),
    CompanyEntity(
        entity_id="nubank",
        name="Nubank",
        aliases=("Nu Holdings", "Nu Pagamentos"),
        domain="nubank.com.br",
        segment="Neobank",
    ),
    CompanyEntity(
        entity_id="wise",
        name="Wise",
        aliases=("TransferWise", "Wise plc"),
        domain="wise.com",
        segment="Payments",
    ),
    CompanyEntity(
        entity_id="robinhood",
        name="Robinhood",
        aliases=("Robinhood Markets",),
        domain="robinhood.com",
        segment="Broker",
    ),
    CompanyEntity(
        entity_id="interactive-brokers",
        name="Interactive Brokers",
        aliases=("IBKR", "IB"),
        domain="interactivebrokers.com",
        segment="Broker",
    ),
    CompanyEntity(
        entity_id="charles-schwab",
        name="Charles Schwab",
        aliases=("Schwab", "The Charles Schwab Corporation"),
        domain="schwab.com",
        segment="Broker",
    ),
    CompanyEntity(
        entity_id="etoro",
        name="eToro",
        aliases=("eToro Group",),
        domain="etoro.com",
        segment="Broker",
    ),
    CompanyEntity(
        entity_id="stripe",
        name="Stripe",
        aliases=("Stripe Inc",),
        domain="stripe.com",
        segment="Payments",
    ),
    CompanyEntity(
        entity_id="plaid",
        name="Plaid",
        aliases=("Plaid Inc",),
        domain="plaid.com",
        segment="Fintech infra",
    ),
    CompanyEntity(
        entity_id="chime",
        name="Chime",
        aliases=("Chime Financial",),
        domain="chime.com",
        segment="Neobank",
    ),
    CompanyEntity(
        entity_id="klarna",
        name="Klarna",
        aliases=("Klarna Bank",),
        domain="klarna.com",
        segment="Payments",
    ),
    CompanyEntity(
        entity_id="coinbase",
        name="Coinbase",
        aliases=("Coinbase Global",),
        domain="coinbase.com",
        segment="Crypto exchange",
    ),
    CompanyEntity(
        entity_id="meridian-securities",
        name="Meridian Securities",
        aliases=("Meridian",),
        domain=None,
        segment="Broker",
    ),
)


def rank_name(name: str, aliases: tuple[str, ...], q: str) -> int | None:
    """Lower is better; None means no match. exact(0) < name-prefix(1) < alias-exact(2) <
    name-substring(3) < alias-substring(4).

    Kept as a free function on (name, aliases) rather than on `CompanyEntity` so the DB-backed
    registry (GRS-0193) ranks its rows through this exact function. One implementation means the
    imported corpus cannot drift from the stub's behaviour — only its size differs.
    """
    lowered = [n.lower() for n in (name, *aliases)]
    if name.lower() == q:
        return 0
    if name.lower().startswith(q):
        return 1
    if q in lowered:
        return 2
    if q in name.lower():
        return 3
    if any(q in n for n in lowered):
        return 4
    return None


def _rank(entity: CompanyEntity, q: str) -> int | None:
    return rank_name(entity.name, entity.aliases, q)


class StubEntityRegistry:
    """The shipped deterministic registry (a seeded in-repo list)."""

    def __init__(self, entities: tuple[CompanyEntity, ...] = _SEED) -> None:
        self._entities = entities
        self._by_id = {e.entity_id: e for e in entities}

    def search(self, query: str, *, limit: int = 8) -> list[CompanyEntity]:
        q = query.strip().lower()
        if not q:
            return []
        ranked = [(r, e) for e in self._entities if (r := _rank(e, q)) is not None]
        ranked.sort(key=lambda re: (re[0], re[1].name))
        return [e for _, e in ranked[:limit]]

    def get(self, entity_id: str) -> CompanyEntity | None:
        return self._by_id.get(entity_id)


def to_company_entity(target: RegistryTarget) -> CompanyEntity:
    """The pure adapter from an imported registry row to the search port's contract (GRS-0193).

    Only the identifying fields cross: the LSEG-specific columns (ric, ctb_id) and the provenance
    columns stay on `RegistryTarget`, because `CompanyEntity` is what an assessment subject links
    to and must not grow a dependency on where the row was imported from.
    """
    return CompanyEntity(
        entity_id=target.target_id,
        name=target.name,
        aliases=target.aliases,
        domain=target.domain,
        segment=target.segment,
    )


class RegistryReader(Protocol):
    """The slice of the repository the DB-backed registry needs.

    Declared here as a Protocol rather than importing `Repository` so the dependency runs one way
    only (repository → entities), leaving this module free of any storage import.
    """

    def search_registry_targets(self, query: str, *, limit: int = 8) -> list[RegistryTarget]: ...

    def get_registry_target(self, target_id: str) -> RegistryTarget | None: ...

    def count_registry_targets(self) -> int: ...


class DbEntityRegistry:
    """The imported GTM universe behind the unchanged `EntityRegistry` port (GRS-0193, ADR-0045).

    Merges with the stub seed rather than replacing it: an import brings in thousands of
    institutions, but the demo subjects (Revolut, Interactive Brokers, Meridian Securities) are
    seeded in-repo and must stay resolvable, or every seeded demo assessment loses its subject link.
    Imported rows win on an id collision, because a curated import is better data than the seed.
    """

    def __init__(self, reader: RegistryReader, *, stub: StubEntityRegistry | None = None) -> None:
        self._reader = reader
        self._stub = stub if stub is not None else StubEntityRegistry()

    def search(self, query: str, *, limit: int = 8) -> list[CompanyEntity]:
        imported = [
            to_company_entity(t) for t in self._reader.search_registry_targets(query, limit=limit)
        ]
        seen = {e.entity_id for e in imported}
        merged = imported + [
            e for e in self._stub.search(query, limit=limit) if e.entity_id not in seen
        ]
        # Re-rank the merged set so a stub hit that matches better than an imported one still leads.
        q = query.strip().lower()
        ranked = [(r, e) for e in merged if (r := _rank(e, q)) is not None]
        ranked.sort(key=lambda re: (re[0], re[1].name))
        return [e for _, e in ranked[:limit]]

    def get(self, entity_id: str) -> CompanyEntity | None:
        target = self._reader.get_registry_target(entity_id)
        if target is not None:
            return to_company_entity(target)
        return self._stub.get(entity_id)


_ACTIVE = StubEntityRegistry()


def active_entity_registry(reader: RegistryReader | None = None) -> EntityRegistry:
    """The registry the app resolves against right now. Route every lookup through here so the
    registry swap stays a single-point change (ADR-0033).

    With no reader, or with an empty `registry_targets` table, this is the seeded stub — a fresh
    development database resolves subjects exactly as before. Once an import has populated the
    table, it is the DB-backed adapter merged over that same seed.
    """
    if reader is None:
        return _ACTIVE
    if reader.count_registry_targets() == 0:
        return _ACTIVE
    return DbEntityRegistry(reader, stub=_ACTIVE)
