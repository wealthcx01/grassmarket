# GRS-0095 — Primer: evidence grades E1–E4, de-jargoned

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** —

## Why

The founder's reaction to the evidence grades: "E1, E2… sounds like jargon, confusing." The primer names
the grades but does not explain them, so a reader cannot tell what each grade means or what qualifies as
each. For a rigorous, evidence-based assessment the grades are load-bearing, so the primer must make them
plain: what each grade means and — crucially — the escalation from weakest to strongest evidence. This
ticket de-jargons the evidence grades in the primer.

## What to build

**Primer (`frontend/app/guide/page.tsx`)**
- Explain **what each grade (E1–E4) means** and **what qualifies as each**, in plain English.
- Make the **escalation obvious**: client-said → interview → artifact → observed (weakest to strongest),
  so a reader understands why a higher grade is stronger evidence.
- Keep the tone plain-English for senior operators — define the term the first time it appears, no bare
  codes.

## Acceptance / verification

- Each of E1–E4 has a plain-English meaning and a "what qualifies" description in the primer.
- The client-said → interview → artifact → observed escalation is shown clearly as increasing strength.
- The grades no longer read as unexplained jargon.

## Not in scope

- Capturing evidence/rationale per rating in the wizard (that is the §3 evidence-rigor work).
- Any change to how grades are computed or stored.
