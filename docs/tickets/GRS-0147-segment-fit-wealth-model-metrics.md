# GRS-0147 — Segment fit: wealth operating model + segment-native metric taxonomies

**Status:** BLOCKED (reconciled 2026-08-01). _Previously recorded as: Surfaced for founder / methodology decision — NOT autonomously buildable._
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

---

## Status reconciliation — 2026-08-01

**BLOCKED — partly built, with a founder-gated residue.** This umbrella ticket has no commit of its
own; its scope was delivered through lettered sub-tickets, and two scope items were never built.

**Built:**
- Wealth operating model — `bdd701b` (GRS-0147c). It is live: `atlas/active.py` registers
  `_WEALTH_PROFILE_KEY = "wealth"` with an **activated, client-usable** `elicited_wealth_coefficient_set`,
  so wealth appears in the wizard's operating-model dropdown and no longer self-flags "not client-usable".
- Wealth infrastructure taxonomy — `bd7e112` (GRS-0147d).
- Per-profile B-index metric selection — `06534f4` (GRS-0147b).
- Exchange operating model made native — `e038967` (GRS-0147g).
- Profile-aware scoreability copy — `bbfd4e6` (GRS-0147e) and graceful rubric guidance for unauthored
  wealth subcomponents — `a09cedf` (GRS-0147f). **Neither has a ticket file**; they shipped as
  sub-tickets of this one and are recorded here.

**NOT built — founder decision D4:**
- **Multi-currency.** The GBP lock the finding named is still in place: there is no currency field or
  normalisation anywhere in the registry or the assessment contracts.
- **UK regulatory framing** (Consumer Duty / SM&CR / MiFID suitability). The only trace in the product
  is a placeholder string in `frontend/components/steps.tsx:222` ("e.g. FCA-authorised; MiFID II
  passported") — a text hint, not the framing the wealth personas expected.

Elicitation for non-retail (scope item 3) is GRS-0150, blocked on **D1**.
