# tools/

Operator tooling that is not part of the application and is not imported by it. Nothing here runs
in CI; everything here is run by hand against a deployed environment.

These files were promoted out of `scratch/` when that directory was removed from the repo. They
earned it by being referenced from work that is still open — the rest of `scratch/` was 75MB of run
artefacts and screenshots whose conclusions already live in `reports/`, and which broke `ruff` on
every branch that inherited them. `scratch/` is now gitignored; use it freely and locally.

## persona-harness/

The mock-advisor stress-test rig — five personas driven through a real deployment by a headless
browser, used for the 2026-07-19, -20 and -22 runs. `PERSONA_PLAYBOOK.md` is the procedure;
`agent_drive.mjs` and `stage_drive.mjs` are the drivers; `smoke_steps.json` is a short step list to
check the rig itself works before spending a run on it.

Needs `bun` and a Chromium that Playwright can drive. Syntheses of past runs are in `reports/`.

## staging-e2e/

Two scripts that drive the live staging API over HTTP as the demo advisor: a full brokerage flow
(prospect → pipeline → sandbox assessment → deliverable) and a commission flow. They are the
starting point for **GRS-0159**, which turns this into a repeatable seed rather than a script
somebody remembers to run.

They take the environment from `GM_*` variables and talk to whatever `API` is set to. Point them at
staging. Pointing them at production would create real records.
