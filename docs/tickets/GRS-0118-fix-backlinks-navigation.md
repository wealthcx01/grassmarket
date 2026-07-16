# GRS-0118 — Fix backlinks / cross-screen navigation

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** —

## Why

Moving between the related screens — engagement ↔ assessment ↔ deliverable ↔ pipeline/prospect ↔
portfolio — is annoying because back-links are missing or inconsistent, so a user regularly dead-ends and
has to navigate up via the global nav or the browser back button. This is a navigation-hygiene fix: audit
the flow and add consistent breadcrumbs / back-links so every screen has an obvious way back to the
context that led to it. It is copy/UI plumbing only, no data-model change, and is independent of the demo
and link-legibility work.

## What to build

**Cross-screen navigation audit + shared breadcrumb/back-link**
- Audit the entry/exit paths across `app/engagements/[id]/`, `app/assessments/[id]/`, and
  `app/prospects/[id]/` and map where a user can arrive and where they currently dead-end.
- Add a **shared nav/breadcrumb component** and apply it consistently so each of these screens shows its
  place in the flow and a reliable back-link. REUSE one shared component rather than hand-rolling
  per-screen back buttons, so the pattern stays consistent as new screens are added.

## Acceptance / verification

- Each of engagement, assessment, and prospect detail screens shows a consistent breadcrumb / back-link.
- A user can navigate the full chain (portfolio → assessment → engagement → deliverable → prospect) and
  back without dead-ending or resorting to the browser back button.

## Not in scope

- The two-way engagement↔assessment information link — GRS-0116.
- Any global-nav / header changes beyond the shared breadcrumb component.
