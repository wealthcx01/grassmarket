# GRS-0203 — The thin outreach sequencer over the GTM registry

**Status:** Draft — not scheduled (2026-07-25, from the GRS-0195 spike). **Priority:** TBD.
**Loop:** follow-on. Depends on GRS-0202 (the gate) and GRS-0204 (the send path decision).

## Why

The "build thin" half of the GRS-0195 recommendation. The registry (GRS-0193) holds the targets and
contacts, the influencer maps (GRS-0194) give a named path into them, and GRS-0202 gives the
approval gate. What is missing is the small piece that turns a selection of contacts into a
reviewable set of drafted messages.

## Scope

1. **Sequence.** An advisor selects contacts from the registry, picks a template, and generates one
   `OutreachMessage` per contact in `proposed`. Suppressed contacts are excluded at generation
   rather than at send, so they never appear in a review queue.
2. **Review queue.** One surface listing proposed messages, each approvable or rejectable
   individually. Bulk approval is deliberately excluded: a gate that can be cleared without
   reading is not a gate.
3. **Operator-triggered only.** No scheduled sends, no cadence engine, no automatic follow-up.
4. **The compliance caveat from GRS-0194 renders on the review queue** whenever any selected
   contact came from a sell-side roster, because that is the moment it is relevant.

## The scope boundary (from the spike)

GRS-0195 recorded an explicit trigger to stop and reconsider: **if this grows past a single
bounded module** — multi-channel sequencing, reply classification, or branching cadences — it has
become a workflow engine, and adopting n8n beats building one. Any of those three arriving in a
follow-up ticket is the signal to re-run the GRS-0195 comparison rather than extend this.

## Test plan

- A generated sequence excludes suppressed contacts.
- Every generated message starts `proposed`; none can reach a send path without approval.
- Owner-scoping on the review queue.

## Out of scope

- The gate and suppression list (GRS-0202). The send transport (GRS-0204). Reply handling.

## Acceptance

An advisor can select registry contacts, generate drafts, and review them one at a time, with
suppressed contacts never appearing and nothing sendable until approved.
