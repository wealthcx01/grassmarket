# GRS-0162 — "What can I sell against this report" — assessment gaps → recommended products

**Status:** Done (2026-07-22, ADR-0039). `product_fit.yaml` (per-product modules/c_modules/powers +
pitch, fail-loud loader), `earnings/opportunities.py` deterministic join (gap = assessed-and-weak by
the report's own gate band; Not Assessed never a gap; ranked by min q_m — commission displayed, never
ordered on), `GET /assessments/{id}/sell-opportunities` (owner-scoped, finalised-only), panel on the
finalised wizard rail + engagement detail. Founder-requested ("look at the Workbench and know what can
be sold based on the report"). **Priority:** MED-HIGH — compelling demo feature + revenue narrative.

## Why

Today the assessment side and the sellable-product side are **architecturally disconnected**. The
knowledge that "product X fixes gap Y" exists only as un-parsed prose in course lessons
(`openbb_course.py:107/121/133/…`, benzinga/brandfetch equivalents). Nothing ingests a finalised report
and emits "sell these products to close these gaps":
- `earnings/product_carrot.py` prices products but takes no assessment.
- `assessments/suggester.py` suggests wizard INPUTS, not products.
- The Workbench "Opportunity Radar" (`workbench/bench.py:86`) is a generic prospect-research filler, not
  report-driven.
- `deliverables/roadmap.py` ranks infrastructure ΔV upgrades — no product SKUs.

So the advisor's most natural question after an assessment — *"so what do I sell them?"* — has no answer
in the product. It's also the clearest link from the (draft-scored) assessment to real commission.

## Scope

- Give each product a **structured mapping**: the registry module keys / powers / C-modules it addresses
  (e.g. OpenBB → Market Data + research/tooling; ConnectTrade → OEMS/order-types). Author from the
  existing course prose — but as data, not strings.
- A service that joins a finalised assessment's **weak modules / low subcomponents / roadmap** against
  that mapping and the live commission carrots → a ranked "Recommended to sell" list (gap addressed +
  Yr1 commission).
- Surface it on the engagement/deliverable view and/or a Workbench "Opportunities for this client" panel.
  (A hand-built illustration of the output shipped in the 2026-07-21 demo report artifact.)

## Acceptance

Opening a finalised assessment shows which represented products best address its gaps, with the gap and
the commission — no hard-coded per-client logic.
