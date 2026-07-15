# GRS-0057 — In-platform Advisor Guide (how-to / docs)

- **Loop:** — (documentation surface)
- **Status:** Done — requested in the 2026-07-15 fit-for-purpose review.
- **Rubric basis:** #4 (guided help for advisors), #7 (plain-language), #10 (orientation).

## What

A practical, in-product **Advisor Guide** at `/help` covering the whole workflow end to end, distinct
from `/guide` (which is the ATLAS *concepts* primer — B·P·L·V, evidence grades):

1. Getting started · 2. Pipeline · 3. Running an assessment · 4. Reading the score honestly ·
5. Deliverables (incl. the client-facing review step) · 6. Earnings · 7. Workbench · plus a
**Principles** section (honest uncertainty, two-track, AI-proposes/humans-approve, fail-loud).

Each section is numbered how-to steps with a "then" clarifier, a governance/gate callout where it
matters, and a button through to the live section. A contents bar jumps between topics; the guide
cross-links the ATLAS primer.

## Discoverability

A **Guide** link is always present in the app header (top-right), and the guide is a static, public
page (it carries guidance, never user data). It cross-links `/guide` and each workflow route.

## Exit criteria

- `/help` renders the full guide on desktop and mobile; the header Guide link reaches it; type-check
  / lint / build green. Content is plain-language and grounded in the actual workflows.
