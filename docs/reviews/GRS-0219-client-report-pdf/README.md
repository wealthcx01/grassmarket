# GRS-0219 — the client report as a branded PDF

Two rendered samples, both from the Meridian golden-master run relabelled as Deutsche Börse so the
non-ASCII client name is exercised:

- **`report-client.pdf`** — a clean client document. This is the one to judge.
- **`report-draft.pdf`** — the same report on a draft coefficient set and a non-production record,
  so both watermarks are visible on every page.

## What to look at

**The cover.** Wordmark, accent rule, client name in Source Serif 4, engagement and date in Inter.
A real cover, not a title heading on page one.

**The running heads.** Client on the left, section on the right, naming the section the page *opens*
in. A first cut named the section the page *ended* in, which put "What is holding it back" above a
page beginning "The business" — so the document is built twice: pass one records which page each
section starts on, pass two draws the heads from that map.

**The break into the appendix.** A rule and a line of copy saying the story ends there. The founder
asked for the maths moved out of the reader's way; the content model (GRS-0211) already refuses
P10/P50/P90 in the body, and this is where it is allowed back in.

**The figures table.** Repeating header across the page break (scope item 5). Its column widths are
measured with `pdfmetrics`, not guessed — a guess rendered the coefficient version as
"v1-draft-pen ding-elicita tion", which reads as a typo in a client document.

## Typography

Source Serif 4 (body), Inter (labels, captions, the mark), IBM Plex Mono (figures and keys) —
vendored into `src/grassmarket/deliverables/assets/fonts/` by
`scripts/vendor_report_fonts.py`, with each family's SIL OFL licence beside it. reportlab can only
embed a TTF that is on disk, and it substitutes Helvetica *silently* when a face is missing, so a
missing face raises `MissingReportFontError` instead.

Inter ships only as a variable font upstream; reportlab renders a variable TTF at its default
instance, which would have given Regular everywhere SemiBold was asked for. The two static weights
are therefore instanced with fontTools at build time rather than downloaded.

## Greyscale

Nothing is encoded by hue alone. Every series carries a luminance step **and** a hatch **and** a
printed value. The palette's pairwise luminance separation is asserted in tests: the first attempt
used plausible-looking greens whose first two steps were only 0.101 apart — distinct on screen,
identical on a laser printer — and the test caught it. The shipped ramp is spaced ~0.19.
