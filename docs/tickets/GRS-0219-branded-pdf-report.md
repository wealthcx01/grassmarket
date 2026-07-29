# GRS-0219 — The client report as a Bruntsfield-branded PDF

**Status:** Planned (2026-07-26, staging review item 9). **Priority:** HIGHEST.
**Loop:** founder-feedback remediation, Wave 3. **Depends on:** GRS-0211 (narrative content model).

## Why

The founder downloaded the Deliverable Preview for Deutsche Börse and said it "has no branding".
That is the least of what is wrong with it, but it is the most fixable and the most visible: a
document that goes to a client with none of our identity on it reads as a machine's output, which
is exactly what it is at the moment.

GRS-0211 settles what the report *says*. This ticket is what it *looks like* as a PDF. They are
split because the content model has to be right before the rendering is worth polishing, and
because two people can work on them at once.

## Scope

1. **A real cover.** Client name, the engagement, the date, the Bruntsfield mark. Not a title
   heading on page one.
2. **Typography from the design system.** Source Serif 4 for body, Inter for UI-adjacent labels and
   captions, IBM Plex Mono for figures and keys. Paper/ink palette, Bottle Green `#1A3B26` as the
   single accent. Sizes and leading set once as tokens, not per element.
3. **Page furniture.** Running heads carrying the client and section, page numbers, a contents page
   for anything over eight pages, and a clear break between the narrative body and the technical
   appendix so a reader knows when they have left the story.
4. **Figures that survive print.** The maturity radar, the value build-up and the module breakdown
   rendered at print resolution, legible in greyscale, with the same colour semantics as the web
   version. A chart that only works in colour is a chart that fails in a boardroom printout.
5. **Tables that break properly** across pages, with repeating headers.
6. **Confidentiality and provenance footer**: who prepared it, when, the methodology and
   coefficient versions, and the non-production watermark when the record is demo or sandbox. The
   watermark rule is unchanged (ADR-0029) and must be tested, because a demo report escaping
   without it is the worst failure this document can have.

## Test plan

1. Golden-master render: one finalised assessment renders to a PDF whose extracted text matches a
   committed fixture, so prose and structure regressions are visible in review.
2. Watermark test: a demo or sandbox record renders with the non-production mark; a production
   record does not.
3. Greyscale legibility check on the three figures, asserted on the generated image rather than by
   eye.
4. Manual: the founder's Deutsche Börse record rendered and attached to the PR.
5. Standing gate: pytest, pyright, ruff.

## Out of scope

- What the report says (GRS-0211).
- The interactive web version (GRS-0220).
- Tiering of what a free versus engaged client receives (GRS-0214).

## Acceptance

The founder opens the PDF and it looks like something Bruntsfield would put its name on, before
reading a word of it.
