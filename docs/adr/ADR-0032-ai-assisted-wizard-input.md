# ADR-0032 — AI-assisted wizard input (proposals over a deterministic port, gated by accept/edit)

- **Status:** Accepted (2026-07-18). Founder theme for the wizard: it should stop being raw data entry
  and feel like **assisted homework** — suggestions, prefill, and contextual help as the advisor works.
- **Date:** 2026-07-18
- **Deciders:** Founder theme + engineering (autonomous Part-2 build).
- **Normative source:** `docs/tickets/GRS-0101-ai-assisted-wizard.md` (the umbrella ticket).
- **Implements:** GRS-0101 (this ADR's v1). Later slices under the umbrella: GRS-0100 (entity linking),
  GRS-0102/0108/0109 (Path B / widget / video ingestion) — each its own ticket.
- **Couples with:** ADR-0009 (AI proposes / humans approve — the injectable-drafter pattern this
  mirrors); CLAUDE.md non-negotiables #2 (methodology is settled — implement, don't re-invent), #3
  (fail loud, never fabricate), #8 (AI proposes, humans approve), #9 (data scoping).

## Context

The wizard already surfaces the §4 rubric anchors inline as *guidance* (the "How to assess this
power" / "Guidance" toggles). What it does not do is **propose** anything: every value starts blank.
GRS-0101 asks for AI-assisted suggestions/prefill so the advisor gets proposed values and nudges
rather than an empty form — with the hard constraint that **no AI-proposed value counts until the
advisor explicitly accepts or edits it** (CLAUDE.md #8).

Two questions this raises:

1. **What is the approval gate for a wizard suggestion?** ADR-0009 requires a *recorded* approval for
   AI narratives because they can reach a client. Does a wizard suggestion need the same store?
2. **How does suggestion generation run offline / in CI**, given the Claude Agent SDK is not a repo
   dependency and live model calls are forbidden in tests (same constraint ADR-0009 faced)?

## Decision

**Deterministic suggestions over an injectable port, gated by an explicit in-UI accept/edit — no new
approval store, no change to the scoring engine.** Directly mirrors ADR-0009's shape.

1. **An injectable `WizardSuggester` port.** The suggestion service depends on a `WizardSuggester`
   Protocol, never on a concrete SDK. The shipped implementation is `HeuristicWizardSuggester` — a
   **deterministic, offline** suggester that derives proposals from the current `AssessmentDocument`
   + the registry. It is a real, testable proposer today and the seam a Claude Agent SDK adapter drops
   into later **without touching feature code or tests** — and any such adapter must still return
   proposals that pass through the same accept/edit gate.

2. **`SUGGESTER_VERSION` is stamped on the response** (like `DRAFTER_VERSION`/`PROMPT_TEMPLATE_VERSION`
   on narratives), so a suggestion is attributable to the suggester that produced it.

3. **The gate is accept-or-edit in the UI — not a recorded approval — and this is deliberate, not an
   omission.** A wizard suggestion produces **no client artifact by itself**: accepting it writes an
   ordinary value into the advisor's own draft document, indistinguishable from a typed value, which
   then flows through **every existing downstream gate before anything reaches a client** — dual-rating
   consensus (§9), Rating Committee sign-off (§8), and the client-usable-coefficient gate on
   deliverables (ADR-0009/§0015). So the AI's influence is already caught by the gates that exist. This
   is the same carve-out CLAUDE.md #8 already makes for practice-arena feedback (self-scoped content
   whose gate is the *label* + scoping, not an approval record). A recorded-approval store here would
   be ceremony without a client-facing risk to gate.

4. **Nothing auto-applies; every proposal is visibly AI-labelled.** Suggestions render in a distinct
   "AI suggestions" panel on the input steps, each marked as AI-proposed. A `prefill` proposal shows
   its value as a **starting point to confirm or edit**; **Accept** applies it via the same
   client-side `update(doc.…)` path a manual edit uses, **Dismiss** hides it. No suggestion mutates the
   document without that click.

5. **The methodology engine is untouched (CLAUDE.md #2), and suggestions fail loud (#3).** The
   suggester proposes *inputs*, never scores; it computes nothing the engine computes. Every proposal
   references registry-valid keys derived from the loaded registry — it can surface no fabricated
   module/power/subcomponent, and it proposes values only for **unset** fields (it never silently
   overwrites an advisor's rating). Anti-anchoring is handled by (a) explicit accept/edit and (b) the
   downstream dual-rating: a co-rater independently rates the same module, so a biased prefill cannot
   survive consensus unchallenged.

6. **Read-only for finalised records.** A finalised (locked) or non-editable assessment returns no
   suggestions — there is nothing to assist. Owner-scoped like every read (#9).

### v1 suggestion kinds (all deterministic; conservative by design)

- **`GUIDANCE` — coverage to scoreable.** Points to the next unrated core-module subcomponent (or the
  ungraded Powers) that stand between the advisor and a scoreable assessment, citing the real
  scoreability blockers. No value; the founder's "assisted homework" nudge.
- **`GUIDANCE` — consistency nudge.** Flags an internal tension for re-check — e.g. a Power rated a
  strong *benefit* with a *None* barrier (a durable advantage with nothing defending it is worth a
  second look). Points to the field; proposes no value.
- **`PREFILL` — carry-forward starting level.** When a module already has several rated subcomponents,
  proposes the module's **modal** rated level as a *starting point* for one unrated subcomponent in the
  same module. Concrete value, applied only on Accept, freely editable after. Chosen because it is a
  structural convenience (align within a module), not a novel judgment, and it is the one kind that
  exercises the accept-applies-a-value path the acceptance criterion names.

## Consequences

- The wizard gains a genuinely useful, offline, testable assist surface today, and a clean seam for an
  LLM suggester later (swap the port impl; the gate and the contract are unchanged).
- No new persistence, no scoring-path change, no new client-facing risk → golden master untouched.
- The suggester is intentionally conservative (guidance-first, one non-judgment-heavy prefill). Richer,
  judgment-bearing prefill (metric-derived power floors, entity-informed priors) is left to the LLM
  adapter + later umbrella slices, where the founder can tune what the AI is allowed to propose.

## Alternatives considered

- **A recorded approval per accepted suggestion (full ADR-0009 store).** Rejected: no client artifact
  to gate, and the downstream §9/§8/coefficient gates already catch AI influence; the store would be
  ceremony. If a future audit needs "which values were AI-suggested," add a field-provenance flag then.
- **A client-only heuristic (no backend port).** Rejected: it would not share the ADR-0009 seam, so the
  later LLM swap would be a rewrite, and the logic could not be unit-tested server-side against the
  registry.
- **Proposing full ratings across the board (aggressive prefill).** Rejected for v1 on anti-anchoring
  grounds (#2) — a deterministic engine has no basis to assert a maturity judgment; that belongs to the
  LLM adapter under founder-tuned limits.
