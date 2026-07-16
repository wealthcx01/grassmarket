# GRS-0091 — Home IA / layout & the "Sections" grid

**Status:** Shipped
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** —
**Branch:** `grs-0091-home-ia-layout`

## What shipped

Replaced the flat, undifferentiated "Sections" tile grid with a **deliberate information architecture**
that prioritises the advisor's client-delivery work.

- **Two grouped clusters** instead of one grid:
  1. **"Your client work"** — the delivery **flow** in workflow order: **Pipeline → Your Brokerages
     (assess) → Deliverables**. Subtitled "Prospect, assess, deliver — the flow from a lead to a
     finished Platform Power Report." These three are numbered `01/02/03` because they genuinely are a
     sequence (the numbering encodes real order, not decoration).
  2. **"Grow & get paid"** — the secondary group: **Workbench**, **My Earnings**. No step numbers.
- **`SectionCard`** extracted so both groups share one card, with the step index shown only on the
  sequenced group.
- Coheres with the GRS-0089 welcome/context block above it (which points into this flow) and the
  GRS-0087 header account menu.

The section *set* was reconsidered and justified: the five live sections are retained but re-grouped by
whether they are **client delivery** or **advisor growth/earnings**, and the delivery group is ordered
by the actual prospect→assess→deliver sequence rather than carried over as an arbitrary tile order.

## Acceptance / verification

The home page presents a considered IA (two labelled groups, a sequenced primary flow, a secondary
group) rather than an undifferentiated grid; the ordering is justified by the delivery workflow; it
coheres with the welcome block + header menu. Frontend type-check · lint · vitest green.

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
