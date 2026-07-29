# GRS-0222 — The narrative assistant: drafting against real scored data

**Status:** Planned (2026-07-26, staging review item 12). **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 3. **Depends on:** GRS-0213 (scenario workspace),
GRS-0211 (report content model). **ADR:** ADR-0050.

## Why

The founder's suggestion, in their words:

> "maybe even a small LLM enabled chat box, so they can draft a narrative that access the data on
> the back end to transform the narrative, so th[at] these can be included in reports distributed
> as deliverables to clients."

This is the right instinct and it is also the most dangerous feature in the programme. An assistant
that writes client-facing prose about a client's business, from a scored assessment, is one
hallucinated number away from a document that damages us. So it gets its own ticket, its own ADR,
and a grounding rule that is enforced in code rather than in a prompt.

## The rule this ticket exists to enforce

**Every figure in generated prose must trace to a value in the scoring run.** Not "should".
Traceable, checked after generation, and refused if it does not hold. A drafting call that cannot
ground a number fails loudly rather than approximating (non-negotiable #3). This is the difference
between a useful tool and a liability.

## Scope

1. **Scope of context.** The assistant sees: the finalised run, the assessment document and its
   evidence, the scenario the advisor is holding, and the segment. It does not see other clients,
   other advisors' work, or the benchmark population.
2. **Grounded generation.** Numbers are supplied to the model as a named value set, and the output
   is post-checked: every numeric token in the draft must match a supplied value within its stated
   precision, or the draft is refused with an explanation. The check is a test-covered function,
   not a prompt instruction.
3. **Voice.** Drafts are written in the register GRS-0205 defines. The founder's complaint about
   AI-heavy copy applies here more than anywhere, because this text is aimed at a client.
4. **Labelled and gated.** Output is marked AI-drafted wherever it appears, and carries the founder
   review gate before it can reach a client artefact (ADR-0041, non-negotiable #8). The advisor
   edits it; the founder approves it; nothing generated goes out unread.
5. **Attached to the work, not floating.** A draft belongs to a scenario or a report section, so
   there is always an answer to "what was this written about".
6. **ADR-0050** records the model choice, the grounding contract, what context is passed, what is
   never passed, and the refusal behaviour.

## Test plan

1. Grounding tests: a fixture that pressures the model toward an ungrounded figure must produce a
   refusal, not a plausible number. Asserted on the checker directly as well as end to end.
2. Scope tests: the context builder cannot reach another advisor's data, asserted at the repository
   layer.
3. Approval tests: an AI draft cannot reach a client artefact without a recorded founder approval.
4. Labelling test: generated text renders with the AI-drafted mark in every surface it appears in.
5. Offline: no live model call in CI. The generator is behind a port with a recorded fixture.
6. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- The scenario workspace itself (GRS-0213).
- Report rendering (GRS-0219, GRS-0220).
- A general assistant anywhere else in the product. This one is scoped to one assessment.

## Acceptance

An advisor drafts a recommendation paragraph they would edit rather than rewrite, every number in
it is traceable to the run, and the founder approves it before it reaches a client.
