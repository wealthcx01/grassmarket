# GRS-0282 — Run the test suite on all four cores

**Status:** OPEN (filed 2026-10-08). **Priority:** LOW. **Type:** Developer speed.
**After:** GRS-0281 — do not start this until GRS-0281 is done and measured.

## Why

The backend test suite runs on one CPU core. The planning box and GitHub's CI runners both have
four, so three sit idle for the whole run. GRS-0281 makes the suite itself cheaper (about 17
minutes down to a target of under 8). Running it on all four cores could cut what is left to
roughly a quarter, which matters because every factory run and every CI run waits for it.

## Scope

1. Add `pytest-xdist` to the `dev` extras in `pyproject.toml`, and lock it.
2. Prove the suite is safe to run in parallel: run `uv run pytest -q -n auto` repeatedly (at
   least five times) and check every run passes with the same number of tests as one-core
   `uv run pytest -q`. Each test already gets its own in-memory SQLite database (the `engine`
   fixture in `tests/conftest.py`), which is the main thing that makes this likely to work.
   Look for anything shared that would break it: files written to fixed paths, module-level
   caches, environment variables changed by tests, fixed ports, and session-scoped fixtures
   (GRS-0281 may add module-scoped ones).
3. Fix what isn't safe, in the tests only. If a test genuinely can't run in parallel, mark it
   to run on its own (for example with xdist's `--dist loadgroup` and a group mark), and say why.
4. Switch CI's pytest step and the `## Checks` line in `CLAUDE.md` to `-n auto`. Changing the
   `## Checks` section is in scope for this ticket only.

## Not in scope

- Anything GRS-0281 covers (password hashing in tests, the demo seed).
- The frontend tests and the browser tests.

## Acceptance

- `uv run pytest -q -n auto` passes five times in a row with the same test count as before.
- The full suite's time on the planning box and in CI, before and after, is recorded in "What
  shipped".
- CI and the factory's `## Checks` run the suite with `-n auto`.
