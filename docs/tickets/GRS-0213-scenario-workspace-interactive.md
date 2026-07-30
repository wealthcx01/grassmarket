# GRS-0213 — Scenarios an advisor can actually drive, with a narrative assistant

**Status:** Planned (2026-07-26, staging review item 12). **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 1. **Extends GRS-0184, which is unstarted.**

## Why

The founder asked us to be incredibly critical of the scenario tool. Being critical of it is easy.
It is a set of unlabelled rows where you change one subcomponent, the result disappears when you
navigate away, and nothing tells you whether the change you made is plausible or worth doing.

They asked for two things: make it far more interactive, and consider a small LLM-backed chat box
so an advisor can draft a narrative against the real scored data, with that narrative flowing into
the client deliverable.

That second part is the interesting one. The scenario screen is where an advisor works out what to
recommend. Right now the thinking happens there and the writing happens somewhere else, from
memory. Connecting them is the point.

## Scope

GRS-0184's persistence work is the foundation and is folded into this ticket: named scenarios,
saved to the repository, comparable over time. On top of that:

1. **Direct manipulation.** Drag a subcomponent and watch V move. Multiple changes per scenario.
   Live P50 with the range around it. The bottleneck module highlighted as it shifts. All of it
   through the existing deterministic `evaluate_assessment_scenarios` path. Scoring does not
   change; only the surface around it does.
2. **Effort against value.** Each lever shows its cost from the value bridge beside its score
   impact, so "cheapest thing that moves the needle" is visible rather than inferred. Score-points
   and currency stay in separate columns and are never combined into one figure (non-negotiable
   #7).
3. **Comparison.** Two or three saved scenarios side by side, with the deltas called out.
4. **A slot for the narrative assistant**, built in **GRS-0222**. This ticket defines where a
   drafted narrative attaches (to a named scenario) and how it flows onward into the report content
   model, and stops there. The assistant itself, its grounding contract and its ADR are separate
   because that is the risky half and it deserves its own review.
5. **Explain the screen.** The founder said they understand what scenarios are for but not what to
   do with the screen. It opens with the three levers the engine already ranks highest and a
   sentence saying why those three.

## Test plan

1. Repository tests: scenarios are owner-scoped, persist, and are editable while the run stays
   immutable (#6).
2. Determinism test: the same scenario evaluated twice gives identical results, and matches the
   existing evaluation path exactly.
3. Attachment test: a drafted narrative belongs to exactly one named scenario and travels with it.
4. Vitest per file for the workspace and the comparison view.
5. Golden master byte-identical.
6. Standing gate: pytest, pyright, tsc, ESLint.

## Out of scope

- Changing the scoring or the value bridge.
- The narrative assistant itself (GRS-0222).
- The report content model and its renditions (GRS-0211, GRS-0219, GRS-0220).
- A general-purpose chat assistant anywhere else in the product.

## Acceptance

The founder opens a finalised assessment, tries three what-ifs without reading instructions, saves
two of them, compares them, and gets a draft recommendation paragraph they would be willing to
edit rather than rewrite.
