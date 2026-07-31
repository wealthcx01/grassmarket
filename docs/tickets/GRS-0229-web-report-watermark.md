# GRS-0229 — The shared web report must carry the non-production mark

**Status:** OPEN (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-31, first-time-user review G1). **Priority:** HIGHEST. **Type:** Bug._
**Loop:** client-report hardening. **Extends GRS-0220.** **Relates to:** ADR-0029, GRS-0219.

## Why

Reviewed live on staging 31/07/2026: the WeBull deliverable (a **sandbox** record) renders its PDF
with "DRAFT — not client-usable / NON-PRODUCTION DATA" on every page, and its shared web page at
`/r/<token>` with **no mark of any kind** — same record, same day, same content model. The page has
the tracking notice, the branding and the confidentiality footer, and nothing that tells the reader
the numbers describe nobody's actual platform.

GRS-0219 called a demo report escaping without the mark "the worst failure this document can have",
and the share link is precisely the escape route: it is the one rendition an outsider can reach
without a login. Worse, the sandbox promise on the new-assessment form reads "everything it produces
is watermarked and can never reach a client" — the web rendition breaks both halves of that sentence
at once, because sandbox records are exempt from the founder gate *on the strength of that promise*.

GRS-0220's test plan item 4 planned exactly this test ("a non-production record carries the mark on
the web page too"); its What-shipped list does not mention it. Either the test was never written, or
it asserts something the page does not render. Find out which and say so in the PR.

## Scope

1. **The mark on the page.** A non-production or draft record renders a persistent, unmistakable
   banner on `/r/<token>` — not a footer line: fixed or repeated so it is visible at every scroll
   position, on phone widths too. Same two distinctions the PDF draws: draft (unapproved for client
   use) and non-production data (demo/sandbox). Reuse the PDF's wording so the two renditions say
   the same thing (GRS-0220 scope 2: one source, two renditions).
2. **The snapshot must carry the flag.** The shared page serves a snapshot stored at issue. The
   production/demo/sandbox provenance must be stored *in* the snapshot, so a record later
   reclassified cannot retroactively change what an already-issued link shows.
3. **Audit the issue path.** Establish whether a sandbox/demo deliverable should be able to issue a
   share link at all. Decision to state in the PR: either links on non-production records are
   refused, or they are allowed and watermarked. (Allowed-and-watermarked is the recommendation —
   advisors need to preview the client experience — but say which and why.)
4. **Why the gap existed.** One paragraph in the PR on how GRS-0220 shipped without this, given its
   own test plan named it. If a watermark test exists and passes, explain what it actually asserts.

## Test plan

1. Backend: issuing a link on a DEMO and a SANDBOX deliverable produces a snapshot whose payload
   carries the non-production flag; a production record's does not.
2. Frontend vitest: the public report shell renders the banner when the flag is set, at the top and
   persistently; absent for production.
3. Manual: re-issue the WeBull link on staging, screenshot top / mid-scroll / phone width, in the PR.
4. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- The PDF watermark (GRS-0219, correct today).
- Founder-gate coverage of share links on production records (GRS-0245).
- Figure labelling on the web page (GRS-0233).

## Acceptance

The founder opens a share link for any demo or sandbox record and cannot read a single screen
without knowing the numbers are not production. A production record's link is unchanged.

---

## Status reconciliation — 2026-08-01

**OPEN.** Scheduled in the GRS-0229–0245 wave (see docs/BACKLOG.md for the build order).
