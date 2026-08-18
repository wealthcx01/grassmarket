# GRS-0231 — The report editor must name the client

**Status:** Planned (2026-07-31, first-time-user review G3). **Priority:** MED-HIGH. **Type:** Bug.
**Loop:** client-report hardening. **Extends GRS-0211.**

## Why

The report editors for WeBull (`/deliverables/f6312cfe…/report`) and Hargreaves Lansdown
(`/deliverables/e5cca720…/report`) are pixel-identical pages titled "What the client reads". The
only place the firm's name exists is the URL. An advisor with two engagements open in two tabs will
eventually write one client's constraint narrative into the other client's report, and nothing on
the page can catch it. For a surface whose whole doctrine is "the same words become the branded PDF
and the shared web page", not knowing whose words these are is the one context that matters most.

Secondary, same page: all six textareas expose the same accessible name (the shared placeholder
"Blank lines separate paragraphs."), so a screen-reader user cannot tell the Business section from
the Appendix.

## Scope

1. **Header carries the identity.** Client name, engagement title, segment badge, and the
   provenance badge (demo/sandbox/production) at the top of the editor — the same identity block
   the PDF cover prints, so editor and artefact visibly agree. Breadcrumb back to the engagement.
2. **The browser tab too.** Document title becomes "Client report — WeBull", not the generic app
   title, so two open editors are distinguishable in the tab strip.
3. **Accessible names per section.** Each textarea is labelled by its section heading
   (`aria-labelledby` or explicit label association), placeholder demoted to placeholder.
4. **The PDF download states its subject.** The confirmation the button gives (per GRS-0230) names
   the client, one more chance to catch cross-client error at the moment of export.

## Test plan

1. Vitest: editor renders client name and engagement title from the deliverable payload; document
   title includes the client name.
2. Vitest: each of the six textareas has a distinct accessible name matching its section heading
   (assert via accessibility queries, not class names).
3. Manual: both staging editors screenshotted side by side in the PR, now distinguishable.
4. Standing gate: tsc, ESLint, per-file vitest.

## Out of scope

- Feedback placement and figure declaration (GRS-0230).
- The deliverables list and engagement navigation (GRS-0241).

## Acceptance

The founder opens the two report editors in two tabs and can tell them apart from the tab strip
alone, and from any scroll position on the page.


**DONE.** All four scopes.

## What shipped

**1 — The client's name IS the heading.** "What the client reads" described the page and named
nobody; it is now the firm. Beneath it: engagement title, operating model in words, and a badge for
non-production records. The identity comes from the *same* assembly path the PDF cover uses, so the
editor and the artefact cannot disagree about whose report this is — returned on the prose fetch the
editor already makes rather than from a second call.

**2 — The browser tab.** `Client report — WeBull`, restored on unmount. Two open editors are now
distinguishable in the tab strip, which is where an advisor actually switches between them.

**3 — Six distinct accessible names.** Each textarea is `aria-labelledby` its own visible heading;
the shared placeholder is demoted to a hint. Tested through accessibility queries —
`getByRole("textbox", { name: "The business" })` — rather than class names, which is a screen-reader
user's view of the page rather than a proxy for it.

**4 — The export names the client.** "PDF downloaded — WeBull." One more chance to catch a
cross-client mistake at the moment of export, which is the last point at which catching it is free.

## A note on the production badge

Only demo and sandbox are badged. Badging *production* too would have made the warning badge mean
nothing — a marker every record carries stops being a marker.
