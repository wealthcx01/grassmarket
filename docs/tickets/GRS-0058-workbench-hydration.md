# GRS-0058 — Fix the Workbench hydration mismatch (React #418)

- **Loop:** 5 (Workbench)
- **Status:** Fixed — found in the 2026-07-15 deep-dive functional audit.
- **Severity:** Medium — a hydration mismatch (uncaught React #418) on every Workbench load.
- **Rubric basis:** #11 (no broken/incorrect render); fit-for-purpose.

## Problem

`WorkbenchClient` read the session from `localStorage` **during render**
(`useMemo(() => getSession(), [])`). The server can't read `localStorage`, so it rendered the
"Please sign in" fallback; the client, with the token present, rendered the tabs. The first client
paint therefore diverged from the server HTML → **hydration mismatch, React error #418**, thrown on
every authenticated Workbench visit.

## Change

Defer the session read to after mount (the pattern `DashboardSessionFooter` already uses): a
`mounted` flag starts `false`, flips in `useEffect`, and the session is only read once mounted. The
server and the first client paint both render a stable "Loading…" placeholder, so they agree; the
real content renders after hydration.

## Exit criteria

- No React #418 / hydration error on `/workbench` (confirmed by the functional audit: 62 checks, 0
  issues). Role gating and all five tabs unchanged; `WorkbenchClient.test.tsx` green.
