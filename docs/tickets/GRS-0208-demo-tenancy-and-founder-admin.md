# GRS-0208 — One clean demo account, and a founder admin who can act as any advisor

**Status:** Planned (2026-07-26, staging review item 6). **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 1.

## Why

The founder cannot follow a single example client through the platform end to end, even from the
admin account. The example data is spread across six seeded advisors, each holding one assessment,
so no account shows a pipeline, an assessment, a deliverable and an earnings line that belong to
the same story. Admin sees everything and therefore shows nothing coherent.

They asked for two accounts with different jobs:

- a **demo account** holding all the example profiles, so a walkthrough is one login,
- **john@bruntsfield.capital** as an admin who can act as any other advisor, so review means
  seeing exactly what that advisor sees.

The cross-advisor management view belongs in Holy Corner, not here. This ticket builds only what
Grassmarket needs to be demonstrable.

## Scope

1. **A single demo advisor holding the full worked example.** `scripts/seed_demo.py` seeds one
   account (`demo@bruntsfield.capital`) with a coherent story: prospects at every pipeline stage,
   two assessments finalised and one in progress, the deliverables generated from them, an
   engagement with workshops and stage history, and the earnings lines that follow. Every record
   is DEMO provenance and watermarked. The per-advisor scatter that exists today is replaced, not
   added to.
2. **Act-as, not impersonate-silently.** An admin principal may open a session scoped to another
   consultant. Implemented in the repository layer where scoping already lives (non-negotiable #9),
   so the acting-as principal is a real scoped principal and every existing scoping test still
   holds. Requirements:
   - only an admin may start it, and only against an existing consultant,
   - the UI shows a persistent banner naming the advisor being viewed and offering one click back,
   - every act-as session start and end is written to the audit log with both identities,
   - writes performed while acting as someone else are recorded with the acting admin's id as
     well as the subject's. No silent authorship.
3. **john@bruntsfield.capital provisioned as admin** through the domain SSO path (GRS-0173), not
   as a hand-seeded row.
4. **Staging seeded to match** and the two production strays currently on the advisor account
   (`Revolut` draft at 0% and `Meridian Securities` finalised at 2%) resolved by the founder's
   decision, since the cleanup tool will not remove production records (ADR-0047).

## Test plan

1. Scoping tests, extended: an admin acting as advisor A sees exactly what A sees and nothing
   more, and an admin not acting-as still cannot read A's records through advisor endpoints.
2. A non-admin cannot start an act-as session. Asserted at the repository layer.
3. Audit test: starting and ending act-as writes both identities.
4. `seed_demo.py` twice produces identical counts, extending the idempotence assertion GRS-0177
   added.
5. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- The cross-advisor management dashboard. That is Holy Corner.
- Deleting production records (ADR-0047 says no; the founder decides those two by hand).
- Any change to what advisors themselves can see.

## Acceptance

The founder logs in as john@bruntsfield.capital, switches to the demo advisor, and walks one
client from prospect to signed deliverable to commission without changing accounts or hitting a
gap.
