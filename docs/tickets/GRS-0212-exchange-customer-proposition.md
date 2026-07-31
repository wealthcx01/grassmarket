# GRS-0212 — Customer Proposition for exchanges: research it, model it, ship it

**Status:** BLOCKED (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-26, staging review item 11). **Priority:** HIGH._
**Loop:** founder-feedback remediation, Wave 1. **Depends on:** the C-index work (GRS-0085/0086).

## Why

The Customer Proposition dimension was built around retail brokerages. An exchange has a different
customer base with different needs, and today the module asks an advisor assessing LSEG or
Deutsche Börse the questions we wrote for Hargreaves Lansdown. The founder asked us to research
what Customer Proposition actually means for an exchange and model it properly.

They named the customer groups themselves, and they are not one market:

- **Institutional participants** accessing the venue: banks, brokers, market makers, buy side.
- **Retail market participants** reaching the venue through an intermediary.
- **Business customers** buying from the exchange's other lines: technology and connectivity,
  market data, investor relations services, and listing services.

An exchange serving all four has four propositions, and its weakness is usually in one of them.
A single blended score hides exactly the thing an advisor is being paid to find.

## Scope

1. **Research, written up first** as `docs/Customer-Proposition-Exchanges-v1.md`, before any
   code. Sourced from the exchange supplier list and the LSEG dataset we already hold in `data/`,
   plus public exchange annual reports and segment disclosures. For each of the four customer
   groups: who they are, what they buy, what "good" looks like, what the observable evidence is,
   and how an advisor can actually assess it in a workshop.
2. **A segment-scoped C-dimension for exchanges.** The C-index taxonomy gains an exchange variant
   with subcomponents per customer group. Registry-validated keys like everything else
   (ADR-0001), coefficients versioned, no silent defaults.
3. **The wizard asks the right questions.** When the resolved segment is an exchange (see
   GRS-0210), the Customer Proposition module presents the exchange rubric. Retail brokerage
   records are untouched.
4. **Report treatment.** The deliverable reports the four groups separately as well as in
   aggregate, so "strong with institutions, weak on data and listings" is sayable. Feeds GRS-0211.
5. **Not Assessed stays honest.** An advisor who cannot assess the listings business marks it Not
   Assessed and it contributes nothing, per the standing property tests. No imputation.

## Test plan

1. Registry tests: every new exchange C key validates at load time; an unknown key is a load-time
   error.
2. Property tests, extended to the exchange taxonomy: monotonicity, bottleneck behaviour, N/A
   renormalisation, Not Assessed contributing nothing.
3. Segment routing test: an exchange assessment gets the exchange rubric, a retail brokerage gets
   the existing one, and nothing changes for existing records.
4. Golden master byte-identical for all existing fixtures. A new golden-master fixture is added
   for an exchange.
5. Standing gate: pytest, pyright, tsc, ESLint.

## Out of scope

- Changing the Platform Value (V) side of scoring. This is the C dimension only.
- Re-scoring any existing finalised record. Runs are immutable (#6).
- Non-exchange segments. Wealth managers and banks are a later ticket if the founder wants them.

## Acceptance

The founder reads the research document and recognises their market in it. An advisor assessing an
exchange is asked questions that make sense for an exchange, and the report says which of the four
customer groups is the weak one.

---

## Status reconciliation — 2026-08-01

**BLOCKED.** Blocked on founder decision **D1** (docs/FOUNDER-DECISIONS-2026-08.md). Exchange Customer Proposition needs the exchange coefficient/rubric authoring that D1 covers.
