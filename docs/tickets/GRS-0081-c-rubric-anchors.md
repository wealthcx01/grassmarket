# GRS-0081 — C rubric anchors

**Status:** Shipped
**Loop:** Loop 7 — C-index (Customer Proposition)
**Depends on:** GRS-0080 (C registry + widgets), ADR-0023, ATLAS-Methodology-v1.3
**Branch:** `grs-0081-c-rubric-anchors`

## Why

A registry key with no rubric anchor cannot be scored consistently across raters. The engine ships
204 anchors in `rubric_anchors.yaml` (Methodology §4 template) and the loader is fail-loud (ADR-0001):
a subcomponent with no anchor set at all four maturity levels refuses to load. The 39 C subcomponents
added in GRS-0080 need the same coverage before the loader's completeness check can extend to C and
before the wizard (GRS-0083) can present §4 guidance for them.

## What shipped

**Loader (`packages/bcap_contracts/…/rubric.py`)** — one library, two sources:
- `validate_against` now requires a full anchor set for `all_subcomponent_keys() |
  all_c_subcomponent_keys()` — B/P/L **and** C. A missing C anchor is a load-time refusal
  (`MissingAnchorError`), same as B/P/L.
- `load_rubric_library` loads both `rubric_anchors.yaml` (B/P/L) and `rubric_anchors_c.yaml` (C),
  expanding `anchors` / `todo_all_levels` / `todo` from each. The library is now 204 B/P/L + 156 C
  = **360** anchors.
- The guidance router (`/guidance/subcomponents/{key}`) serves C anchors with no change — it already
  keys off `for_subcomponent`.

**Content (`registry_data/rubric_anchors_c.yaml`)** — a full §4 anchor set for every C subcomponent:
39 subcomponents × 4 levels = **156** anchors, each a behavioural statement on the standard
Basic → Developing → Advanced → Frontier maturity ladder specialised to the subcomponent theme, plus
generic required-evidence and a differentiator question.

> Authored as **DRAFT** (`AnchorStatus.DRAFT` — statement required, not the full ratified §4
> template), file `status: draft-pending-ratification`. The statements are drafted from the
> subcomponent themes via the maturity ladder and **must be ratified against the founder's seven
> completed Brokerage-App-Review checklists** (Saxo, IBKR, Lightyear, Revolut, Trading212, WeBull,
> Hargreaves Lansdown — OneDrive, reference-only, never committed) — the same honest domain-authoring
> posture as the GRS-0080 widget taxonomy. No B/P/L anchor is touched; those stay AUTHORED.

## Acceptance / verification

`tests/test_c_rubric_anchors.py` — every C subcomponent has all four levels; 156 C anchors, all DRAFT
with a non-empty statement; the 204 B/P/L anchors are unchanged (still AUTHORED,
`authored_count == 204`); dropping the C anchors makes `validate_against` refuse (C coverage is now
required). `tests/test_rubric.py` scoped its 204 count to the B/P/L keyspace. Golden master
byte-identical (no engine change). Schema parity green.

## Not in scope

- Registry/widget definitions — GRS-0080 (prerequisite).
- Engine `_score_c` and coefficients — GRS-0082.
- Wizard widget grid + C guidance UI — GRS-0083.
- Benchmark ingestion of the scored reviews — GRS-0084.
- C deliverable sections — GRS-0085. C into V — GRS-0086 (gated).
