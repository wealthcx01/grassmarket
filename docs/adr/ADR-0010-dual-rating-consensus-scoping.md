# ADR-0010 — Dual-rating consensus: widened scoping and the lead-resolves authority model

- **Status:** Accepted
- **Loop:** 5 (GRS-0020)
- **Normative source:** ATLAS Methodology §9 ("minimum two raters per module; consensus
  characterisation with documented dissent. Solo ratings are drafts, never deliverables"); PRD §3.4.
- **Amends:** the absolute-scoping rule (CLAUDE.md non-negotiable #9), narrowly and explicitly.

## Context

Methodology §9 requires that every module in a deliverable-bearing assessment is rated by **two
independent assessors**, working **blind of each other** until both submit, after which their
differences are **resolved into a consensus with a documented dissent** where one position yields.
A solo-rated assessment is a draft and must never finalise.

Two structural tensions with the existing design:

1. **Scoping.** Until now every owned resource obeyed one rule: *the owner sees it, an admin sees
   it, nobody else* (`_assert_can_access`). But a second rater is, by construction, **not** the
   assessment's owner. A strict owner-only rule makes dual rating impossible — the co-rater cannot
   even open the assessment to rate it.

2. **Authority.** Who records the consensus? Modelling real-time multi-party agreement (both raters
   must click "agree") is heavy and still needs a tie-breaker. The methodology already names one —
   the assessment lead.

## Decision

### 1. Scoping widens for the rating surface only (never for document editing or finalisation)

A consultant may reach the **rating workflow** of an assessment if they are the **lead (owner)**, an
**assigned rater** (they hold a `module_rating_drafts` row on it), or an **admin**. This is enforced
in one new guard, `Repository._require_rating_access`, alongside — not replacing — the owner-only
`_assert_can_access`. The widening is surgical:

- **Widened (rating surface):** read/write one's own blind draft, submit it, list a module's drafts
  (blind-filtered), and — for the lead — assign raters and resolve consensus.
- **Unchanged (owner-only):** `GET/PUT /assessments/{id}` (the document), `/live-score`,
  `/scenarios`, and `/finalise`. A rater never edits the document, sees the live score, or finalises;
  those stay the lead's, exactly as before. The existing cross-consultant scoping tests are
  untouched and still pass.

A boundary refusal is still a **404** (the API never reveals an assessment the caller may not
reach).

### 2. The blind is absolute — even for the lead and admin

`list_module_drafts` returns a caller's **own** draft always, but a **co-rater's** draft only once
**every** assigned rater on that module has submitted. This holds uniformly — the lead cannot peek
before both submit, and neither can an admin. Peeking would defeat the *method* (an independent
second opinion), not merely leak data, so the blind is not an access-control rule an admin bypass
should override. It is the one place admin does **not** see all.

### 3. The lead resolves consensus; the record is computed, not asserted

The lead records the agreed rating per assessed subcomponent. The governance fields are **derived by
the repository from the submitted drafts, never taken from the request**:

- `rater_ids` = the consultants who actually assessed that subcomponent (≥2 enforced, so a
  subcomponent only one rater scored cannot masquerade as dual-rated);
- `consensus` = `True` iff the raters gave the **same** level;
- a subcomponent the raters **disagreed** on must carry a **dissent note** (mandatory, else refused).

The resolved ratings are written into the assessment document. This choice means **no separate
consensus table**: dissent rides the existing `SubcomponentRating.{rater_ids,consensus,dissent_note}`
fields already on the document, which already flow into the immutable scoring run's `inputs_json`
and are sealed by its content hash — so dissent is captured and tamper-evident for the methods
appendix for free (the map of that path is why `SubcomponentRating` carried these fields since
Loop 0).

**Governance fields are write-restricted to the consensus workflow.** Because the finalise gate
reads `rater_ids`/`consensus`/`dissent_note` off the document, those fields would be forgeable if a
raw `PUT /assessments/{id}` (autosave) could carry them — a lead could store a document with
`consensus=True, rater_ids=[…]` and finalise with no real second rater, making §9 advisory. So
`update_assessment` **strips** those three fields back to their unrated defaults on every autosave;
only `resolve_module_consensus` (which computes them from real submitted drafts) writes them, and it
does so by writing `document_json` directly. Consequence: editing a subcomponent via autosave after
consensus clears that consensus, which is correct — changing the rating invalidates the agreement,
and finalisation then blocks until it is re-resolved.

### 4. Finalisation gate

`consensus_blockers(document)` refuses finalisation while any **assessed** subcomponent lacks a
resolved consensus (≥2 `rater_ids` and either `consensus=True` or a `dissent_note`). It runs in the
finalise endpoint right after the scoreability gate; both are 409s. Not Assessed / Not Applicable
subcomponents are exempt (they carry no rating).

## Consequences

- Dual rating is enforced **structurally**, not by convention: a solo-rated assessment physically
  cannot finalise, and the consensus record cannot be faked past the "two raters actually assessed
  it" check.
- Every path that produces a *finalised* assessment (engagements, deliverables, narratives) now
  routes through the consensus workflow; the shared test helpers seed the mandatory second rater so
  this is exercised end-to-end.
- **Accepted limitation:** the lead can still clobber a resolved consensus by re-`PUT`ting the raw
  document. That is caught at the finalisation gate (which re-checks the document), not prevented at
  write time — the gate, not the write, is the enforcement point. A future ticket may lock module
  subcomponents once consensus is resolved.
- Peer-to-peer consensus (both raters must actively agree) and rater assignment beyond the lead are
  deliberately out of scope; the lead-resolves model is sufficient for §9 and revisitable.
