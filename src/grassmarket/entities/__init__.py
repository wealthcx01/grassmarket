"""Entity resolution (GRS-0100, ADR-0033). An assessment subject resolves to a canonical company via
the injectable `EntityRegistry` port. The shipped `StubEntityRegistry` is a small seeded in-repo
list; `DbEntityRegistry` (GRS-0193) serves the imported GTM universe from the database behind the
same port, merged over that seed."""

from grassmarket.entities.registry import (
    DbEntityRegistry,
    EntityRegistry,
    RegistryReader,
    StubEntityRegistry,
    active_entity_registry,
    rank_name,
    to_company_entity,
)

__all__ = [
    "DbEntityRegistry",
    "EntityRegistry",
    "RegistryReader",
    "StubEntityRegistry",
    "active_entity_registry",
    "rank_name",
    "to_company_entity",
]
