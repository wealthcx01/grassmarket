# GRS-0264 — Contacts base and certification capability gating

**Status:** OPEN (2026-09-03). **Priority:** LOW. **Type:** Two related decisions.
**Source:** R12. Gaps **G2 + G9**. **Waits on:** the G2 decision memo.

## Why — two halves

**Contacts.** `/entities/{id}/contacts` returns registry contacts per target. Scout-style matching
with a rationale, and assigning a contact to an advisor, still needs the **G2 decision on where the
contact base lives** — Grassmarket, bcap-base, or Holy Corner. Building matching before that is
building it twice.

**Gating.** Day one must hide what a Trained advisor cannot yet do — agents, contact assignment —
and say so in words rather than showing dead controls. Today the frontend infers capability from
level, which is a guess re-derived in every component.

## Build

- A per-level **capability map in the token**, so "can this advisor do X" is answered once,
  server-side, and the UI reads it rather than inferring it.
- Contact matching once G2 is answered.

**Do not invent the capability names.** They are a product taxonomy; take them from the
certification ladder as it actually exists.

## Done when

The token says what an advisor may do; day one hides the rest with a sentence explaining why, and no
component computes capability from level.
