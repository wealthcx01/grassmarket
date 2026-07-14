# ADR-0019 — Path B extraction: gated proposal, identical scoring, evidence-grade cap

- **Status:** Accepted
- **Loop:** 6 (GRS-0030)
- **Normative source:** PRD §3.3 — verbatim: "confirmed Path B data produces identical scores to
  manual entry of the same data." CLAUDE.md #8 (AI proposes, humans approve), #6 (immutable runs).
- **Builds on:** GRS-0029 (the encrypted transcript this reads), GRS-0009/0010 (the Path A
  document → finalise → scoring-run path this converges on), ADR-0009 (the gated-AI pattern).

## Context

Path B lets AI map a meeting transcript onto the assessment schema. Two guarantees are load-bearing:
nothing AI proposes may be scored until a human confirms it (#8), and confirmed Path B data must
score **identically** to the same data typed into the wizard (the PRD acceptance criterion). A third
concern: an extractor must not be able to inflate evidence strength from a transcript alone.

## Decision

### 1. Extraction is a gated proposal — the proposed document lives off the assessment

`propose_extraction` runs a swappable `Extractor` port over the (decrypted, owner's) transcript and
stores the proposed `AssessmentDocument` **on the extraction record, NOT on the assessment**. The
assessment's own document is untouched until `confirm_extraction`. So an unconfirmed extraction can
**never reach the engine** — a scoring run over the assessment sees only confirmed data (tested:
a proposed-but-unconfirmed extraction leaves the assessment document empty). Extraction is AI, so
the port has a deterministic offline default (`EmptyExtractor` — proposes nothing, honest about
needing the real model) and the Claude extractor wires in at the composition root; CI makes no call.

### 2. Identical scoring is STRUCTURAL, not a re-implementation

Confirmation applies the (optionally corrected) document through the **same `update_assessment` Path
A save path** the wizard uses. From there, finalisation, `_complete_inputs`, and
`content_hash_for` are shared, single code. So a confirmed Path B document that equals the manual
Path A document produces a **byte-identical scoring run** — the run's identity IS its content hash,
computed from the same inputs. There is no separate "Path B scoring" to drift. THE test asserts
exactly this: the same data via manual entry and via confirmed extraction yields the identical
`content_hash`. Confirmed Path B data is indistinguishable from manual entry downstream.

### 3. Extracted evidence grades are capped — no artifact, no high grade

Extraction defaults extracted subcomponents to E1 and **caps them: an E3/E4 grade with no
`evidence_refs` is knocked down to E1** (`_cap_extraction_evidence`). AI cannot manufacture a high
evidence-strength grade from a transcript alone — an artifact link is required (Methodology §3.3). A
**power** carries no evidence-ref field at all, so an extracted power `benefit_grade`/`barrier_grade`
can never be artifact-backed — any E3/E4 there is knocked to E1 **unconditionally** (these grades
drive the Monte Carlo uncertainty band, so an unsupported one would fake a confident range). A
correction is capped the same way. Per-field provenance (transcript id, character span, confidence,
accepted) is persisted for every extracted field and marked accepted on confirmation — the audit
trail the ticket requires.

## Consequences

- The #8 gate is structural: unconfirmed AI output is physically not on the assessment, so it cannot
  be scored, downloaded, or finalised.
- The identical-scores guarantee cannot regress without breaking the shared Path A path — there is no
  parallel scoring code to keep in sync.
- **Accepted scope boundaries:** the real Claude extractor and the review UI (wizard pre-populated
  with confidence-marked extractions, per-field accept/correct/reject, the E-grade-needs-a-link UI
  rule) are composition-root / frontend work behind the port and provenance defined here. The
  `field_ref` is a free-form string identifying the schema field; a stricter typed reference can
  replace it without touching the gate or the identical-scores guarantee.
