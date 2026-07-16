# GRS-0087 — Header account/session menu

**Status:** Shipped
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** —
**Branch:** `grs-0087-header-account-menu`

## What shipped

A proper account menu in the global header, and the footer session stub retired.

- **`components/AccountMenu.tsx`** (new) — an avatar-initial + email trigger to the right of the header
  nav, opening a dropdown: **Profile**, **Settings**, a link to **bruntsfield.capital ↗**, and **Log
  out**. Identity comes from the existing `lib/session` accessor (no re-fetch, no duplicated token
  logic); when signed out it renders a **Sign in** link instead. Client-side mount guard avoids a
  hydration flash; click-outside + Escape close it.
- **`app/layout.tsx`** — mounts `AccountMenu` on the far right of the sticky header (all pages).
- **`app/profile/page.tsx`** + **`app/settings/page.tsx`** (new) — minimal, honest destinations so the
  menu has no dead links. Profile confirms your identity from the session (email / role / assessor
  level); Settings is a "coming soon" placeholder. Richer editing is a later Part-2 ticket.
- **Retired the footer stub** — deleted `components/DashboardSessionFooter.tsx` (+ its test) and its
  render in `app/page.tsx`; session controls (log out / sign in) now live in ONE place, the header.

## Acceptance / verification

`components/AccountMenu.test.tsx` — signed-out shows a Sign in link; signed-in shows the identity + a
menu with Profile / Settings / bruntsfield.capital / Log out; Log out clears the session (the old
footer's behaviour). Frontend type-check · lint · vitest green.

## Why

An advisor signing in (e.g. Byoung) lands on a dashboard with no account chrome at all: no profile, no
settings, no log-out, and no way back to the public site. The only session affordance today is a bare
"Signed in · Sign out" line in a footer — below the bar a McKinsey/Bain-grade advisor expects on any
serious platform. A top-consultancy tool puts identity and session controls in the header, where they
are always reachable. This ticket adds a proper account menu to the global header and retires the
footer stub.

## What to build

**Header account menu (`frontend/app/layout.tsx` — header)**
- Add an account menu to the right of the existing nav. It shows the signed-in identity (name / email),
  and menu items: **Profile**, **Settings**, **Log out**, and a **link back to bruntsfield.capital**
  (the public site).
- Identity comes from `frontend/lib/session.ts` — REUSE the existing session accessor rather than
  re-fetching; do not duplicate token/identity logic.

**Retire the footer session stub (`frontend/components/DashboardSessionFooter.tsx`)**
- Log-out moves into the header menu. Replace the "Signed in · Sign out" footer so session controls live
  in one place (the header), not two.

## Acceptance / verification

- The header shows the signed-in advisor's identity and an account menu with Profile, Settings, Log out,
  and a link to bruntsfield.capital.
- Log out works from the menu and clears the session (same behaviour the old footer had).
- The bare "Signed in · Sign out" footer no longer appears on the dashboard.

## Not in scope

- Building out the Profile and Settings pages themselves (menu items may link to placeholders).
- Session-persistence / refresh-token work — that is the GRS-0120 sign-out fix.
