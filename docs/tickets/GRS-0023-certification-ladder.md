# GRS-0023 — Certification ladder (enforced)

- **Loop:** 5
- **Branch:** `grs-0023-certification-ladder`
- **Status:** In review — PR #25
- **Normative source:** Methodology v1.2 §9 (CMMI appraiser pattern); PRD §2, §6.
- **Depends on:** GRS-0020. Content dependency: coursework + exam content (founder track; Advisor Guide is the textbook seed).

## Goal

Trained → Shadow → Observed Lead → Certified Lead as *enforced capability*, not a badge.

## Scope

1. Certification state machine per advisor with evidence requirements: coursework completions, rubric exam, 2 shadow assessments, observed-lead sign-off by a Certified Lead.
2. Enforcement points: only certified advisors lead engagements (PRD §6); Frontier module ratings and Wide power ratings require a Certified Lead on the assessment (Methodology §9) — refusal, not warning.
3. Tier + certification level into JWT claims (Holy Corner claim shape preserved).
4. Admin override path with mandatory recorded reason (fail-loud: no silent bypass).
5. Progression events persisted append-only (Holy Corner sync later; feeds My Performance).

## Exit criteria

- An uncertified advisor attempting to finalise a Frontier-bearing assessment is refused (service + HTTP).
- State transitions require their evidence (cannot reach Observed Lead with one shadow).
- Override leaves an audit record.
- Full gate green; CI green.
