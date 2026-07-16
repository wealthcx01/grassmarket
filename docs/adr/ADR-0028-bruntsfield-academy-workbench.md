# ADR-0028 — Bruntsfield Academy / Workbench (one flagship program)

- **Status:** Accepted (2026-07-16). Founder-directed in the Part-2 UI/UX review: "probably one of the
  biggest build-outs to date." Build the training/certification/enablement layer as **one program**.
- **Date:** 2026-07-16
- **Deciders:** Founder + engineering
- **Normative source:** `docs/planning/PART2-uiux-review.md` §6.
- **Implements:** GRS-0121 (course-content-cms), GRS-0122 (sales-egoist-core), GRS-0123 (product-course-
  framework), GRS-0124 (benzinga-course), GRS-0125 (brandfetch-course), GRS-0126 (openbb-course),
  GRS-0127 (certification-restructure), GRS-0128 (workbench-hub), GRS-0129 (sales-ops-playbook),
  GRS-0130 (practice-calibration-content), GRS-0131 (cert-evidence-autolink), GRS-0132 (admin-oversight-hc).
- **Couples with:** ADR-0026 (Earnings v7 — the commission "carrot"); ADR-0009 (AI-approval gating —
  lesson drafts); the CLAUDE.md non-negotiables (#8 AI proposes/humans approve; practice-arena feedback is
  self-scoped and AI-labelled, not an approval record).

## Context

The Workbench is a mature 7-tab surface (bench / certification / learning & drills / practice arena /
calibration / rating requests / committee) with clean pure-domain backends (`src/grassmarket/workbench/`) and
ownership-scoped repositories. But its **training content is not modelled**: `LearningModule`
(`bcap_contracts/learning.py:84`) is a *titled pointer* (`kind`/`title`/`methodology_ref`/
`certification_credit`) with no lesson body, ordering, or media — the actual teaching material lives nowhere
in the system.

This matters because **commission on selling represented products is a primary way Bruntsfield Advisory
earns** (ADR-0026). Three products are signed — **Benzinga, Brandfetch, OpenBB** (ConnectTrade pending) —
each a potential solution to a gap found in an assessment *or* sold as-is. Advisers need in-depth,
maintainable course catalogs per product, plus a deepened **Sales Egoist** core module (the intro "Sales 101"
doctrine; two of eight lessons exist as teaser decks), all tied to the assessment work across retail
brokerage / wealth / exchange. This is the enablement engine that turns advisers into sellers.

## Decision

Build **one program — "Bruntsfield Academy"** — on top of the existing Workbench, binding twelve tickets:

1. **Content foundation (GRS-0121).** A versioned **Course → Module → Lesson → Drill/Assessment** content
   model with a **back-end editor** (replace/update without a deploy). Reuse the existing completion → coursework-
   credit → certification-evidence plumbing and the AI-draft **approval gate** already used for quizzes
   (`GeneratedQuiz`/`QuizStatus`), extended to AI-authored lesson drafts (ADR-0009).
2. **Sales Egoist core (GRS-0122).** Deepen the 8-lesson doctrine and make it the mandatory intro module,
   each lesson tied to Bruntsfield's assessment work.
3. **Product courses (GRS-0123 framework + GRS-0124 Benzinga + GRS-0125 Brandfetch + GRS-0126 OpenBB).**
   A per-product template that always answers why-relevant / white-labelling / sell-motion / **how much
   commission** (wired to Earnings v7, ADR-0026). The three courses are **VM research builds** — the VM
   spawns research agents over each product's public + developer docs (OpenBB additionally over Didier
   Lopez's blogs and the OpenBB blog/YouTube; the largest lift). We build our own structured catalog, not a
   link farm.
4. **Certification + hub + ops (GRS-0127/0128/0129).** Extend the existing `AssessorLevel` ladder
   (`common.py:180`) with course/product certs and senior↔junior pairing; make the bench the single hub for
   everything an adviser should / must / has done (and add the missing global-nav link to `/workbench`);
   author the sales operational process playbook from the v7 contracts.
5. **Practice/calibration + evidence linking (GRS-0130/0131).** Feed the practice arena + calibration from
   the course content; **auto-count real assessment participation** toward certification evidence (today
   shadow/observed-lead are honour-system admin entries) and reconcile the two overlapping high-stakes
   thresholds.
6. **Admin oversight (GRS-0132) — deferred to Holy Corner.** The admin **role already exists**
   (`Role.ADMIN`, `common.py:163`); the cross-consultant **oversight dashboards** (committee + learning +
   assessment progress) are a Holy Corner capability that consumes the existing admin claim. Nothing new is
   built in Grassmarket now beyond recording this.

## Consequences

- A genuinely new content-CMS subsystem (contracts + service + routers + admin-authoring UI), three product
  research/authoring build-outs, and the certification/hub/ops/practice expansions on top of the existing
  workbench domain logic — which is reused, not rebuilt.
- AI-authored lessons are approval-gated; practice-arena feedback stays self-scoped and AI-labelled (not an
  approval record) per non-negotiable #8. No client/partner data is committed — product docs, the Sales
  Egoist decks, and the v7 contracts are reference-only.
- Commission figures shown to advisers are computed by the Earnings v7 kernel (ADR-0026), never re-typed.

## Alternatives considered

- **Keep training content external/hardcoded.** Rejected — the catalog must be maintainable by non-engineers
  and versioned; a titled-pointer model cannot hold a course.
- **Build local admin oversight dashboards now.** Rejected/deferred — oversight across consultants is a Holy
  Corner (Bruntsfield OS) responsibility; Grassmarket only reserves and consumes the admin claim.
- **Phase the product courses behind the core module.** Rejected — the products are the revenue driver; they
  ship as part of the one program (the VM sequences OpenBB last only because it is the largest research lift).
