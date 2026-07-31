# GRS-0199 — Bench honesty + Opportunity Radar wiring

**Status:** OPEN (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-23, founder feedback item 25). **Priority:** MED._
**Loop:** founder-feedback remediation, Wave 4 (honesty) → Wave 5 (wiring). Depends on GRS-0188
(queue re-prioritisation) and GRS-0193 (contact data).

## Why

The founder asked how live and real the Bench is. Honest answer, verified in source: the
Opportunity Radar is a naming layer over the advisor's own early-stage pipeline — no contact
database, no RSS, no external signal anywhere. Several queue items are inert text (only Academy
items link). The founder decided against importing an LMS-style system; the Bench stays ours and
gets honest, then real.

## Scope — Wave 4 (honesty now)

1. **Re-copy the radar to what it is.** `src/grassmarket/workbench/bench.py` `_research_spec`
   (~86–99): the title becomes "Research your prospect: {company_name}" and the detail states it is
   the advisor's own early-stage pipeline needing deeper sourcing — it must claim no external
   signal, no news, no contact database (that arrives in Wave 5). The empty-state copy drops
   "scan for new sourcing opportunities" (which implied a feed that does not exist) in favour of
   "No early-stage prospects to research right now."
2. **Remove governance queue items (per GRS-0188).** `assemble_queue` (~102–198) drops the
   `pending_rating_count` / `pending_rating_subject` / `pending_rating_ref` and
   `committee_review_count` / `committee_ref` parameters and their two spec blocks; `routers/bench.py`
   stops computing those counts. `BenchItemKind.RATING_REQUEST` and `.COMMITTEE` remain in the
   contract (dormant, as GRS-0188 leaves them). This ticket assumes GRS-0188 has merged.
3. **Every queue item becomes a working link.** `frontend/components/workbench/BenchDashboard.tsx`
   `KIND_HREF` (~16) is replaced by a `hrefFor(item)` helper that uses `item.kind` **and**
   `item.ref_id`:
   - `research` → `/prospects/{ref_id}` (the prospect record).
   - `arena` → `/workbench?tab=arena` (opens the arena; the scenario is the next-to-attempt one).
   - `drill` → `/workbench?tab=learning`.
   - `certification` → `/workbench?tab=certification`.
   - `academy` → `/workbench/academy` (unchanged).
   To support the query-param deep-links, `frontend/components/workbench/WorkbenchClient.tsx` reads
   `?tab=` (via `useSearchParams`) to set the initial tab. Every rendered item now shows a link
   (the generic "Open the Academy →" is replaced by a kind-appropriate label), so no queue row is
   inert text.
4. **Queue re-prioritisation.** `assemble_queue` order becomes: founder-review (the item GRS-0188
   introduces, produced only for the founder account) → certification next-step → Academy → due
   drills → arena → research. The founder-review block is appended first only when the caller is the
   founder (the flag threaded exactly as GRS-0188 threads `is_founder`); for every other advisor the
   order starts at certification. The golden master for `assemble_queue` priority order is updated
   in the same PR (the two governance items are gone; the order is the new product decision).

## Scope — Wave 5 (wiring, after GRS-0193)

5. **Radar reads the imported target universe.** Once GRS-0193's target registry exists, a new
   research spec draws from it: banks and exchange suppliers in the imported universe that do **not**
   match any of the advisor's own prospects surface as sourcing suggestions. New `BenchItemKind`
   stays `RESEARCH`; the item's `detail` cites provenance — "from the exchange supplier list,
   imported 2026-07" — and `ref_id` points at the registry entry, linking to its record. Repository
   reads the registry (GRS-0193) filtered to entries not present in `_own_prospects`; still
   self-scoped (the suggestion is for this advisor to source). No external fetch happens here — the
   universe is already imported data.
6. **RSS / news signals** on identified targets are a **later** increment, scoped separately once
   the registry proves useful (this ticket does not add any live feed).

## Test plan

Backend (pytest, offline):
- `tests/test_bench_scoring.py`:
  - The queue never contains `RATING_REQUEST` or `COMMITTEE` items (the params are gone).
  - Priority order is founder-review (founder only) → certification → academy → drills → arena →
    research; the golden master is updated and green.
  - A non-founder advisor's queue starts at certification (no founder-review item).
  - `_research_spec` copy claims no external signal (assert the honest strings; the "scan for new
    sourcing opportunities" empty-state string is gone).
  - Wave 5 (behind a GRS-0193 fixture registry): a registry target not in the advisor's own
    prospects surfaces as a `RESEARCH` item whose `detail` carries the source-dataset provenance and
    whose `ref_id` is the registry entry; a target that **is** already the advisor's prospect does
    not double-surface.
  - Scoping: the radar/research items are computed from the caller's own prospects and the shared
    registry only — advisor B's prospects never appear in advisor A's queue.

Frontend (vitest, per-file):
- `bunx vitest run frontend/components/workbench/BenchDashboard.test.tsx`: every queue item renders
  an actionable link with the correct href per kind (`research`→prospect, `arena`/`drill`/
  `certification`→workbench tab, `academy`→academy); no item renders as inert text; a `research`
  item shows its provenance label when present.
- `bunx vitest run frontend/components/WorkbenchClient.test.tsx`: `?tab=arena` opens the arena tab
  on mount.

## Out of scope

- RSS / live news signals (a separate later increment).
- Any external network fetch (the Wave 5 universe is imported data from GRS-0193).
- Re-introducing peer-rating / committee queue items (retired dormant by GRS-0188).
- The founder-review item's own production logic (owned by GRS-0188; this ticket only orders it).
- One ticket = one branch = one PR (Wave 4 and Wave 5 may land as two PRs on the same ticket, gated
  by the GRS-0193 dependency).

## Acceptance

Every Bench queue item is actionable with one click (a kind-appropriate link, verified per kind);
the radar's copy claims nothing it does not do (no external-signal language until the registry
exists); the queue contains no governance items and follows the new priority order (golden master
updated); once GRS-0193 lands, radar suggestions drawn from the imported universe cite their source
dataset and never double-surface an advisor's existing prospects.

---

## Status reconciliation — 2026-08-01

**OPEN.** No implementing commit on main; genuinely unbuilt.
