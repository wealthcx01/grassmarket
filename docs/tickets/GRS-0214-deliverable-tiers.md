# GRS-0214 — What the client gets free, and what they get when they engage

**Status:** Planned (2026-07-26, staging review item 13). **Priority:** MED-HIGH.
**Loop:** founder-feedback remediation, Wave 3. **Depends on:** GRS-0211.

## Why

The founder wants the commercial shape of the assessment made explicit: what is free from an
assessment, what is charged for once a client engages, and the ability for the wizard to build
more downstream reports off the same work.

Today there is one deliverable and no tiering. An advisor cannot lead with something valuable and
free, and there is nothing structurally different about the paid artefact except that it exists.
The assessment work is the same either way, so the tiering has to be about what we choose to
release, and that choice has to be a declared rule rather than an advisor's judgement in the
moment.

## Scope

1. **Two tiers, defined as data.** A `DeliverableTier` on the deliverable, with the section
   manifest for each tier declared in config rather than coded into the renderer:
   - **Teaser (free):** the headline reading, the maturity radar, the one thing holding them back,
     and what engaging would tell them. Enough to be genuinely useful and obviously incomplete.
   - **Full (engaged):** everything in GRS-0211, including the levers priced, the ranked plan, the
     scenarios, and the technical appendix.
   A section belongs to a tier by declaration. There is no "mostly free" fallback and no silent
   downgrade: a section with no tier declared is a load-time error (non-negotiable #3).
2. **Downstream reports from the same assessment.** The wizard can generate further artefacts off
   a finalised run without re-running it: a board summary, a single-module deep dive, a
   before-and-after when a follow-up assessment exists. Each is a declared template drawing on the
   same immutable run, so nothing is re-scored (#6).
3. **The tier is visible to the advisor**, on the deliverable list and on the artefact itself, so
   nobody sends a full report to a prospect who has not engaged.
4. **Earnings linkage.** A full-tier deliverable is what a consulting engagement bills against.
   Connects to the consulting commission lines GRS-0187 added. No new commercial rules are
   invented here; the rates stay config.

## Test plan

1. Manifest tests: every section maps to a tier; an undeclared section fails at load.
2. Rendering tests: a teaser artefact contains no full-tier section, asserted against the rendered
   content rather than the intent.
3. Downstream-report test: generating a board summary from a finalised run produces no new scoring
   run and leaves the existing run untouched.
4. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest. Golden master byte-identical.

## Out of scope

- Pricing. What we charge is a founder decision and stays in config.
- Payment or invoicing flows.
- The report's prose and design, which are GRS-0211.

## Acceptance

The founder can point at a teaser and a full report side by side and say which sections are which,
and the rule that separates them is written down rather than remembered.
