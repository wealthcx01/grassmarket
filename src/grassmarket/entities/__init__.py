"""Entity resolution (GRS-0100, ADR-0033). An assessment subject resolves to a canonical company via
the injectable `EntityRegistry` port. The shipped `StubEntityRegistry` is a small seeded in-repo
list; a real registry (Companies House / LSEG / a vendor) drops in behind the same port later."""

from grassmarket.entities.registry import (
    EntityRegistry,
    StubEntityRegistry,
    active_entity_registry,
)

__all__ = ["EntityRegistry", "StubEntityRegistry", "active_entity_registry"]
