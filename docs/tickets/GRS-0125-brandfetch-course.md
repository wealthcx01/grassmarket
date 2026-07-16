# GRS-0125 — Brandfetch course (VM research)

**Status:** Planned
**Loop:** Part 2 — Bruntsfield Academy / Workbench (one program)
**Depends on:** ADR-0028 (Bruntsfield Academy / Workbench), GRS-0121 (content CMS), GRS-0123 (product-course framework)

## Why

Brandfetch is a **signed** product and a commission earner, so advisers need a course to learn how to
introduce and white-label it. No content exists yet; this is a **VM-research ticket** built the same way
as the Benzinga course (GRS-0124) — research first, then authored through the CMS.

## What to build

- The VM **spawns a research agent** over **Brandfetch's dev docs / APIs** to gather the course source
  material.
- Build our **own course catalog** framed by GRS-0123's template: relevance to retail broker / wealth
  manager / exchange, what white-labelling Brandfetch looks like, the sell/introduction motion, and the
  commission the advisor earns (via Earnings v7).
- Author the course **through GRS-0121's CMS**; any **AI-authored lesson drafts stay approval-gated**
  (ADR-0009).

## Acceptance / verification

- A Brandfetch course exists in the CMS with all GRS-0123 sections filled from researched Brandfetch
  material.
- AI-drafted lessons are published only after passing the approval gate (ADR-0009).
- The commission section resolves from Earnings v7 rates, consistent with GRS-0123.

## Not in scope

- The product-course template (GRS-0123) and the CMS (GRS-0121).
- Benzinga (GRS-0124) and OpenBB (GRS-0126) courses.
