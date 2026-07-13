# ADR-0013 — Certification ladder: enforcement, evidence gating, and the audited override

- **Status:** Accepted
- **Loop:** 5 (GRS-0023)
- **Normative source:** ATLAS Methodology §9 (CMMI-appraiser certification ladder; "High-stakes
  ratings (Frontier, Wide) require a Certified Lead plus committee"); PRD §2, §6.
- **Builds on:** ADR-0011 (the committee gate this composes with at finalisation); ADR-0012 (the
  same "evidence, not a badge" discipline as calibration).

## Context

The ladder Trained → Shadow → Observed Lead → Certified Lead (`AssessorLevel`, already a JWT claim
since GRS-0020) had a name but no teeth: nothing recorded the evidence for a rung, and nothing
stopped an uncertified advisor from signing off a top-band rating. §9 requires it to be *enforced
capability*.

## Decision

### 1. The level lives on the consultant; the evidence lives in a record

`consultants.assessor_level` stays the single source of an advisor's level (it is the JWT claim and
what every check reads). A new `certification_records` row holds the **evidence** a promotion is
gated on — coursework, exam score, shadow count, observed-lead flag, and a Certified Lead's sign-off.
Promotion updates the consultant's level and appends an event; the two never drift because promotion
is the only writer of both.

### 2. Promotion is one rung at a time, on recorded evidence (the state machine)

`promotion_blockers(record, target)` refuses unless the current level is exactly the rung below
`target` **and** that rung's evidence is in: coursework + a passed exam (≥0.7) + two shadow
assessments to reach Shadow; an observed lead to reach Observed Lead; a Certified Lead's sign-off to
reach Certified Lead. You cannot skip a rung, and you cannot reach Observed Lead with one shadow.
Evidence is recorded by an admin (trainer/facilitator); a sign-off must come from an actual Certified
Lead and never from the advisor themselves.

### 3. Enforcement at finalisation, composed after the committee gate

`requires_certified_lead(result)` flags a **Frontier module** or a **Wide power** in a scored
assessment. When present, finalisation requires the assessment's **owner (the lead)** to be a
Certified Lead — read fresh from the DB, not the possibly-stale JWT. It runs right after the §8
committee gate; both are 409s. This is the runtime refusal §9 asks for, not a warning.

### 4. The override is admin-only, reason-mandatory, and audited

An admin may override the certification floor at finalisation by passing `override_reason`. Without a
reason it is refused **even for an admin** — no silent bypass (#3). An override writes an append-only
`certification_events` OVERRIDE record (who, when, why, which ratings), so every waiver is on the
audit trail. The committee and consensus gates are **not** overridable this way — only the
certification floor, which is a people-capability judgment an admin is entitled to make with
accountability.

## Consequences

- A Frontier- or Wide-bearing assessment cannot be finalised by an uncertified lead; promotions
  cannot be faked past their evidence; every waiver is recorded. All three are tested end-to-end.
- Because the standard assessment fixture carries neither a Frontier module nor a Wide power, the
  cert gate is a no-op for the existing finalise paths — it bites only where §9 says it should.
- **Accepted scope boundary:** the coursework/exam *content* is a founder-track authoring task; this
  ticket records completions and scores, not the content. A "My Performance" view aggregating the
  events (GRS-0028) reads this audit trail but is out of scope here.
- **JWT staleness note:** because level changes take effect in the DB immediately but a live JWT
  carries the old level until re-login, every enforcement check reads the level from the DB, never
  from the token — so a just-promoted (or just-overridden) advisor is judged on their true level.
