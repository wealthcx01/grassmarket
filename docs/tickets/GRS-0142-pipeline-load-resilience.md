# GRS-0142 — Pipeline board load resilience (kill the stuck "Loading…")

**Status:** In progress
**Loop:** Part 2 — mock-advisor stress test / trust hardening

## Why

The mock-advisor cold stress test surfaced one product bug independent of the test infra: on a slow
or failed board fetch the pipeline board sat on **"Loading…" forever** — no error, no retry, a dead
screen. The root cause was in `app/pipeline/page.tsx`: the load handler swallowed *every* `status: 0`
`ApiError` with `if (err.status === 0) return;`. But `request()` throws `ApiError(0, …)` for **both**
an aborted fetch (unmount) *and* a genuine network failure (backend down/slow). Conflating the two
meant a real "cannot reach the server" error was discarded, leaving `board === null` and the screen
stuck on the loading placeholder with no way back.

## What changed

`app/pipeline/page.tsx` only (no contract/schema/backend change):

- **Distinguish abort from network failure.** The catch now checks `signal?.aborted` — an aborted
  reload (unmount / superseded) stays silent; anything else surfaces. A genuine network failure
  (`ApiError` status 0) now sets a friendly "Couldn't reach the server… try again" message instead of
  being swallowed.
- **Explicit loading / error / loaded states.** New `loading` and `loadError` state (kept separate
  from the existing `error`, which is for *create* failures). The board area renders one of: the
  KanbanBoard, an **error card with a Retry button**, a "Loading your pipeline…" line, or an empty
  hint.
- **Retry path.** A `retry()` callback re-runs the load with a fresh (non-aborted) request.
- The **Add-prospect** form was already independent of the board load and stays usable throughout —
  which also gives a second recovery path (creating a prospect triggers a reload).

## Acceptance

- A failed/slow board fetch shows an error + working Retry, never a permanent "Loading…".
- An aborted reload (navigating away) shows nothing (no spurious error).
- Typecheck, prod build, and all 19 frontend test files pass; golden master untouched (no scoring
  code touched).
