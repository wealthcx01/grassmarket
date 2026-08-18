# GRS-0245 — Founder sign-off covers everything that reaches a client

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-31, first-time-user review; founder decision 23/07 item 24)._
**Priority:** HIGH. **Type:** Policy gap. **Loop:** client-report hardening.
**Extends GRS-0188 / ADR-0041.** **Relates to:** GRS-0220, GRS-0229.

## Why

The founder's rule, 23/07: "all client drafts of reports should go to me… I will sign and approve
everything that goes out." The Workbench Founder-review tab promises the same: "Every assessment
that is going to a client comes through here first."

Demonstrated on staging 31/07/2026: a share link for the WeBull report was written, saved, issued
and opened publicly **without anything appearing in the founder review queue**. The gate on the
client-facing path (`assert_client_ready`, wired by the GRS-0220 correction) checks that
*AI-drafted* sections carry approvals — and every section was consultant-written, so it passed
trivially. Human-authored prose currently reaches a client with no founder sign-off at all, which
inverts the intended hierarchy: the founder gate exists because *human judgement* signs what goes
out, not because AI text is uniquely dangerous.

(The staging demonstration was on a sandbox record, where exemption is arguably by design — but the
same code path governs production records, and nothing in it consults founder approval for
human-written sections. Verify and state the exact production behaviour in the PR before changing
it; if production is already gated somewhere this analysis missed, this ticket becomes the test
that proves it.)

## Scope

1. **Establish the actual gate matrix first.** A table in the PR: {record provenance: production /
   demo / sandbox} × {path: PDF download, share-link issue, docx client pack} × {prose authorship:
   human / AI-drafted} → what is required today. Measured from code, with file references.
2. **Close the gap.** On production records, issuing a share link or downloading the client PDF
   requires a current founder approval of the report content — regardless of authorship — through
   the existing ADR-0041 machinery (hash-bound: editing prose after approval invalidates it, same
   rule the Founder-review tab already states for assessments). Demo/sandbox records stay exempt
   and stay watermarked (GRS-0229) — the watermark is their gate.
3. **The refusal teaches.** An advisor issuing a link before approval is told exactly where the
   report is in the review queue and what happens next, in the product voice (GRS-0230's error
   surface).
4. **The queue shows it.** Client reports awaiting sign-off appear in the Founder-review tab beside
   assessments, with a diff-aware view of the six sections since any prior approval.

## Test plan

1. Backend: production record + unapproved prose → link issue and PDF refuse; approval → both
   succeed; any prose edit after approval → refuse again (hash invalidation). Sandbox/demo: allowed,
   watermark flag asserted on the snapshot.
2. The GRS-0220 test that fails if `assert_client_ready` is removed extends to fail if the founder
   check is removed.
3. Vitest: queue renders pending reports; refusal copy names the queue state.
4. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- The watermark itself (GRS-0229).
- Approval UX beyond the existing founder-review surfaces (no new roles, no delegation — ADR-0041
  owns the model).
- AI drafting (GRS-0222) — when it lands, its sections flow through this same gate unchanged.

## Acceptance

Nothing generated from a production record can reach a client — by PDF or by link — without the
founder having approved the exact words it carries, and the founder can see that queue in the place
the product already told them to look.

---

## Status reconciliation — 2026-08-01

**DONE.** Matrix, measurement and post-change state in
`docs/reviews/GRS-0245-founder-gate-share-links/gate-matrix.md`.

## What shipped

**Scope 1 — the matrix, measured before anything changed.** Production was **not** already gated:
on a production record with prose written after the founder approved the assessment, the PDF
downloaded (200), the link issued (201) and the public page read (200). The mechanism is that the
gate was bound to the wrong artefact — `current_founder_approval` matches
`sha256(document_json)`, the *assessment*, while the report prose lives in another table and is
written after finalisation.

**Scope 2 — the gap closed.** A report-scoped approval on `founder_approvals`
(nullable `deliverable_id` + the prose hash, migration `0037`), and both client-report release
paths now take one shared helper, `assert_report_releasable`. Hash-bound: editing any section after
approval invalidates it, the same rule the Founder-review tab already states. Demo and sandbox stay
exempt and stay watermarked — the GRS-0229 mark is their gate.

**Scope 3 — the refusal teaches.** Three states, three sentences: never submitted (with the next
action), submitted and waiting, or approved-and-then-edited (naming the sections that changed). The
report editor gained a **Send to the founder for review** button beside where the advisor is
stopped, because an instruction with no affordance next to it is a dead end dressed as guidance.

**Scope 4 — the queue shows it.** Client reports appear in the Founder-review tab beside
assessments, labelled as reports, linking to the report rather than the assessment, and carrying a
**diff**: which of the six sections differ from the version the founder last approved. That needed
the approval to store the prose it cleared, not just its hash — a hash can say "this differs", only
the content can say where to look.

## Notes for whoever reads this next

- The approval row keeps its `assessment_id` even for report approvals, so scoping and queue joins
  are unchanged. Two scopes, one table, one rule.
- The queue's React key had to become `report:<id>` / `assessment:<id>`: a report is submitted
  against an assessment that was itself reviewed, so both rows can carry the same `assessment_id`
  and keying on it alone collapsed them into one row. There is a test for that.
- A first review reports **no** changed sections rather than "all six". Empty means "nothing to
  compare against", and telling the founder to re-read work they have never read once would make
  the diff worse than useless.
- `test_client_report_wiring.py` needed the founder approval added to seven tests that released a
  production report. That is the behaviour change working, not collateral damage.
