# GRS-0228 — The E2E gate assertion tested a message we deliberately stopped sending

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: Done._
**Branch:** `integration-test-0731` (landed with the client-report wave)

## The defect

`CI / E2E (Playwright)` had been red on `main` continuously since **2026-07-22** — every run, one
test: `e2e/deliverables.spec.ts:48` "client-facing generation is refused with a plain-English gate
message".

The gate itself was never broken. The refusal fires correctly, the alert renders, and the advisor is
told why. What broke was the assertion: it matched the **old raw wording**.

`d344154` (GRS-0163, demo-polish sweep, 2026-07-21) rewrote the `ClientUsabilityError` message in
`src/grassmarket/deliverables/gate.py` from:

> Refusing to generate a client-facing deliverable from coefficient set
> 'v1-draft-pending-elicitation' (client_usable=False)…

to:

> This assessment's scores are still in draft (weights pending expert elicitation), so a
> client-facing deliverable can't be produced yet. Generate the internal, watermarked draft instead.

That was the whole point of GRS-0163 item 4: stop leaking internal flag names at a human. The spec
still asserted `/client-usable|client_usable=False|Refusing/`, so it looked for jargon the product
had — correctly — stopped emitting. A **copy improvement reading as a test failure**, and nine days
of a red gate that everyone learned to scroll past.

## The fix

Test-only. No production code changed.

- `frontend/e2e/deliverables.spec.ts` — assert the shipped sentence (`still in draft`, `can't be
  produced yet`, `watermarked draft instead`) and add a **negative** assertion that the alert never
  contains `409` or `client_usable=`. The test now defends GRS-0163's intent instead of contradicting
  it.
- `frontend/components/DeliverablesPanel.test.tsx` — the unit test mocked a 409 carrying the *old*
  string, so it proved verbatim pass-through of a message the API can no longer send. Fixture
  realigned to the real message; it still asserts pass-through, not a status code.

## Verification

Reproduced locally on the CI configuration (sqlite, seeded, built frontend, `npm start`) before and
after. Full suite `npm run e2e`: **8/8 passed**. Backend `pytest`: 1431 passed.

## Note for whoever reads this next

A message asserted in two places and authored in a third will drift again. The durable fix is to
export the gate's copy as a contract constant both sides import, rather than three hand-copies of an
English sentence — see the follow-up note in `docs/BACKLOG.md`.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `64cc44c` (GRS-0228: the red E2E gate was testing copy we deliberately removed).

This ticket carried no *What shipped* record; the commits above are that record.
