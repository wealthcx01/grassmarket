# GRS-0080 — C registry section + 93-widget Level-1 layer

**Status:** Shipped
**Loop:** Loop 7 — C-index (Customer Proposition)
**Depends on:** ADR-0023, ATLAS-Methodology-v1.3
**Branch:** `grs-0080-c-registry-and-widgets`

## Why

ADR-0023 adds C (Customer Proposition) as a fourth index alongside B/P/L. Nothing scores without a
registry entry (ADR-0001), so the registry must carry the C modules, their subcomponents, and the
Level-1 widget taxonomy before any engine/rubric/wizard work.

## What shipped

**Model (`packages/bcap_contracts/…/registry.py`)** — C is a **parallel dimension**, not folded into
the B/P/L `modules`, so the engine's L path never touches it and the golden master is byte-identical
(C rides *alongside* V in Stage 1):
- `CModuleDef` / `CSubcomponentDef`, `WidgetDef` (`key, name, category, rarity, module_key`) with
  `WidgetRarity = Literal["Common","Uncommon","Rare"]` (no default → missing/unknown rarity refuses
  at construction).
- `Registry` gains `c_modules`, `c_widgets`, `c_status`, `c_widget_profile` + accessors
  (`c_module_keys`, `widget_keys`, `require_c_module`, `widgets_for_profile`).
- `_assert_unique_keys` extended: C module keys share the one module keyspace; C subcomponent + widget
  keys are globally unique across the whole keyspace (fail loud on collision).
- Loader reads a new `registry_data/registry_c.yaml` (fail-loud `status`).

**Content (`registry_data/registry_c.yaml`)** — the 10 Phase-E modules (verbatim keys) with Level-2
subcomponents, and **93 widgets across 15 categories**, each with a rarity and mapped to a C module.
**Retail-scoped** (`profile: retail`) — `widgets_for_profile("exchange")` returns none.

> The module/subcomponent structure is the ratified Phase-E set; the widget taxonomy is authored from
> standard retail-brokerage-app-review structure and **must be reconciled against the founder's
> `WidgetChecklist_COMPLETED` (OneDrive, reference-only, never committed)** — status
> `draft-pending-ratification`.

## Acceptance

`tests/test_c_registry.py` — 10 C modules + 93 widgets × 15 categories; every widget has a valid
rarity + maps to a C module; retail-scoped (exchange sees none); B/P/L set + golden master untouched
(no C key leaks into the B/P/L keyspace); duplicate widget key / C-module-shadows-L-module / missing
rarity / missing status all fail loud. Schema regenerated (parity green).

## Not in scope

Rubric anchors (GRS-0081); the C scoring engine + coefficients (GRS-0082); wizard widget grid
(GRS-0083); C into V (GRS-0086, gated).
