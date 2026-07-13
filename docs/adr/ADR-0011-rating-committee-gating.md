# ADR-0011 — Rating Committee: high-stakes gating and committee-member scoping

- **Status:** Accepted
- **Loop:** 5 (GRS-0021)
- **Normative source:** ATLAS Methodology §8 ("any power rated Established or above, any triad
  rating above None, and any module rated Frontier requires Rating Committee approval with recorded
  rationale and dissent. Judgment disciplined by peer challenge, not formula"); PRD §3.4.
- **Builds on:** ADR-0010 (the dual-rating consensus gate this composes with); ADR-0002 (the gate is
  ordinal, never score arithmetic).

## Context

Some ratings carry more weight with a client than others: a Strategic Power that is durable
(Established+), a Platform Power triad dimension that is real at all (above None), an infrastructure
module at the top band (Frontier). The methodology refuses to let a single assessor have the last
word on these — they need **peer sign-off** with recorded rationale and dissent. This must be a
runtime guarantee, not a convention: a high-stakes rating without committee approval must not reach
a finalised run or a client pack.

## Decision

### 1. The high-stakes set is computed from the scored result, not asserted

`grassmarket.atlas.committee.required_committee_items(result)` derives the requirement purely from
the `AtlasResult`: powers whose `strength` is Established or Wide, triad dimensions whose `rating` is
not None, modules whose `gate_band` is Frontier. This is an **ordinal, rule-based** gate on the
headline words — the same discipline as the module rating gate (ADR-0002). No coefficient or score
number enters it. A `CommitteeItem` is never stored; it is recomputed each time from the current
score, so it always reflects the ratings as they actually are.

### 2. A decision is valid only for the exact rating it reviewed

A `CommitteeDecision` records `(item_type, item_key, rating, status, rationale, dissent_note,
decided_by, decided_at)` and clears the gate only while its `rating` still matches the current score.
Re-rating a high-stakes item (e.g. a triad dimension moves Emerging → Established) **re-opens** the
requirement — the prior sign-off was for a different rating. This mirrors ADR-0010's rule that
editing a rating invalidates its consensus: sign-off tracks the rating, not just the item.

### 3. Committee membership is the existing `Role.COMMITTEE_MEMBER` — no new JWT claim

The claim shape (`JWTClaims`) is the future Holy Corner SSO contract and stays byte-compatible: we
reuse the `Role.COMMITTEE_MEMBER` value that already flows through token creation, decoding, and
`Principal`, adding only a derived `Principal.is_committee` property (mirroring `is_admin`). No
schema change.

### 4. Scoping widens for the committee surface, and sign-off is peer-only

- **View the queue** (`GET /assessments/{id}/committee`): the assessment **owner** (to watch
  status), a **committee member**, or an **admin**. Enforced in one guard,
  `_require_committee_view` — the owner-only `_assert_can_access` is untouched.
- **Record a decision** (`POST …/committee/decide`): a **committee member or admin**, and **never on
  their own assessment**. A consultant cannot sign off the high-stakes ratings on work they led —
  that is the whole point of peer challenge. The self-review refusal is a 409 (a clear governance
  message), a non-committee principal at the decide surface is a 404 (the action is not theirs to
  see).

### 5. Two gates, defence-in-depth

`committee_blockers(required, decisions)` reports every required item lacking a matching APPROVED
decision. It runs:

- at **finalisation** (assessments router), right after the dual-rating consensus gate — both 409s;
  and
- at **client-pack generation/download** (deliverables), alongside the client-usable and
  AI-narrative gates — a `CommitteePendingError` → 409, only for a client-facing pack (a watermarked
  internal draft renders with the pending status shown in the appendix).

Finalisation already guarantees a finalised run has all its high-stakes items approved, so the
client-pack gate is redundant for a legitimately-finalised assessment — but it is cheap, and it
keeps the deliverable layer honest on its own terms (a stored run that somehow lacked sign-off would
still be refused a client pack).

### 6. Approved rationale is the client-facing text; every decision renders into the appendix

The committee-approved rationale for a triad dimension is rendered as the client-facing triad text in
the Platform Power Report (replacing the generic derivation note); every committee decision, with its
rationale and any dissent, renders into the Methods Appendix as §8 audit evidence.

## Consequences

- Because the triad is above None for essentially any scored assessment, **committee sign-off is a
  routine precondition of finalisation**, not a rare one. Every path that produces a finalised
  assessment now clears the committee gate; the shared test helpers and `scripts/seed_dev.py` seed a
  committee member and approve the queue so this is exercised end-to-end.
- **Accepted scope boundary:** the queue is per-assessment. A cross-assessment "all pending items"
  view for a committee member is deferred to the Workbench frontend (GRS-0027); the data and gate
  are in place for it.
- **Founder-track note (from the ticket):** the registry's `critical` subcomponent flags should be
  ratified before this ships in anger — until then the Frontier module gate protects draft criticals.
  This is a content-ratification task, not a code change.
