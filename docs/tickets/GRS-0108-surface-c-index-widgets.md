# GRS-0108 — Surface the widget checklist + Customer Proposition Index in the wizard

**Status:** Shipped
**Loop:** Part 2 — Advisor Studio UI/UX review
**Phase:** A (build now)
**Depends on:** ADR-0023 (C-index) / GRS-0080–0085

## Why

The founder was emphatic here — "so crucial, we're missing the point": the widget checklist
(present/absent per widget) and the **Customer Proposition Index** (Ease / Usability / Depth feeding the
C-index) are the heart of judging how good a platform actually is, yet they're buried. The C-index and
its widget scoring already exist as Part-1 work (ADR-0023 / GRS-0080–0085); this ticket is a
**surfacing/prominence** job, not new computation — bring the widget checklist and C-index forward in
the wizard as a first-class, prominent step so advisors treat it as central rather than incidental.

## What to build

**Wizard (`components/steps.tsx`, `app/assessments/[id]/WizardClient.tsx`)**
- Present the widget checklist (present/absent) and the Ease / Usability / Depth inputs feeding the
  C-index as a prominent, first-class step in the flow.
- REUSE the Part-1 C-index computation and widget scoring (GRS-0080–0085) — this ticket surfaces and
  elevates them, it does not re-implement the index.

## Acceptance / verification

- The widget checklist and C-index (Ease/Usability/Depth) appear as a prominent wizard step, not a
  buried afterthought.
- The surfaced inputs feed the existing Part-1 C-index computation unchanged.

## Not in scope

- The C-index computation and widget model itself — GRS-0080–0085.
- Screen-recording → AI auto-population of the checklist — GRS-0109 (Phase B).

## What shipped (Status: Shipped — branch grs-0108-surface-c-index)

Elevated the widget checklist + Customer Proposition Index from incidental to front-of-mind (the
computation is Part-1 / GRS-0080–0085 — this is pure surfacing):

- **C on the live side rail, every step** (`WizardClient` `LiveSummary`) — a prominent "C — CUSTOMER
  PROPOSITION" card (the score /100) now sits beside V in the sticky rail, visible on every wizard step
  and as soon as C is scoreable (independent of V-scoreability). Previously C only appeared on the
  Summary step; now the widget-driven view of platform quality stays in view throughout.
- **Reframed the Customer Proposition step intro** to lead with what it is for — *"This is where you
  judge how good the platform actually is for a customer"* — and to name the Ease · Usability · Depth
  scoring and the rare-done-well / common-missing logic explicitly, so advisors treat it as central.

Reuses the Part-1 C-index computation and widget scoring; no new index.

## Acceptance / verification

The widget checklist + C-index are a prominent, first-class part of the wizard (a live C card on every
step + a reframed step intro), reusing the existing C computation. Frontend type-check · lint · vitest
green.
