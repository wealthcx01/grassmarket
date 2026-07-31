# GRS-0241 — Engagements: a list you can read, a link you cannot cross-wire

**Status:** Planned (2026-07-31, first-time-user review). **Priority:** MED-HIGH.
**Loop:** first-time-user coherence. **Relates to:** GRS-0177, GRS-0198, GRS-0208.

## Why

Walked as a first-time user, 31/07/2026:

- **The duplicate demo rows the founder complained about on 23/07 are still here.** "Revolut —
  delivery", "Hargreaves Lansdown — delivery" and "WeBull — delivery" each appear twice. GRS-0177
  cleaned the portfolio; engagements got no equivalent pass and no demo/sandbox badging either, so
  the founder's original complaint reads as unfixed on this page.
- **Four naming conventions in one list:** "Meridian Securities — delivery", "LSEG Platform Power
  diagnostic", "Platform Power Assessment — Deutsche Börse", "Platform modernisation diagnostic —
  RBC Brewin Dolphin".
- **Every row reads "contracted · 0 comms".** "comms" is internal shorthand; a count of zero
  communications on every row is metadata with no information in it.
- **The engagement detail invites a data error.** "LINK A FINALISED ASSESSMENT" renders with a
  dropdown of *every other firm's* assessments even when the engagement already has its assessment
  linked — one click links Deutsche Börse's scores to the WeBull engagement. Nothing warns that the
  subjects differ.
- **The client report is unreachable from here.** Deliverable rows offer "Review AI | Download"
  (crammed into one cell) but no link to `/deliverables/<id>/report` — the flagship new surface is
  not reachable from the page that owns the deliverable.

## Scope

1. **Badge and dedupe.** Demo/sandbox badging identical to the portfolio's (shared component), and
   the staging duplicate rows cleaned by extending the ADR-0047 cleanup to engagements — run on
   staging as part of the PR, per the GRS-0177 lesson.
2. **One naming convention.** Engagement display titles become `<Client> — <engagement type>` with
   type from a small vocabulary; a migration normalises existing titles; free-text stays stored but
   display is derived.
3. **Row metadata that means something.** Status word, client, linked-assessment state
   (none/in-progress/finalised), deliverable count, last activity date. "comms" becomes
   "communications" and hides at zero.
4. **The link control stops inviting error.** When an assessment is linked, the control shows the
   link (with unlink as the explicit rare action). When unlinked, the dropdown lists only
   assessments whose subject matches the engagement's client, with a stated override path that
   *warns* on subject mismatch instead of silently accepting it.
5. **Deliverable rows link the report.** Each deliverable row gains "Client report" beside
   Review/Download (the same link the /deliverables index has), and the two existing actions get
   breathing room and clear labels.

## Test plan

1. Vitest: list renders badges, derived titles, and the metadata set; zero-comms hidden.
2. Vitest + backend: link control excludes mismatched subjects by default; override path warns;
   linking a mismatched subject without the override refuses.
3. Cleanup script test (pattern: ADR-0047 suite) for engagement dedupe; PR states it was run on
   staging.
4. Manual: engagements list before/after screenshots in the PR.
5. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- Pipeline linkage chips (GRS-0198).
- Gmail-backed communication log (GRS-0197).
- Demo tenancy restructure (GRS-0208).

## Acceptance

The founder opens Engagements and sees one clean, consistently named row per real engagement, can
reach the client report from it, and cannot link the wrong firm's scores to it without being told
exactly what they are about to do.
