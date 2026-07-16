# GRS-0080 — C registry section + 93-widget Level-1 layer

**Status:** Planned
**Loop:** Loop 7 — C-index (Customer Proposition)
**Depends on:** ADR-0023 (Accepted), ATLAS-Methodology-v1.3

## Why

ADR-0023 ratifies a fourth composite index — C (Customer Proposition) — alongside B/P/L, built
on the Phase-E 10-module set. Nothing scores without a registry entry, and ADR-0001 makes an
unknown or missing key a load-time error. Before any engine, rubric, or wizard work, the registry
must carry the C modules, their subcomponents, and the Level-1 widget taxonomy that the retail
customer profile is assessed against. This ticket lays that foundation and nothing more.

## What to build

Files:
- `src/grassmarket/atlas/registry.py` — extend the loader/model to carry a C module section.
  Respect the existing uniqueness invariant (`registry.py:382`): every C module / subcomponent /
  widget key must be globally unique across the B/P/L keyspace and fail loud on collision.
- `src/grassmarket/atlas/data/registry_c.yaml` (new) — the C section content: 10 Phase-E modules,
  their subcomponents, and the 93-widget Level-1 layer.

The 10 Phase-E modules (keys, verbatim):
`CUST_ONBOARDING`, `CUST_UI_NAVIGATION`, `CUST_TRADING_EXPERIENCE`, `CUST_PRODUCT_RANGE`,
`CUST_RESEARCH_EDUCATION`, `CUST_AI_PERSONALISATION`, `CUST_SECURITY_REGULATION`,
`CUST_SUPPORT_COMMUNITY`, `CUST_FEES_PRICING`, `CUST_INNOVATION_DIFFERENTIATORS`.

Widget layer:
- 93 Level-1 widgets across 15 categories, each carrying a **rarity tag**: Common / Uncommon / Rare.
- **Profile-aware:** the retail widget taxonomy is scoped to the retail profile only
  (depends on GRS-0077 / GRS-0078 profile machinery). A non-retail profile must not see or be
  scored against retail widgets.
- Source structure (read-only reference for authoring — do not import at runtime):
  `…/Business/Briefing/Content-Bank/Projects/Brokerage-App-Reviews/*/…WidgetChecklist_COMPLETED_Claude.md`
  (15 categories, 93 widgets).

Reuse:
- The registry loader + ADR-0001 uniqueness/validation machinery extend to C modules unchanged —
  C keys validate against the single registry at load time exactly as B/P/L keys do.

New:
- The rarity dimension (Common/Uncommon/Rare) on widget rows.
- The profile scoping tag on the widget taxonomy.

## Acceptance / verification

- Registry loads with all 10 C modules, their subcomponents, and 93 widgets; total widget count
  asserted at exactly 93 across 15 categories.
- Every widget carries a rarity tag ∈ {Common, Uncommon, Rare} and a retail-profile scope.
- A duplicate C key (module, subcomponent, or widget) is a load-time error (uniqueness test).
- A widget with a missing or unknown rarity tag fails loud (no default).
- Existing B/P/L registry tests stay green; golden master is untouched (no engine change here).

## Not in scope

- Rubric anchors for the C modules — GRS-0081.
- Any scoring engine change or coefficients — GRS-0082.
- Wizard capture UI — GRS-0083.
- Folding C into V — GRS-0086.
