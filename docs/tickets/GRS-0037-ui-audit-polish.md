# GRS-0037 — UI audit: dashboard auth-state, dead link, raw IDs, bare controls

- **Loop:** UI retro-audit (grs-ui-retro-audit)
- **Status:** Triage — found in the 2026-07-14 visual retro-audit; NOT yet fixed.
- **Severity:** Medium — polish/correctness defects across the dashboard and CRM detail pages.
- **Found by:** Visual audit of the CI screenshot gallery. Repro screenshots:
  `assets/ui-audit-dashboard.desktop.png`, `assets/ui-audit-engagement-detail.desktop.png`,
  `assets/ui-audit-prospect-detail.desktop.png`.

## Defects

1. **Dashboard shows "Not signed in? Go to sign in" even when authenticated.** `app/page.tsx` is a
   static server component with no session awareness, so a logged-in advisor is told they're not
   signed in. It should reflect the session (e.g. show the advisor / a sign-out, or drop the line
   when a token is present). (`assets/ui-audit-dashboard.desktop.png`.)

2. **"Deliverables" dashboard tile is a dead link (`href: "#"`).** Clicking it goes nowhere. Either
   point it at a real destination or make the tile clearly non-navigable. (Same class of gap that
   GRS-0035 fixed for the "My Earnings" tile.) (`app/page.tsx`.)

3. **Engagement detail exposes a raw assessment UUID as the link text.** Under "Linked assessments",
   the link reads `22dc0d7a-6e40-4d23-9343-359c89a18a2b` instead of the assessment's subject/name.
   Show a human label. (`assets/ui-audit-engagement-detail.desktop.png`.)

4. **Prospect detail's stage-move control is an unlabeled, empty-looking native `<select>`.** It
   sits under "Stage Contracted · entered …" with no label and appears blank/unstyled, reading as a
   broken element rather than a "move to stage" action. Give it a label/placeholder and styling
   consistent with the design tokens. (`assets/ui-audit-prospect-detail.desktop.png`;
   `components/StageMoveControl.tsx`.)

## Repro

Seed + run the app, log in as the demo advisor, and open `/`, `/engagements/{id}`, `/prospects/{id}`.

## Exit criteria (for the fix ticket, later)

- The dashboard reflects auth state correctly; no "not signed in" copy for a signed-in advisor.
- No dashboard tile is a dead `#` link.
- Linked assessments render a human-readable label, not a UUID.
- The stage-move control is labelled and styled (not a bare empty select).
