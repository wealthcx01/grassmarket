# GRS-0232 — The appendix must not contradict the run

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-31, first-time-user review G4). **Priority:** MED. **Type:** Bug._
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

---

## Status reconciliation — 2026-08-01

**DONE.** All three scopes — and the ticket's diagnosis of the cause was wrong, which changed the fix.

## The ticket's mechanism is not the real one

The ticket says: *"The declared-figure gate checks numeric tokens in the body sections and exempts
the appendix."* **It does not.** `_every_number_in_prose_is_declared` has no section test at all —
the appendix is checked like every other section. The appendix exemption a few lines above it is for
**rule 2** (P10/P50/P90 belong in the appendix), not rule 3.

So how did "Methodology v1.2" ship above a table reading 1.1? Because **the declared-figure rule is a
presence check, not a correctness check.** It asks "is this number somewhere among the run's declared
values", never "is this the right value for the thing it claims to be". A version claim of `1.2`
passes if any declared figure renders as `1.2` — or merely *contains* it, since the check also
matches substrings. `Methodology v55` would pass wherever 55 is a module score.

That is a larger hole than the ticket describes and it is not confined to the appendix, which is why
the fix is not confined there either.

## What shipped

**1 — Version claims are checked in every section.** A new `ClientReport` validator reads any
methodology / coefficient / engine / uncertainty version asserted in prose and compares it with the
run's own. On `ClientReport` rather than `ReportSection`, because a section does not know the run's
versions — only the assembled report does. That also means no rendition can opt out: the PDF and the
web page are both built from a validated `ClientReport`.

The regex anchors on the **name** ("methodology…v1.2"), never on anything version-shaped, so it
cannot fire on an ordinary number. A false refusal here would teach an advisor to distrust the gate,
which costs more than the check is worth. Tested: "9 modules across 51 subcomponents" and "the 7
Powers framework" pass untouched.

**2 — The numeric rule, decided.** Neither of the ticket's options, because both rest on the premise
that the appendix is exempt. It is not: appendix numbers must already be declared figures, which is
option (a) and it is already in force. What was missing is that *declared* does not mean *correct*.
So the rule is now: **numbers must be declared (unchanged) AND a claim about a named version must
match that version.** The test that proves the distinction declares `9.9` as a figure and still
refuses `Methodology v9.9` — presence satisfied, correctness not.

Versions the report does not carry are left alone. Refusing prose about something the rule has no
truth for would be a gate inventing an opinion.

**3 — Coverage is documented where prose is written.** The editor's appendix caption now states what
is checked, so the rule is met by reading rather than discovered by refusal.

Golden master untouched; nothing here goes near scoring.
