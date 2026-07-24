# ADR-0045 — GTM target & contact registry

- **Status:** Proposed (2026-07-23). Founder-directed (feedback 23/07/2026, item 16); ratifies
  with GRS-0193. Extends ADR-0027 (pipeline/GTM engine direction).
- **Deciders:** Founder (data assets in product), Engineering (model and scoping).
- **Normative source:** non-negotiable #5 (repository layer), #9 (scoping), ESTATE-
  RECONCILIATION policy (operator files referenced by path, never committed), existing SAR /
  scrub machinery.

## Context

Bruntsfield holds real GTM data assets — the audited Exchange Supplier List (1,001 supplier-
service rows with contacts), a 150-bank target list, and the LSEG influencer-map method proven
on Barclays Live — but the product has no home for them: prospects are hand-typed, contacts
exist only as rows on individual prospects, and the Bench radar has no external signal.

## Decision

1. **Two registry entities through the repository layer:** `targets` (institutions — name,
   country, segment, source provenance) and `contacts` (people — name, title, channel details,
   verification status, source provenance). Every imported row is stamped with its source file
   and import date.
2. **Scoping:** the target/contact registry is network-shared **read**; an advisor's pipeline
   claims (which targets they are working) remain private to them. Writes are operator/admin
   imports and explicit edits — never silent enrichment.
3. **Ingestion is operator-run, file-referenced:** import scripts read the operator's files
   from OneDrive paths and fail loud on malformed rows; source files are never committed.
4. **PII posture:** contacts are personal data — included in SAR export and scrub paths,
   excluded from committed fixtures, and never placed in generated artifacts without the
   compliance caveats the source method carries (see GRS-0194).
5. **Consumers:** Add-prospect autocomplete, prospect-detail contact panels, the Bench radar
   (provenance-cited suggestions), and the LSEG influencer-map generator.

## Consequences

- GTM data becomes a governed product asset instead of a spreadsheet estate.
- The registry is the substrate later automation (agentic outreach, GRS-0195) must go through —
  which is where the human-approval gate attaches.
- Import provenance makes every radar suggestion and contact row explainable and auditable.
