# GRS-0245 scope 1 — the gate matrix as it stands today

**Date:** 2026-08-01 · Measured from code and confirmed by running the paths.

The ticket asks for this table *before* anything changes, and specifically asks whether production
is already gated somewhere the analysis missed. **It is not.** The gap is real on production
records, not an artefact of the sandbox demonstration.

## The matrix

Rows are the three paths by which something reaches a client. Columns are what is actually required
today, by record provenance.

| Path | Production | Demo / sandbox | Consults founder approval? |
|---|---|---|---|
| **docx client pack** (`POST /engagements/{id}/deliverables`, `client_facing=true`) | client-usable coefficients + §7 widths + **founder approval of the assessment** | self-approves (ADR-0029) | **Yes** — `deliverables.py:163/265/327` fetch `current_founder_approval`, `service.py:134/206` assert it |
| **client report PDF** (`GET /deliverables/{id}/client-report.pdf`) | prose written; AI sections approved | same | **No** |
| **share link issue** (`POST /deliverables/{id}/links`) | prose written; AI sections approved | same | **No** |

Prose authorship does not change any row. `assert_client_ready` (`client_report.py:171`) checks that
*AI-drafted* sections carry approvals; with every section consultant-written the approved set is
empty and the check passes trivially — exactly as the ticket describes.

## Measured, not inferred

A characterisation run on a **production** record, prose written *after* the founder approved the
assessment:

```
PDF download      -> 200
Share link issue  -> 201
Public read       -> 200
```

No founder sign-off of the report content anywhere in that sequence.

## The precise mechanism of the gap

It is not that the founder gate is absent from the record. It is that the gate is bound to the
**wrong artefact**.

`current_founder_approval(assessment_id)` (`repository.py:3252`) matches an approval against
`_document_hash(row)` — `sha256(row.document_json)`, the **assessment document**. The client
report's prose lives in a different table entirely, written through
`PUT /deliverables/{id}/report-prose` *after* finalisation.

So the sequence that ships unreviewed prose to a client is:

1. Advisor builds a production assessment. The founder reviews and approves it — the hash matches.
2. Assessment finalises (the gate at `assessments.py:370` passes).
3. Advisor writes the client report prose. **This changes no hash the gate looks at.**
4. Advisor issues a share link or downloads the client PDF. **Neither path consults approval at all.**

The founder approved a scored document. What reaches the client is that document's *numbers* wrapped
in prose the founder has never seen, and which can be rewritten freely after approval without
invalidating anything.

## What this implies for the fix

The existing hash-invalidation rule is the right one and it is bound to the wrong thing. The fix is
an approval scoped to the **report content** — `(deliverable_id, prose_hash)` — so that:

- editing prose after approval invalidates it, the same rule the Founder-review tab already states;
- demo/sandbox records stay exempt and stay watermarked (GRS-0229 — the watermark is their gate);
- when GRS-0222 starts drafting sections, they flow through the same gate unchanged, because the
  gate is on the content rather than on its authorship.

That is a new approval scope on `founder_approvals` (a nullable `deliverable_id` plus a content
hash), the repository methods to read and write it, the two route gates, the refusal copy, and the
queue entries.

## Built — the matrix after the change

| Path | Production | Demo / sandbox |
|---|---|---|
| docx client pack | unchanged: founder approval of the **assessment** | self-approves |
| client report PDF | **+ founder approval of the report's PROSE** | exempt, watermarked |
| share link issue | **+ founder approval of the report's PROSE** | exempt, watermarked |

Both client-report paths call one helper, `assert_report_releasable`, and a test spies on **both**
call sites — because gating one of two equivalent routes is exactly how this gap arose.

Non-production records stay exempt and stay watermarked. That is not a hole: they self-approve under
ADR-0029, carry the GRS-0229 mark on every rendition, and have no client on the other end. The
watermark is their gate, and putting them in the founder's queue would spend attention on work that
is not going anywhere.
