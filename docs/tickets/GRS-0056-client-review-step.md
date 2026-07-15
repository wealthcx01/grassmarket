# GRS-0056 — Review-before-send on client-facing deliverables

- **Loop:** 4 (deliverables)
- **Status:** Fixed — the highest-value item from the 2026-07-15 UX audit (rubric #8, was Partial).
- **Severity:** Low/Medium — a consequential action lacked proportional friction in the UI.
- **Rubric basis:** #8 — deliberate friction on consequential/irreversible actions; friction
  proportional to consequence.

## Problem

Generating a **client-facing** deliverable is consequential — it produces an artifact intended to
reach a client. The UI generated it on a single click, identical to an internal draft. The backend
gates were already strong (client-usable coefficients, every AI section approved, committee sign-off
— all enforced at generate *and* download), but the *UI* placed no review moment on the act.

## Change

- Selecting **Client-facing** turns the primary button into **"Review & generate"**. Clicking it
  opens an explicit review step (not a generate) that states the document, that it is client-facing,
  and the three release gates it must pass — and warns inline if AI sections still await approval.
- The advisor **Cancels** or **"Generate client-facing document"** to confirm. **Internal drafts are
  unchanged** — one click, no friction (proportional).
- Switching back to Internal draft cancels any pending review.

## Exit criteria

- A client-facing generation requires the review step; Cancel backs out with nothing generated;
  confirm generates with `client_facing: true`. An internal draft still generates on one click.
  Pinned by `DeliverablesPanel.test.tsx` (7 tests).
