# GRS-0263 — Agents: run store, held plans, spend

**Status:** OPEN (2026-09-03). **Priority:** LOW (gates nothing). **Type:** Feature.
**Source:** R11. Gaps **G1 + G10**. **Waits on:** the G2 decision memo (where the contact base lives).

## Why

The desk shows what Scout and Scribe did overnight, plans they are **holding** for a read, and
weekly spend. No agent endpoints exist. The frontend ships "agents not yet enabled" and is honest
about it, so this gates nothing.

## Build

Run store, scheduler, and the **propose → hold → approve** cycle. Per-run cost and a weekly budget.

**The hold is the point.** A held plan releases only on an explicit press — non-negotiable #8 in the
one place where an agent could most plausibly be allowed to "just get on with it". An agent that
acts on a timeout is not this product.

Relates to GRS-0248: if ActiveGraph is ever adopted, this is the surface with the strongest case —
run store, replay and fork-and-diff are its primitives.

## Done when

An overnight run is visible with what it did, what it cost, and what it is holding; nothing it
proposes reaches a client without a press.
