# Marcus Bell (Robinhood / retail) — cold stress-test report (break-it focus)

## HIGH/MED findings
- **No sanity validation on scoring inputs** (HIGH) — negative -999,999 "Assets Under Administration" saved cleanly and satisfied the "enter a metric" gate. Garbage feeds the score — a fail-loud violation.
- **Bad/missing IDs leak raw "Request failed (422)"** (MED) — /prospects/<junk>, /assessments/<junk>. Should be a friendly 404 "not found".
- **Dead routes referenced by the product** (MED) — Help page copy lists "Deliverables" as a nav section; /deliverables 404s; /academy 404s (real /workbench/academy). 3/3 personas hit this.
- **Silent duplicate prospects** (MED) — two identical "Robinhood" cards, no dedupe warning.
- **Settings/Profile "coming soon"** (MED) — no change-password/prefs on a live product. (Tom also.)
- Inconsistent power label casing "BRANDING" (raw key) vs Title Case (LOW).
- "Closed" = 0% with no Won/Lost split (LOW/MED).
- Workshop scheduled "date TBD" one-click, stage doesn't advance (LOW).
- Workbench "50% pipeline conversion" with 0 completed engagements looks hardcoded (LOW).
- Segment misfit: GBP/AUA vocabulary vs USD/MAU/PFOF for a neobroker (retail).

Positives: double-submit protection, whitespace rejected, autosave, live-score gating, explainable win-prob, strong primer; clean 404 page for truly-unknown routes.

## Confidence: 68/100
Top 5: (1) no input validation; (2) raw 422 on bad IDs; (3) dead routes in copy; (4) silent dupes; (5) Settings/Profile non-functional.
