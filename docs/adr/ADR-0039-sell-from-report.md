# ADR-0039 — Sell-from-report: product→gap fit as config, deterministic opportunity ranking

- **Status:** Accepted (2026-07-22). Founder-requested ("look at the Workbench and know what can be
  sold based on the report"), GRS-0162.
- **Date:** 2026-07-22
- **Deciders:** Engineering (within founder direction), per the demo-readiness program.
- **Normative source:** ADR-0001 (single registry, load-time key validation), ADR-0002 (two-track
  scoring; score-points and currency never mix in one equation), ADR-0023 (C reported alongside V),
  ADR-0026 (commission schedule is configuration), D9 (Not Assessed contributes to nothing).
- **Couples with:** GRS-0123 (product carrots — the live rate source), ADR-0029 (demo provenance —
  the showcase records this first demos on).

## Context

The assessment side and the sellable-product side are architecturally disconnected. The knowledge
that "product X fixes gap Y" exists only as un-parsed prose inside product-course lessons; nothing
ingests a finalised report and answers the advisor's most natural next question — *"so what do I
sell them?"* `product_carrot.py` prices products but takes no assessment; the wizard suggester
suggests inputs, not products; the roadmap ranks ΔV upgrades with no product SKUs.

Three forces shape the design:

1. **The mapping is knowledge, not code.** Which registry gaps a product addresses is authored
   commercial judgment that will change as the catalogue changes. It belongs in configuration
   (like the commission schedule, ADR-0026), validated at load against the single registry
   (ADR-0001) — never string-matched out of course prose at runtime.
2. **Recommendation must not price the gap.** ADR-0002's boundary: scores are dimensionless,
   commission is currency. A "top opportunity" computed as `gap × £` would fuse the two tracks and
   let a high-commission product outrank a deeper gap.
3. **Honesty about the unknown.** A module nobody assessed is not a gap (D9). Recommending a
   product against an unassessed module would manufacture a sales case from absence of data.

## Decision

**1. `product_fit.yaml` in `bcap_contracts/registry_data/` — the product→gap mapping as config.**
Per product: the infrastructure `modules`, customer-proposition `c_modules`, and `powers` it
addresses, plus a one-line `pitch`. `load_product_fit()` fails loud at load when a product id is
not in the commission catalogue, any key is unknown to the registry, or a product addresses
nothing. Every catalogue product must appear (a product with no authored fit is an explicit
`modules: []`-style decision, not an omission — the loader refuses a missing product).

**2. A deterministic join, no AI.** `sell_opportunities(document, …)` re-scores the finalised
document with the active coefficient set (the same deterministic engine path the portfolio's C
column uses) and, per product, collects its addressed targets that are **assessed and weak**:

- a V/C module is a gap iff it was assessed and its gate band is Basic or Developing (or gated);
- a power is a gap iff it was assessed and benefit or barrier is None/Emerging;
- **Not Assessed is never a gap** (D9) — it is reported separately as "not yet assessed", never
  as a reason to sell.

**3. Ranking is score-track only.** Products with at least one module gap rank first, ordered by
the **minimum q_m among their addressed gap modules** (deepest gap first — the bottleneck logic
advisors already know). Products with only power gaps follow, ordered by the weakest addressed
power strength (None before Emerging). Ties break on product_id. The Year-1 rate and worked £
example (the live carrot, GRS-0123) are **displayed alongside** each recommendation — they never
enter the ordering. Products whose addressed targets are all strong or unassessed are excluded.

**4. Surface and audience.** `GET /assessments/{id}/sell-opportunities` — owner-scoped, refused
(409) until the assessment is finalised (the sales case quotes a locked score, not a moving
draft). Rendered on the engagement detail view and the finalised assessment summary. This surface
is **advisor-facing only**: it never appears in a client deliverable (the client-facing
conflict/independence disclosure is a separate founder decision, GRS-0148 #4).

## Consequences

- Adding a product = one yaml stanza + one commission stanza; the recommendation engine needs no
  code change, and a typo'd key refuses to load rather than silently never matching.
- The ranking is reproducible from the stored document + versioned coefficients — an advisor can
  be told exactly why a product is listed ("OEMS q_m 0.31, your deepest addressed gap").
- Because commission never enters the ordering, a future rate change reorders nothing — only the
  displayed £ updates (non-retroactivity mirrors ADR-0026).
- The fit map is deliberately coarse (module-level). Subcomponent-level fits, effort/ΔV pairing
  with the roadmap, and client-facing phrasing are explicitly out of scope until the founder
  scopes them.
