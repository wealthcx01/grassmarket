# GRS-0123 — Product-course framework + the commission "carrot"

**Status:** Shipped
**Loop:** Part 2 — Bruntsfield Academy / Workbench (one program)
**Depends on:** ADR-0028 (Bruntsfield Academy / Workbench), GRS-0121 (content CMS), ADR-0026 (Earnings v7)

## Delivered

A reusable **product-course template** on the GRS-0121 content model
(`workbench/content/product_course.py`): a `ProductCourseSpec` (product_id, relevance, white-label,
sell-motion) → a four-section `CourseTree` in fixed order — **Why it's relevant / What white-labelling
is / The sell motion / How much you earn**. The commission section is **generated from a live
`ProductCommissionCarrot`**, never a re-typed number. The carrot
(`earnings/product_carrot.py` → new `ProductCommissionCarrot` contract) resolves the Year-1/Year-2
rates + a worked £ example straight from the Earnings v7 schedule via `compute_product_commission`
(ADR-0026), stamped with the schedule version so it can't drift. New live endpoint
`GET /earnings/product-commissions`; the earnings page shows the live carrot cards. Fails loud on an
unknown product; template rejects a spec/carrot product mismatch. GRS-0124/0125/0126 instantiate it
per product with no bespoke structure. Golden master untouched (Money, not Score — ADR-0002).

## Why

Commission on selling the signed products (Benzinga, Brandfetch, OpenBB) is one of the primary ways
Bruntsfield Advisory earns, and the products double as **solutions** an advisor can recommend against
gaps found in an assessment. Every product course therefore needs the same spine, and it must show the
advisor — prominently — **how much commission they earn**, using the £ carrot to motivate. This ticket
builds the reusable template that GRS-0124/0125/0126 fill in.

## What to build

- A **per-product course template** on GRS-0121's content model that always answers: **why the product
  is relevant** to a retail broker / wealth manager / exchange, **what white-labelling is**, the
  **sales/introduction motion**, and — prominently — **how much commission the advisor earns**.
- Wire the commission figure to **Earnings v7 / ADR-0026** rates via `earnings/`, **not re-typed** — the
  carrot reads live rates so it can't drift from the real schedule.
- Frame it so a product course maps to an assessment-identified gap where one exists (sold as a fix), or
  stands alone as a commission product where it doesn't.

## Acceptance / verification

- A product course instantiated from the template exposes all four required sections (relevance,
  white-label, sell motion, commission).
- The commission figure resolves from the Earnings v7 compute (ADR-0026), not a hardcoded number.
- The template is reusable — GRS-0124/0125/0126 instantiate it without bespoke structure.

## Not in scope

- The individual product content (Benzinga 0124, Brandfetch 0125, OpenBB 0126).
- Changes to the Earnings v7 rates themselves (ADR-0026 owns those).
