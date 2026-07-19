# GRS-0147 — Segment fit: wealth operating model + segment-native metric taxonomies

**Status:** Surfaced for founder / methodology decision — NOT autonomously buildable
**Loop:** Part 2 — mock-advisor stress test / segment fit

## The finding (all 5 personas)

The product's method impressed every persona; the **fit to their segment did not**. Concrete, cross-
persona:

- **No wealth operating model.** The wizard offers only *Retail brokerage* and *Exchange / market
  infrastructure*. Both wealth personas (St. James's Place, Brewin Dolphin) had to mislabel their firm
  as "Retail brokerage" — while the Academy treats "wealth manager" as a first-class segment. An
  internal contradiction a wealth board would notice.
- **Retail-framed, GBP-locked metrics.** The metric set (Assets Under Administration, Active Clients,
  ARPU, Gross Margin, in GBP) is a custody/retail vocabulary. It fits neither an exchange (needs
  volume/ADV, cleared notional, listings, index/market-data revenue) nor a US neobroker (funded
  accounts, MAU/DAU, PFOF, net deposits, in USD).
- **Non-retail profiles self-flag "not client-usable."** Selecting Exchange shows "weights & criticals
  pending elicitation — scores indicative, not client-usable." Honest, but it means there is no
  defensible deliverable for the exchange personas' customers today.

## Why this is founder-gated

The operating-model set, the metric registry (units + normalisation anchors), and the per-profile
weight/critical elicitation are **methodology/registry** artefacts (ADR-0001, Methodology §5). Adding a
wealth model and segment-native metrics, and finishing non-retail elicitation, is exactly the
"settled methodology — change via ADR + version, not a silent edit" case.

## Scope to weigh
- A **Wealth / investment-management** operating model + a wealth-native infrastructure rubric
  (suitability, discretionary vs advisory mandates, custody, platform/AUM economics) instead of
  brokerage OEMS/App-Server modules.
- **Segment metric taxonomies** (exchange, retail, wealth) with declared units + anchors; multi-
  currency (the GBP lock).
- Finish **weight/critical elicitation** for non-retail so those profiles stop self-declaring
  non-client-usable.
- Optional: UK regulatory framing (Consumer Duty / SM&CR / MiFID suitability) that the wealth personas
  expected front-and-centre.

## Related
Metric **input-domain validation** (a negative −£999,999 AUA saved and scored — Marcus, HIGH) belongs
here: a correct guard needs per-metric domain bounds in the registry (some metrics, e.g. gross margin,
can legitimately be negative; AUA cannot), which is the same registry/methodology decision. See the
synthesis report `reports/mock-advisor-stress-test-2026-07-19.md`.
