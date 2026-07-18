"""The entity registry port + the shipped stub (GRS-0100, ADR-0033).

`EntityRegistry` is the injectable seam. `StubEntityRegistry` is a small, seeded, in-repo list of
well-known finance/fintech firms with ranked case-insensitive matching (exact > prefix > alias /
substring). It only ever PROPOSES candidates — it never auto-resolves a typed string to one entity
(the human picks; fail loud on ambiguity, CLAUDE.md #3). A real registry adapter drops in behind the
same port later without touching the endpoint, the storage, or the UI.
"""

from __future__ import annotations

from typing import Protocol

from bcap_contracts.entities import CompanyEntity


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


def _rank(entity: CompanyEntity, q: str) -> int | None:
    """Lower is better; None means no match. exact(0) < name-prefix(1) < alias-exact(2) <
    name-substring(3) < alias-substring(4)."""
    names = (entity.name, *entity.aliases)
    lowered = [n.lower() for n in names]
    if entity.name.lower() == q:
        return 0
    if entity.name.lower().startswith(q):
        return 1
    if q in lowered:
        return 2
    if q in entity.name.lower():
        return 3
    if any(q in n for n in lowered):
        return 4
    return None


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


_ACTIVE = StubEntityRegistry()


def active_entity_registry() -> EntityRegistry:
    """The registry the app resolves against right now (the stub). Route every lookup through here
    so the future real-registry swap is a single-point change (ADR-0033)."""
    return _ACTIVE
