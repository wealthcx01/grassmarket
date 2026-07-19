# GRS-0143 — Routing & not-found resilience (no dead ends from a guessed URL)

**Status:** In progress
**Loop:** Part 2 — mock-advisor stress test / trust hardening

## Why

The mock-advisor cold stress test found the single highest-consensus friction (4 of 5 personas): a
cold user reaches for plausible top-level URLs that hard-404. `/academy` actually lives at
`/workbench/academy`; deliverables are opened from an engagement, so `/deliverables` 404s; and a bad
or malformed record id (e.g. `/prospects/<junk>`) leaked a raw "Request failed (422)". There was no
global not-found page, so any miss dropped the user on a bare Next.js 404 with no way back.

## What changed (frontend-only, no contract/backend change)

- **Redirects** (`next.config.mjs`): `/academy[/:slug]` → `/workbench/academy[/:slug]`, `/courses` →
  `/workbench/courses`, `/deliverables` → `/engagements` (its real home). Guessed URLs now resolve.
- **Global not-found page** (`app/not-found.tsx`): a friendly 404 rendered inside the app shell, with
  labelled links to Dashboard / Pipeline / Portfolio / Engagements / Workbench — always a way back.
- **Bad-id handling**: the prospect- and assessment-detail pages already bounced a `404` to their
  list; they now treat a `422` (malformed id in the URL) the same way instead of surfacing the raw
  status code.

## Acceptance
- `/academy`, `/deliverables`, `/courses` resolve to a real page instead of 404.
- An unknown route or a malformed record id lands on a friendly page with navigation, never a raw
  error string. Typecheck, prod build, and all frontend tests pass. No scoring code touched.
