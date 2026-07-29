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
4. **The narrative assistant.** A chat panel scoped to this assessment. It can read the scored
   data, the scenario the advisor is holding, and the module evidence. It drafts recommendation
   prose in the advisor's voice.
   - It reads real data only. It never invents a number, and every figure it writes must trace to
     a value in the run. A drafting call that cannot ground a number refuses rather than
     approximating (non-negotiable #3).
   - Output is labelled AI-drafted and carries the founder review gate before it can reach a
     client deliverable (ADR-0041, non-negotiable #8).
   - The drafted narrative attaches to the scenario and flows into GRS-0211's report as a
     proposed section, never as final text.
5. **Explain the screen.** The founder said they understand what scenarios are for but not what to
   do with the screen. It opens with the three levers the engine already ranks highest and a
   sentence saying why those three.

## Test plan

1. Repository tests: scenarios are owner-scoped, persist, and are editable while the run stays
   immutable (#6).
2. Determinism test: the same scenario evaluated twice gives identical results, and matches the
   existing evaluation path exactly.
3. Grounding test: the assistant refuses to emit a figure that does not appear in the run data.
   Asserted directly, with a fixture that tries to make it approximate.
4. Approval test: assistant output cannot reach a client artefact without a recorded approval.
5. Vitest per file for the workspace, the comparison view and the assistant panel.
6. Golden master byte-identical.
7. Standing gate: pytest, pyright, tsc, ESLint.

## Out of scope

- Changing the scoring or the value bridge.
- The report rendering itself (GRS-0211).
- A general-purpose chat assistant anywhere else in the product.

## Acceptance

The founder opens a finalised assessment, tries three what-ifs without reading instructions, saves
two of them, compares them, and gets a draft recommendation paragraph they would be willing to
edit rather than rewrite.
