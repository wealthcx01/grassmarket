# GRS-0192 — Content freshness watcher

**Status:** OPEN (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-23, founder feedback item 20, final paragraph). **Priority:** MED._
**Loop:** founder-feedback remediation, Wave 4. Extends ADR-0043. Depends on GRS-0190
(references) and lands after the first GRS-0191 course PRs give it something to watch.

## Why

The founder expects "some mechanism to track their blogs and links for any changes or updates,
so we can continuously upgrade the academy". Courses authored once will silently rot as OpenBB,
Benzinga, and Brandfetch ship; staleness should be detected, not discovered.

## Scope

1. **Watchlist as authored data.** New `src/grassmarket/workbench/content/watchlists.py`:
   per-course tuples of `WatchedSource(course_slug: str, url: str, kind: SourceRefKind,
   label: str)` covering each vendor's docs root, changelog, and blog/RSS URL. Decision: the
   watchlist lives in code next to the course content (same review path, same PR discipline),
   not in the DB — the DB stores observed state only.
2. **State table.** Migration `migrations/versions/00xx_content_source_state.py`: table
   `content_source_state` — id, course_slug, url (unique together), kind, last_hash (nullable),
   last_checked_at, last_changed_at (nullable), status (`ok` | `changed` | `unreachable`),
   error (nullable text), acknowledged_hash (nullable), created_at, updated_at. All access via
   new repository methods `upsert_source_state`, `list_source_states`,
   `acknowledge_source_change` (admin-gated, fail-loud on unknown url).
3. **Checker** (new `src/grassmarket/workbench/freshness.py`): a `SourceFetcher` Protocol
   (`fetch(url) -> str`, raising `SourceFetchError` on any non-200/network failure) with a
   real httpx implementation and a fixture fake for tests — the same seam pattern as
   `GoogleOAuthClient`. `check_sources(fetcher, watchlist, repo, now)` fetches each source,
   computes `sha256` of the raw response body, and compares to `last_hash`:
   unchanged → status `ok`; different → status `changed`, `last_changed_at = now`; fetch
   failure → status `unreachable` with the error recorded. Decision: hash the raw body with no
   content extraction — simple and honest; a noisy source that flags often is acknowledged
   away in one click, whereas "smart" extraction would silently miss real changes. Unreachable
   is a first-class surfaced status, never a skip (#3).
4. **Lesson linkage.** `flag_stale_lessons(states, courses)` (pure, in freshness.py): a
   `changed` source flags every lesson — in the course's draft AND latest published version —
   whose `references` contain a URL for which the watched URL is an exact match or a prefix
   (so `docs.openbb.co` flags every lesson citing a page under it). Output:
   `StaleLesson(course_slug, lesson_id, lesson_title, source_url, changed_at)` rows, computed
   at read time — no denormalised flag storage.
5. **Endpoints** (in `routers/workbench.py`, admin-only, 403 for non-admin):
   - `POST /workbench/freshness/run` → 200 run summary `{checked, changed, unreachable}` —
     runs the checker with the real fetcher. This is the operator trigger; Railway cron calls
     the same logic via a new script `scripts/check_content_freshness.py`. Decision: no
     in-process scheduler (no new daemon dependency); cron plus on-demand covers the need.
   - `GET /workbench/freshness` → 200 `{sources: [...states], stale_lessons: [...]}`.
   - `POST /workbench/freshness/acknowledge` body `{url}` → 200; sets
     `acknowledged_hash = last_hash`, which clears the lessons flagged by that source until
     the hash changes again; unknown url → 404.
6. **Authoring UI.** New `frontend/components/workbench/FreshnessQueue.tsx` rendered on the
   admin courses page (`frontend/app/workbench/courses/page.tsx`): a "Source updates" section
   listing changed sources with their flagged lessons (each linking to the course editor at
   that lesson), an "unreachable" section rendered as errors, and an acknowledge button per
   source ("reviewed — clear until it changes again"). Learner surfaces show nothing.
7. **CI/offline:** the real fetcher is only constructed in the router/script; every test uses
   the fake. No live fetch in CI (existing rule).

## Test plan

Backend (pytest, new `tests/test_content_freshness.py`, fixture fetcher only):
- First run records hashes with status `ok`; second run with one changed fixture body flags
  exactly the lessons referencing that URL (prefix match covered), and no lesson of any other
  course.
- Unreachable fixture → status `unreachable` with the error string persisted and returned by
  GET; it is never silently omitted from the response.
- Acknowledge clears the flagged lessons; a subsequent content change at the source re-flags.
- Idempotence: two runs against identical bodies produce no `changed` state and do not move
  `last_changed_at`.
- Scoping: non-admin GET/POST on all three endpoints → 403; unknown acknowledge url → 404.
- Watchlist integrity: every watchlist url is https and every course_slug exists in the seeded
  catalog (load-time style guard, mirroring registry key validation).

Frontend (vitest):
- `frontend/components/workbench/FreshnessQueue.test.tsx`: renders changed sources with lesson
  links, renders unreachable as an error state, acknowledge posts and removes the group,
  empty state.

## Out of scope

- Automatic content updates or AI-drafted lesson revisions (review stays human).
- Watching sources that require authentication.
- Learner-facing staleness indicators.
- RSS-based prospect/news signals (that is GRS-0199's later increment).

## Acceptance

- Changing a watched fixture flags exactly the linked lessons, including prefix-matched docs
  pages (test-enforced).
- The authoring queue lists stale lessons with a working link to each and the source that
  changed; acknowledging clears them until the next change.
- An unreachable source surfaces as a visible failure in both API and UI; nothing is skipped
  silently.
- CI runs the entire suite with zero network access.

---

## Status reconciliation — 2026-08-01

**OPEN.** No implementing commit on main; genuinely unbuilt.
