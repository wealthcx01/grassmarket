# GRS-0088 — Remove the dev health chip from the dashboard

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** —

## Why

The dashboard carries a "System ok · v0.0.1" chip that reports API/DB health. This is dev-facing
plumbing: it means nothing to an advisor, and when it flips to a non-ok state it will alarm them about
something they can neither understand nor act on. A top-consultancy dashboard does not surface build
version or backend health to the operator using it. Remove the chip from the advisor-facing dashboard;
if the signal is worth keeping at all, it belongs on an admin-only system-status view, not the home
page.

## What to build

**Dashboard (`frontend/app/page.tsx`, `frontend/app/health-widget.tsx`)**
- Remove the health chip from the dashboard render in `app/page.tsx`.
- Either delete `health-widget.tsx` or, if the health signal should be retained, relocate it behind an
  admin-only system-status surface (not the advisor home). Do not leave it mounted on `page.tsx`.

## Acceptance / verification

- The "System ok · v0.0.1" chip no longer appears on the advisor dashboard.
- No advisor-facing surface renders API/DB health or build version.
- If retained, the health signal is reachable only from an admin-gated view.

## Not in scope

- Building a full admin system-status dashboard (only relocation, if the signal is kept).
- Any change to the underlying health endpoint itself.
