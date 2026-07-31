# GRS-0232 — The appendix must not contradict the run

**Status:** Planned (2026-07-31, first-time-user review G4). **Priority:** MED. **Type:** Bug.
**Loop:** client-report hardening. **Extends GRS-0211.**

## Why

Verified on staging 31/07/2026: appendix prose stating "Methodology v1.2" shipped into the WeBull
PDF and the shared web page a centimetre above the run's own declared table reading
"Methodology version 1.1". The declared-figure gate (GRS-0211 scope 4) checks numeric tokens in the
body sections and exempts the appendix — reasonable for P10/P50/P90 prose, but it means the one
section holding the audit trail is the one section where a wrong number survives into a client
artefact. "Every number traceable" currently means "every number outside the appendix", and a
version claim is exactly the kind of number a technical reviewer checks first.

## Scope

1. **Version strings are checked everywhere.** A methodology, coefficient or engine version stated
   in *any* section's prose — appendix included — must match the run's recorded value, or the
   report refuses with the section named (through the GRS-0230 error surface).
2. **Decide the appendix's numeric rule, and state it.** Options: (a) appendix numbers must also be
   declared figures, with P10/P50/P90 percentile *labels* whitelisted; or (b) the appendix stays
   free-text but every number matching a run field's value-shape is cross-checked. Pick one in the
   PR with the reason; what is forbidden is today's unchecked pass-through.
3. **The gate's coverage is documented where prose is written.** The editor's appendix caption says
   what is checked, so the rule is not discovered by refusal (same principle as GRS-0230 scope 3).

## Test plan

1. Backend: appendix prose claiming a wrong methodology version refuses; the correct version passes.
2. Backend: whichever numeric rule scope 2 picks, one passing and one refusing fixture, asserted on
   the model (renditions must not be able to opt out — GRS-0211's own construction rule).
3. Golden master byte-identical; scoring untouched.
4. Standing gate: pytest, pyright, ruff.

## Out of scope

- Where and how refusals render (GRS-0230).
- The provenance footer's coefficient wording (GRS-0234).

## Acceptance

The founder cannot ship a report whose appendix disagrees with the run's own version table, however
the prose is worded.
