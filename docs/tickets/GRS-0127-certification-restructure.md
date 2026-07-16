# GRS-0127 — Certification restructure

**Status:** Planned
**Loop:** Part 2 — Bruntsfield Academy / Workbench (one program)
**Depends on:** ADR-0028 (Bruntsfield Academy / Workbench)

## Why

The Academy needs a basic certification set — a **Sales Egoist cert + one cert per product** — on top of
the existing assessor ladder. The **ladder already exists**: `AssessorLevel` TRAINED → SHADOW →
OBSERVED_LEAD → CERTIFIED_LEAD (`bcap_contracts/common.py:180`, carried in the JWT `assessor_level`
claim), gated by `promotion_blockers` (`workbench/certification.py:39`). The gap is course/product
certifications and wiring certification to **senior↔junior operator pairing** — extend the ladder, don't
rebuild it.

## What to build

- Extend certification with **course/product certs** (Sales Egoist + one per product), distinct from the
  assessor ladder but reusing its machinery: `CertificationRecord` / `CertificationEvent`
  (`certification.py`) + `promotion_blockers`.
- Wire certification to **senior↔junior operator pairing** so promotion reflects real pairing, not just
  self-report.
- Surface the extended cert set in the panel. Files: `workbench/certification.py`,
  `bcap_contracts/certification.py`, `CertificationPanel.tsx`.

## Acceptance / verification

- A Sales Egoist cert and a per-product cert exist alongside the assessor ladder and reuse
  `CertificationRecord`/`CertificationEvent` (no parallel cert store).
- Course/product cert progress is gated through `promotion_blockers` consistent with the ladder.
- `CertificationPanel.tsx` renders the new cert set.

## Not in scope

- Auto-computing certification *evidence* from assessment participation (GRS-0131).
- The course content the certs sit on (GRS-0122/0124/0125/0126).
