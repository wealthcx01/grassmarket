# GRS-0134 — Guide / primer navigation shell

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** GRS-0092–0097 (primer depth); do this LAST, after the content tickets land

## Why

The primer is being expanded substantially (GRS-0092–0097 add rationale, provenance, the 7 Powers, evidence
grades, and reading-the-outputs depth), and Academy/product content will keep growing. As the founder put it,
once the new tickets land the guide gets "longer and longer and longer" and needs to be **easier to
navigate** — "a little library or a burger menu or something." A single long scroll stops working past a
certain length. This ticket adds the navigation shell so the guide stays browsable.

## What to build

**Frontend (`frontend/app/guide/page.tsx` + a nav/sidebar component)**
- A **navigation shell** for the guide: a table-of-contents / sidebar / burger menu that lists the sections
  and lets the reader jump to any of them, with the current section indicated.
- Structure the guide content into addressable sections (anchors) so the nav can target them.
- Responsive: a persistent sidebar on wide viewports, a burger/drawer on narrow ones.

**Sequencing**
- **Do this last** — after GRS-0092–0097 (and any Academy content that surfaces in the guide) have made the
  guide long enough to warrant it. Building the shell first would target content that doesn't exist yet.

## Acceptance / verification

- The guide renders a working table-of-contents / sidebar (with a burger/drawer on narrow viewports) that
  navigates to every major section.
- The current section is indicated as the reader scrolls or jumps.
- No regression to the primer content added by GRS-0092–0097.

## Not in scope

- The primer *content* itself (GRS-0092–0097).
- A site-wide navigation redesign beyond the guide (the workbench-hub nav link is GRS-0128; the header
  account menu is GRS-0087).
