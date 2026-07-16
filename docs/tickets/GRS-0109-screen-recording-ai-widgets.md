# GRS-0109 — Screen-recording → AI video dissection → auto-populate the widget checklist

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Phase:** B (flagged follow-up — its own ADR/ticket set later)
**Depends on:** ADR-0009 (AI-approval gating)

## Why

The crown-jewel new capability from the review: an advisor logs into the target platform, **records
their screen, uploads the video, and AI dissects it** to auto-populate the widget checklist — feeding
the C-index with grounded depth on how good each platform really is. This goes well beyond the manual
widget scoring in the Part-1 C-index tickets (GRS-0080–0085) and beyond surfacing it (GRS-0108); it is a
**major, new AI/video initiative** and a significant lift. It is therefore **deferred behind Phase A**
and scoped as its own ADR / ticket set later (alongside GRS-0100/0101). It must be approval-gated per
ADR-0009 — AI-derived checklist values are proposals a human approves before they count.

## What to build

**Screen-recording ingestion → widget population (video AI initiative)**
- Let an advisor upload a screen recording of the target platform; run AI video dissection to detect
  widgets and populate the widget checklist that feeds the C-index (GRS-0108's surface).
- Gate every AI-derived checklist value behind the ADR-0009 approval flow (AI proposes, human approves)
  before it contributes to the C-index — nothing auto-committed.

## Acceptance / verification

- An uploaded screen recording drives AI dissection that proposes widget-checklist values.
- No AI-proposed checklist value contributes to the C-index without a recorded human approval
  (ADR-0009).

## Not in scope

- Manual widget scoring and the C-index computation — GRS-0080–0085.
- Surfacing the (manual) checklist/C-index in the wizard — GRS-0108.
- The full video-AI architecture and storage decisions — the deferred ADR.
