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

## What shipped

`grassmarket.deliverables.report_pdf` renders a `ClientReport` (GRS-0211) to a branded PDF. Samples
for review, both from the golden-master run: `docs/reviews/GRS-0219-client-report-pdf/`.

**Scope items 1–6 are all in.** A real cover (wordmark, accent rule, client, engagement, date);
typography set once as tokens in `report_pdf/tokens.py` mirroring `globals.css`; running heads,
folios, and a ruled break into the appendix; figures at 300dpi; a figures table that repeats its
header across page breaks; and a provenance footer carrying preparer, date, methodology and
coefficient versions.

**Four things were harder than the ticket assumed, and each changed the implementation:**

1. **The house fonts were not in the repo at all.** The frontend gets them from `next/font/google`
   at build time, which is no help to a Python renderer, and reportlab can only embed a TTF on disk.
   They are now vendored by `scripts/vendor_report_fonts.py` (~1.7MB, all SIL OFL 1.1, each licence
   committed beside its family). reportlab substitutes Helvetica *silently* when a face is missing —
   precisely the "no branding" failure this ticket exists to fix — so a missing face now raises.
2. **Inter ships only as a variable font.** reportlab renders a variable TTF at its default
   instance, so asking for SemiBold would have silently produced Regular. The two static weights are
   instanced with fontTools at vendoring time.
3. **A running head cannot be drawn in one pass.** `onPage` fires before the page's flowables are
   laid out, so the head named the previous page's section; `onPageEnd` names the *last* section on
   the page, which is equally wrong. The document is built twice — pass one records which page each
   section begins on, pass two draws from that map.
4. **The greyscale palette I first chose did not meet its own contract.** Two adjacent fills were
   0.101 apart in luminance against a declared 0.15 minimum — different colours on screen, the same
   grey on a printer. The test caught it; the shipped ramp is solved for ~0.19 separation. Column
   widths in the figures table are likewise measured with `pdfmetrics` rather than guessed, after a
   guess broke the coefficient version into "v1-draft-pen ding-elicita tion".

**Test plan status.** Golden-master render on extracted text (1), watermark on/off for draft and
non-production (2), greyscale legibility asserted on the palette *and* on the generated image (3),
and samples committed for the founder (4). 17 tests; ruff, pyright clean.

**Still not visible in the app.** This renders a report; nothing yet calls it from a route. Wiring
the download into the deliverables surface is the last mile and is not in this ticket's scope.
