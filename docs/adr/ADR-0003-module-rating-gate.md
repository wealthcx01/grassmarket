# ADR-0003 — The module rating gate (operationalising Methodology §5.2)

- **Status:** Proposed (awaiting John's ratification)
- **Date:** 2026-07-04
- **Deciders:** Founder + engineering (Loop 1)
- **Normative source:** `docs/ATLAS-Methodology-v1.md` §5.2. This ADR *extends* the Methodology
  text and therefore requires a Methodology v1.1 amendment on acceptance (CLAUDE.md
  non-negotiable #2 — scoring rules live in the Methodology + ADRs, never in a script docstring).
- **Raised by:** "ATLAS Golden Master — Suggested Changes" review, items A2 and A3.

## Context

Methodology §5.2 states two *necessary* conditions on **critical** subcomponents: a module cannot
be **Advanced** if any critical subcomponent is Basic, and cannot be **Frontier** unless all
critical subcomponents are Advanced+ at evidence E3+. It does not give a full algorithm for the
band, and it says nothing about non-critical subcomponents. The GRS-0003 generator filled that
gap with an overall-bottleneck floor — but embedded in a script docstring, which violates
non-negotiable #2, and with a bug: "Basic" was unreachable (review A2).

## Decision

The module rating gate is **rule-based (never arithmetic on q_m)** and computed as:

```
band = min( critical-rule CEILING, overall-bottleneck FLOOR )
```

**Ceiling — necessary conditions on the module's critical subcomponents:**

| Condition | Ceiling |
|---|---|
| a critical subcomponent is Not Assessed (`gate_blocked`) | Developing |
| all critical Advanced+ **and** at evidence E3+ | Frontier |
| no critical is Basic (all ≥ Developing) | Advanced |
| every critical is Basic | Basic |
| otherwise (some, not all, critical Basic) | Developing |

**Floor — the bottleneck over ALL assessed subcomponents** (the headline obeys the same
bottleneck principle as q_m):

| Weakest assessed subcomponent | Floor cap |
|---|---|
| all assessed Advanced+ | Frontier |
| minimum is Developing | Advanced |
| some (not all) assessed Basic | Developing |
| all assessed Basic | Basic |

Non-score states: **Not Applicable** subcomponents are dropped (out of scope). **Not Assessed**
never contributes to a level and, on a *critical* subcomponent, blocks the ceiling at Developing.
Evidence is **fail-loud**: an assessed subcomponent that reaches the gate without an evidence
grade raises (no `E1` default — review A6).

## Consequences

- **Positive:** the headline is honest — a module with any Basic assessed part is never Frontier
  even if its criticals are strong (why Meridian's FRONTEND is Developing though both criticals
  are Advanced/E3+). "Basic" is now a reachable band (fixes A2).
- **Cost:** this is stricter than the literal §5.2 text. On acceptance it becomes Methodology
  v1.1 §5.2a.
- **Open question for ratification:** is the floor rule too strict? "Any single Basic caps the
  band at Developing" is defensible (bottleneck) but means one weak non-critical item can hold a
  broadly-Advanced module at Developing. Alternative: only *critical* Basics, or ≥2 Basics, cap
  the band. **John to decide before the golden master is frozen** — every engine test pins to it.

## Compliance

- Golden-master gate bands match this rule; regression guards in `tests/test_golden_master_gate.py`.
- (Loop 1) The GRS-0004 engine re-implements the gate and a property test asserts the gate never
  reports Frontier over a Basic part, and that "Basic" is reachable.
