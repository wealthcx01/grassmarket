# GRS-0129 — Sales operational process playbook

**Status:** Shipped
**Loop:** Part 2 — Bruntsfield Academy / Workbench (one program)
**Depends on:** ADR-0028 (Bruntsfield Academy / Workbench), GRS-0121 (content CMS)

## Delivered

A **Sales Operations Playbook** course authored through the GRS-0121 CMS
(`workbench/content/sales_ops_playbook.py`), seeded idempotently alongside Sales Egoist. Four
lessons walk the advisor's standing operational motion **keyed to the real `PipelineStage` values**
(prospect → workshop_scheduled → workshop_delivered → qualified → scoped → contracted → active →
delivered), so the process the CRM (§4) enables and the process the Academy teaches line up. Grounded
in the **v7 two-stream commission schedule** — product Stream A / consultancy Stream B (delivery_type
× sourcing, self- vs firm-sourced) + workshop recovery fees — referenced, never re-typed as figures
(the live numbers stay on the product courses, GRS-0123). Pure content on the existing CourseTree —
no contract/schema/frontend change; the course surfaces automatically in the catalog + the hub.
Golden master untouched.

## Why

Advisers need a documented **operational process** for what they actually do when they meet a prospect —
the standing motion, not just the sales doctrine. The source of truth is the **v7 Consultant Agreement +
Commission Schedule** and the represented-company contracts. This playbook ties the Pipeline / GTM engine
(§4) to the Workbench so the process the CRM enables and the process the Academy teaches are the same.

## What to build

- A **process module** authored through GRS-0121's CMS describing the advisor's operational motion on
  meeting a prospect, sourced from the **v7 Consultant Agreement + Commission Schedule** and the
  represented-company contracts (reference-only; not committed).
- Cross-link the playbook to the Pipeline / GTM engine (§4) so the CRM stages and the taught process
  correspond.

## Acceptance / verification

- A sales-ops process module exists in the CMS, grounded in the v7 agreement + commission schedule.
- The module cross-references the Pipeline/GTM stages so process and tooling line up.
- Content is CMS-authored (no hardcoded copy), consistent with GRS-0121.

## Not in scope

- The v7 contract documents themselves (reference-only, not committed).
- The Pipeline / GTM engine build (§4 tickets).
