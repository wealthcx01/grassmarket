# GRS-0066 — Estate doc corrections + engine A1/A2 re-verification

**Status:** In review
**Loop:** Track A (estate reconciliation — no methodology decision needed)
**Branch:** `grs-0066-estate-reverify`

## Why

The July 2026 binder (`NEXT-STEPS-2026-07.md` §6) flagged two stale estate docs, and the delivery
review (`reviews/ATLAS-Delivery-Review-2026-07-15.md` §6.8) asked for re-verification of two engine
invariants before the guided-consulting build proceeds. Both are cheap correctness/hygiene items that
gate nothing but should not linger.

## Scope

**1. Engine re-verification (review §6.8).**

- **A1 — empty module must renormalise, not zero-fill.** A module with **no** assessed subcomponent
  must contribute `q_m = None` and be **excluded** from L's δ-weighted term (the old prototype defect
  zero-filled it, dragging L down). Verified clean in `atlas/engine.py`: `_score_l` builds
  `assessed_q = {k: v for … if v is not None}` and renormalises δ over the assessed set. Pinned by a
  new test — `test_empty_module_excluded_from_l_not_zero_filled` — which empties a non-critical module
  (`EMS_GATEWAY`) that would otherwise equal every other module's q_m and asserts L is **identical**
  after renormalisation (a zero-fill would lower it materially), with `q_m is None`, `coverage == 0.0`.
- **A2 — the rating gate must be able to emit "Basic".** Verified clean; already pinned by
  `test_gate_all_basic_module_is_basic` (all-Basic module → gate band "Basic") and
  `test_gate_never_frontier_with_any_basic_part`. No change needed.

No engine code changed — both invariants were already structurally correct; A1 gained the missing test.

**2. Estate doc corrections (binder §6).**

- `METHODOLOGY-V2-SCOPE.md` — corpus figures were stale ("~70-widget checklist", "7 platforms").
  Corrected to **93 widgets × 15 categories** and **16 app folders (7 scored)** via a dated correction
  banner plus the two most-cited inline figures; §1/§3 marked superseded by ADR-0023, §2 (profiles)
  still live.
- `BACKLOG.md` — was listing GRS-0016–0034 as `Planned` when they had shipped, and had no Loop 7.
  Rewritten as a shipped-ranges index + a Track A (GRS-0066–0073) in-flight table + a Track B
  (Loop 7 / exchange profile / v1.4) gated table, pointing to the binder as the sequencing narrative.

## Out of scope / explicitly not done

- No scoring behaviour changed — this is verification + docs only (CLAUDE.md non-negotiable #2:
  scoring changes are ADRs + methodology versions, never silent code edits).
- No C-index / exchange-profile work — those are Track B, gated on founder decisions D1/D2
  (`ADR-0023`) and on corpus ingestion through scoped storage (never committed to this repo).

## What shipped

- `tests/test_atlas_engine_properties.py` — `test_empty_module_excluded_from_l_not_zero_filled` (A1).
- `docs/METHODOLOGY-V2-SCOPE.md` — corpus correction banner + inline figure fixes.
- `docs/BACKLOG.md` — full index refresh.
- `docs/tickets/GRS-0066-estate-reverify.md` — this ticket.
