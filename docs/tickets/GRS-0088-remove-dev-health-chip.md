# GRS-0088 — Remove the dev health chip from the dashboard

**Status:** Shipped
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** —
**Branch:** `grs-0088-remove-dev-health-chip`

## What shipped

Removed the dev-facing "System ok · v0.0.1" health chip from the advisor dashboard — it surfaced
API/DB health + build version, which mean nothing to an advisor and would alarm them on a non-ok
state. `HealthWidget` was mounted only on the home hero (`app/page.tsx`); deleted `app/health-widget.tsx`
and its import/render. No advisor-facing surface now renders health or build version. The `api.health`
client method stays for a future admin-only system-status view (nothing else consumed the widget).

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
