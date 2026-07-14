# GRS-0035 — My Earnings frontend page

- **Loop:** 6 (frontend gap-fill)
- **Branch:** `grs-0035-my-earnings-frontend`
- **Status:** In review
- **Normative source:** PRD §7 (earnings); GRS-0028 (the earnings backend + commission config).
- **Depends on:** GRS-0028 (backend `/earnings/*` endpoints + `CommissionLine` / `EarningsSummary` contracts).

## Goal

Give the "My Earnings" dashboard tile a page to link to. GRS-0028 shipped the earnings **backend**
(commission config, self-scoped views, `/earnings/summary`, `/earnings/commissions`,
`/earnings/statement`) but no frontend, so the tile pointed at `#` and there was no way for an
advisor to see their own earnings in the app. This closes that gap.

## Scope

1. `lib/types.ts` — mirror the `CommissionLine` and `EarningsSummary` contracts (plus the
   `CommissionKind` / `SourcingAttribution` / `PaymentStatus` enums), reusing the existing `Money`,
   `Currency`, and `ConsultantTier` types.
2. `lib/api.ts` — an Earnings section: `earningsSummary`, `listCommissions` (self-service GETs), and
   `downloadEarningsStatement` (the `.docx` blob download, mirroring `downloadDeliverable`).
3. `app/earnings/page.tsx` — a client page mirroring `pipeline/page.tsx`: token-gated with a
   `/login` redirect, `Promise.all` load with `ApiError` handling, the design-token styling, the
   summary totals rendered via `<MoneyAmount>` (display-only — no arithmetic, ADR-0002), the
   commission lines in a table, an empty state, and a "Download statement" button.
4. `app/page.tsx` — point the "My Earnings" tile `href` from `#` to `/earnings`.
5. Test — `app/earnings/page.test.tsx`: summary + line render, empty state, statement download, and
   an API error surfaced verbatim (not a status code).

Viewing own earnings is self-service (only record/advance/claim are admin-only, returning 403), so
the page needs no role gate beyond the token check — the backend enforces scoping.

## Exit criteria

- The "My Earnings" tile navigates to a working `/earnings` page showing the advisor's own summary
  and commission lines, with a downloadable statement.
- Money is display-formatted only, never computed client-side.
- Frontend gate green (type-check · lint · test · build); CI green.
