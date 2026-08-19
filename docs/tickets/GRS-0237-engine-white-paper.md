# GRS-0237 — The engine white paper: one document that answers "is this up to scratch?"

**Status:** DONE (2026-08-19). _Previously recorded as: Planned (2026-07-31, founder: "I am not sure if the engine calculator behind the._
assessment wizard is up to scratch — need a white paper on this"). **Priority:** HIGH.
**Loop:** first-time-user coherence. **Relates to:** GRS-0179, GRS-0180, GRS-0150, GRS-0223, ADR-0046.

## Why

The founder cannot currently answer a due-diligence question about the engine with one document.
The material exists but is scattered and part-stale:

- `docs/ATLAS-Methodology-Guide.md` is already ~80% of a white paper (formal model, behavioural
  properties, elicitation design, reliability programme, limitations, prior-framework comparison) —
  but it declares v1.1 normative and predates v1.4–v1.6, the founder gate (its governance section
  still describes the retired Rating Committee), the C-index, the critical-control cap and the
  one-number rule.
- `docs/ATLAS-Scoring-Explained.md` (advisor explainer) and `docs/ATLAS-7Powers-Adaptation.md`
  (Helmer packet, ADR-0046 still Proposed pending his review) serve different audiences and neither
  is framed as validation.
- The validation evidence that exists is genuinely strong — golden master (V = 0.478565, every
  intermediate pinned), ~140+ engine/coefficient tests, property tests, the dispersion analysis —
  and the gaps are equally real: **retail coefficients are uniform draft placeholders; the
  wealth/exchange "elicited" sets are engineering starter values activated by founder direction
  (ADR-0037) whose provenance records name a panel that has not run**; no systematic weight
  sensitivity beyond the θ/α variant grid; no outcome evidence; reliability machinery dormant with
  zero measurements.

A white paper that hides those gaps fails its own purpose. One that states them, with the roadmap
to close them, is what survives a sceptical reader — the same honesty doctrine the product itself
runs on (non-negotiable #3).

## Scope

1. **`docs/ATLAS-White-Paper-v1.md`**, one document, external-reader audience (a client's CTO, an
   acquirer's DD team, Helmer's office). Structure: what the engine computes (the full chain,
   subcomponents → q_m → B/P/L(/C) → V, with the actual formulas and the min()/bottleneck
   semantics); why each design choice (two tracks, fail-loud, uncertainty by evidence grade); the
   7 Powers derivation and its boundary (what is Helmer's, what is Bruntsfield's — per ADR-0046);
   worked example (the golden-master firm end to end); validation evidence with counts and file
   references; **a limitations register that names the coefficient status plainly**; the closure
   roadmap (elicitation panel, calibration data, outcome register thresholds from Guide §1.2).
2. **Re-baseline the Methodology Guide** to v1.6 as part of the same pass, or fold it into the
   white paper and retire it — decide and state which; two documents claiming different normative
   versions is worse than either choice.
3. **Correct the elicited-set provenance records** (`elicited_coefficients.py`) so they say what
   happened — founder-directed starter values, panel pending — rather than naming
   "bruntsfield-elicitation-panel-2026" with method strings for a session that has not occurred.
   A provenance record that overstates its evidence is a D-class defect in our own terms.
4. **Add the missing sensitivity exhibit:** a one-off analysis (committed under `docs/analysis/`)
   sweeping λ/δ/W_g/strength-encoding perturbations and reporting rank-stability of module ordering
   and V across the three showcase firms — the question a reviewer asks that the θ/α grid does not
   answer.
5. **Surface it.** The Guide and the report appendix link to the white paper; the wizard's
   "How the maths works" link points at the explainer which points at the white paper.

## Test plan

1. Doc-structure test (pattern: `tests/test_docs_powers_adaptation.py`): required sections present,
   version pinned to Methodology v1.6, no stale "Rating Committee" governance language.
2. Provenance-record tests updated to the corrected wording; nothing else in scoring changes —
   golden master byte-identical.
3. The sensitivity notebook/script is committed and re-runnable (`tools/` or `docs/analysis/`),
   seeded, offline.
4. Standing gate: pytest, pyright, ruff.

## Out of scope

- Running the elicitation panel (GRS-0150 owns the values).
- Changing any scoring behaviour whatsoever.
- The Helmer review itself (GRS-0201 packet; ADR-0046 ratification).

## Acceptance

The founder hands one PDF/markdown document to a sceptical technical reader and it answers what the
engine does, why, how it is tested, what is not yet proven, and when that closes — without a single
claim the repo cannot back.

---

## Status reconciliation — 2026-08-01

**DONE** — shipped 2026-08-19, all five scopes.

## What shipped

**1 — `docs/ATLAS-White-Paper-v1.md`.** One document for an external technical reader: the formal
model with the actual formulas, the behavioural properties P1–P7, the C-index and critical-control
cap as conditional-by-construction amendments, uncertainty, the value bridge, a validation-evidence
table where every row names a file, a limitations register, and a closure roadmap mapping each gap
to what closes it.

**2 — The Methodology Guide is RETIRED, not re-baselined.** Decision stated in §12 of the paper and
in the stub that replaces the Guide. It was an informative companion pinned to v1.1 that had
drifted past v1.4/v1.5/v1.6, still described the Rating Committee as operative governance, and
never mentioned C, the cap or the one-number rule. Its audience was the white paper's audience;
maintaining two documents for one reader is what produced the drift. The stub is kept rather than
deleted so existing links resolve to an explanation.

**3 — Provenance corrected, and the ticket's premise was partly wrong.** See below.

**4 — `docs/analysis/weight-sensitivity-2026-08.md` + `tools/weight_sensitivity.py`.** Seeded,
offline, re-runnable. Headline: the module ranking survives λ perturbation until **±110%**, and the
ordering of the three showcase firms by V did not change in any of 160 runs.

**5 — Surfaced** from the Advisor Guide, the scoring explainer, the in-app Guide page, the wizard
("Is it up to scratch?" beside "How the maths works"), and the PDF appendix.

## Where the ticket — and my own founder-decision write-up — were wrong

The ticket says `elicited_coefficients.py` stamps its records with a panel name, and
`FOUNDER-DECISIONS-2026-08.md` (which I wrote) said it stamps **every weight family** that way.
Measuring it first:

| Set | Active? | Record said | Verdict |
|---|---|---|---|
| retail `v1-elicited-2026` | **No** — built and client-usable, but not the active set | `bruntsfield-elicitation-panel-2026`, "elicited by the Bruntsfield weight panel" | false claim, now corrected |
| wealth / exchange starters | **Yes**, since 2026-07-20 (ADR-0037) | `engineering-starter-research-validated-2026-07`, "panel ratification scheduled" | already honest |

So the false claim sat in a **dormant** set. Still worth fixing — that is the set which activates
when the panel signs off, so the lie was queued rather than live — but less severe than both
documents claimed. The D1 section has been corrected to say so.

**No coefficient value changed.** Golden master byte-identical, 56 golden tests pass.

## Two things measured that the ticket did not anticipate

**The default profile cannot produce a client deliverable.** Retail scores on
`v1-draft-pending-elicitation` with `client_usable=False`, so the deliverable gate refuses it. Only
wealth and exchange can go to a client today. That is the fail-loud design working exactly as
specified, and it is almost certainly not what the founder expects the product to do. Recorded in
the white paper §10.1 and in D1.

**Two coefficient version strings still read `...-elicited-starter-...`.** Deliberately NOT renamed:
a coefficient version is stamped onto every immutable scoring run, and rewriting it would falsify
runs already recorded (non-negotiable #6). The provenance record beside them is the authoritative
statement, and the white paper says so.

## Two defects this ticket's own work caught in itself

1. **τ = 1.000 across all four families was three-quarters tautology.** δ, W_g and the strength
   encoding are downstream of q_m and cannot move a module score, so their rank stability is a
   property of the model's structure, not a measurement. The table now reports `n/a` for them.
   Publishing the first version would have been evidence-laundering in a document whose whole
   purpose is not doing that.
2. **The committed numbers did not reproduce.** Three consecutive runs of the same seeded sweep gave
   0.55, 0.53 and 0.47. Cause: weight families built from set comprehensions upstream + per-process
   string-hash randomisation + RNG consumed in dict order. `perturbed()` now sorts keys. The guard
   that missed it asserted `sweep() == sweep()` — true in one interpreter and therefore worthless;
   it now runs two subprocesses under different `PYTHONHASHSEED` values.

## Not done

- **Scope 3 is complete for the record, not for the values.** Whether these numbers survive is
  founder decision **D1**; nothing here invents or ratifies a value.
- The sweep does **not** cover θ, α (existing variant grid), κ, or the C-index families. Stated in
  the analysis document's closing section rather than left implied.
- ADR-0046 remains **Proposed**; the Helmer review is D7.
