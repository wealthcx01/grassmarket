# GRS-0091 — Home IA / layout & the "Sections" grid

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** —

## Why

The founder's verdict on the home page: it reads *basic*, and the flat "Sections" grid prompts the
question "Is that the best use of space? Is that all the sections we need?" A top-consultancy dashboard
has a considered information architecture that puts the advisor's real work first, not an undifferentiated
tile grid. This ticket reworks the home layout and reconsiders the section set so the home page has a
professional, intentional IA.

## What to build

**Dashboard (`frontend/app/page.tsx`)**
- Rework the home layout: give the page a deliberate information architecture rather than a flat tile
  grid — prioritise the advisor's active work and next actions, and use the space with intent.
- Reconsider the section set itself: which sections belong on home, in what order, and at what prominence.
  Per-section deep-dives are handled by their own tickets; this ticket owns the home-level arrangement.

## Acceptance / verification

- The home page presents a considered IA (clear hierarchy, intentional use of space), not an
  undifferentiated section grid.
- The section set and ordering are reconsidered and justified, not carried over verbatim.
- The layout coheres with the welcome/context block (GRS-0089) and the header account menu (GRS-0087).

## Not in scope

- Per-section functionality changes (pipeline, wizard, workbench, etc. — their own tickets).
- The welcome copy (GRS-0089) and header chrome (GRS-0087), though this layout must accommodate them.
