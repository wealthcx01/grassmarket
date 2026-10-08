# GRS-0281 — The test suite takes 17 minutes; two causes account for about 11 of them

**Status:** OPEN (filed 2026-10-08). **Priority:** MED. **Type:** Developer speed.
**Found by:** cowgate's investigation of slow factory runs (GRS-0279's runs, 8 October 2026).

## Why

`uv run pytest -q` takes about **17 minutes** for 1,952 tests. Every factory run of a grassmarket
ticket runs it at least once, and GitHub's CI runs it on every push and pull request. GRS-0279's
ship run waited 17 minutes for it; its ticket run hit its time limit partly because of it.

It is **not** the planning box, its sandbox, or two runs at once:

- **GitHub's CI is just as slow.** The last 40 CI runs' pytest step took 11 to 20 minutes, usually
  about 19 (for example 1,169.97s and 931.99s on 2026-10-08). The box took 1,002s.
- **The sandbox makes no difference.** Inside cowgate's `archon-jail` the suite took 1,002s, the
  same as the factory's checks step (1,003s). pytest used 99–100% of one CPU core throughout, so it
  is computing, not waiting on the network.
- **Running alongside other work makes no difference.** Today's four checks runs took 1,035 to
  1,040 seconds each, whether another run was active or not. The box has 4 cores; pytest uses one.

## What takes the time

Measured on the planning box, 2026-10-08, `pytest -q --durations=80` at `8fe8d9f`:

1. **`tests/test_demo_seed.py`: about 7 minutes (42% of the total).** 7 tests take about 35 seconds
   each, and 9 more about 19 seconds each. Each builds the whole demo account from scratch, and the
   idempotency tests build it twice. A profile of one test (`test_the_story_is_idempotent`) shows
   the time is the scoring engine's **Monte Carlo** run: the seed scores 33 runs at the full
   `DEFAULT_DRAWS = 2000` (`src/grassmarket/atlas/montecarlo.py`), about 4 million random samples,
   plus the report prose backfill, which scores again.
2. **Password hashing: about 3.75 minutes.** `hash_password` uses bcrypt at its default 12 rounds:
   0.247 seconds a hash, and the same again to check one. The shared fixtures (`_seed` in
   `tests/conftest.py`, used by `alice`, `bob`, `admin`, `founder`) hash a password for every user
   they create: at least 939 hashes across 608 test functions, before parametrisation and logins.
   The same suite with bcrypt at 4 rounds (patched for the measurement only) took **776s instead of
   1,002s**. (A bcrypt hash at 4 rounds takes 0.001 seconds.)
3. **A long tail** of report, sharing and founder-gate tests at about 1–3 seconds each, mostly in
   setup (`test_report_links.py`, `test_client_report_wiring.py`, `test_report_founder_gate.py`).
   Some of that is item 2; the rest is worth a look once 1 and 2 are done.

## Scope

1. **Hash passwords cheaply in tests only.** In `tests/conftest.py`, make bcrypt use its minimum
   cost (4 rounds) for the test session, for example by patching `bcrypt.gensalt` in an autouse
   session fixture. **Production keeps 12 rounds**; add a test that `hash_password` outside the
   test patch still produces a 12-round hash (`$2b$12$`), so the speed-up can never leak into the
   app.
2. **Build the demo once per test module where a test only reads it.** Tests that read the seeded
   demo share one seed (a module-scoped fixture). Tests that need a fresh database, or that check
   re-running the seed, keep their own. If a test needs fewer Monte Carlo draws to be fast, pass
   `draws` explicitly in the seed's test path; **never change `DEFAULT_DRAWS`**, and leave every
   golden-master or determinism test on 2,000 draws.
3. **Measure again** with `--durations=30` and put the before and after numbers in "What shipped".

## Not in scope, but worth deciding

- **Running tests in parallel** (`pytest-xdist`, `-n auto`): the box and GitHub's runners have 4
  cores and pytest uses one. Each test already gets its own in-memory SQLite database (the `engine`
  fixture), so it may be safe. It would change CI and the factory's `## Checks` line, so it should
  be its own ticket, after 1 and 2.

## Acceptance

- The full suite passes, with the same number of tests, in **under 8 minutes** on the planning box
  (from about 17).
- Production password hashing is unchanged (12 rounds), proved by a test.
- No golden-master or determinism test changes its numbers.
