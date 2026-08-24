# GRS-0234 — PDF furniture: the filename, the subtitle, the footer, the precision

**Status:** MOSTLY DONE — scope 4 half built (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-31, first-time-user review G6). **Priority:** MED._
**Loop:** client-report hardening. **Extends GRS-0219.** **Relates to:** ADR-0040, GRS-0150.

## Why

The report body is now something Bruntsfield could put its name on; the furniture around it is not.
Observed on the staging WeBull and Hargreaves Lansdown PDFs, 31/07/2026:

- **The downloaded file is named `f6312cfe-4310-4dba-8a25-0c2c3bd77a57.pdf`.** An advisor will
  forward a database UUID to a CFO, or waste a minute renaming every export.
- **The cover subtitle reads "WeBull — delivery"** — the engagement's internal title, which reads as
  a system key, under an otherwise good cover.
- **Every page's footer prints `coefficients v1-draft-pending-elicitation`.** Provenance honesty is
  right (GRS-0219 scope 6) and stays; the wording is an internal config identifier. A client-facing
  sentence carrying the same fact reads: "Draft weighting — pending expert panel ratification."
  The identifier can live in the appendix's version table, where identifiers belong.
- **Page 4 of the WeBull sample is one chart and ~90% white space** — the figure placement strands
  the value build-up on its own page when the preceding section runs short.
- **The portfolio quotes V as 54.7 where the PDF appendix quotes 55** (`v_display_0_100` rounded).
  Same number, two precisions; an advisor saying "54.7" to a client holding a page saying "55" is
  friction the one-number rule (ADR-0040) exists to prevent. Pick one display precision for V and
  apply it on every surface and both renditions.

## Scope

1. **Filename:** `Bruntsfield — Platform assessment — <Client> — <YYYY-MM>.pdf` (sanitised for
   filesystem), set via Content-Disposition; the web download honours it.
2. **Cover subtitle:** derived from deliverable type + client ("Platform Power assessment", already
   line 1) with the engagement title dropped or humanised; no internal keys on the cover.
3. **Footer wording:** plain-English coefficient status sentence from a single mapping owned by
   contracts (draft / elicited / ratified → sentence), identifier retained in the appendix table
   only. The mapping is data, so GRS-0150's eventual ratification changes the sentence without a
   code edit.
4. **Figure flow:** allow the build-up figure to share a page with the section that references it
   (keep-with heuristics), and add a regression check that no interior page of the golden-master
   sample is >80% empty.
5. **Precision:** one display rule for V (recommend one decimal, matching the wizard), applied in
   the PDF figures table, web appendix, portfolio, stage 6 and engagement header. State the rule in
   ADR-0040's terms in the PR.

## Test plan

1. Backend: Content-Disposition filename asserted for a demo record; UUID absent.
2. Golden-master render re-baselined once, with the diff reviewed line by line in the PR (the text
   fixture changes here by design; scoring does not — golden master engine values byte-identical).
3. Footer mapping unit tests: three statuses, three sentences, identifier only in the appendix.
4. Page-fill check on the sample PDFs.
5. Standing gate: pytest, pyright, ruff.

## Out of scope

- What the report says (GRS-0211) and the web page (GRS-0220/0229/0233).
- Actually ratifying coefficients (GRS-0150).

## Acceptance

The founder downloads a report and could attach it to a client email unedited: the filename says
what it is, the cover carries no keys, and the footer's caveat reads as a sentence a client can
understand.

---

## Status reconciliation — 2026-08-01

**MOSTLY DONE.** Four scopes shipped. Scope 4 is half done and the half that is not is stated below
rather than glossed.

## 1 — The filename, and the reason it was a UUID

The backend was **already** naming the file after the client. The UUID came from the frontend
falling back to `${deliverableId}.pdf` because it could not read `Content-Disposition` — that header
is not CORS-safelisted, and `expose_headers` was never set. `allow_headers` governs the *request*;
exposing a *response* header is a separate list, and the asymmetry is easy to miss.

Both halves fixed. The name is now
`Bruntsfield — Platform assessment — <Client> — <YYYY-MM>.pdf`, punctuation-stripped because it
crosses a filesystem, an email client and whatever the recipient uses, and sent in both spellings —
RFC 5987 `filename*` for the real name, a plain ASCII `filename` for anything that cannot read it.

## 2 — The cover

The engagement title is **dropped**, not humanised. The title above it is the client and the line
above it is the document, so a third line could only repeat one of them.

## 3 — The footer

`COEFFICIENT_STATUS_SENTENCES` in contracts maps status → sentence, so GRS-0150's ratification
changes the words by changing which status the set carries rather than by editing a renderer. The
identifier keeps its place in the appendix version table — asserted to appear exactly **once** in
the document rather than once per page.

A set that is client-usable and still names itself draft resolves to the *weaker* sentence. A
labelling mistake must not be able to produce a stronger claim than the evidence.

## 5 — One precision for V

One decimal, everywhere. The portfolio quoted 54.7 where the appendix quoted 55 — the same number at
two precisions, which is what ADR-0040's one-number rule exists to prevent. The rule is about the
*displayed* number: a reader cannot tell rounding from disagreement.

One decimal rather than zero because the wizard and portfolio already use it; rounding the surfaces
an advisor reads daily to match a document they send occasionally is the wrong way round. Module
scores keep 0dp — they are read as a ranking, V is read as a value.

## 4 — Half done, and the half that is not

**Done:** a regression check that no interior page of the three sample PDFs is effectively blank.

**Not done:** the sparse page. Narrowing the build-up figure to 0.72 of the frame was tried as the
cheap fix and **measured not to help** — across all three samples the page stayed at ~300–460
characters beside the chart. The change was reverted rather than kept, because it had no effect and
its comment would have claimed one; the finding is recorded in `render.py` where the next person
will look.

The cause is not the figure's width. It is the VALUE section's own length plus a figure that
`KeepTogether` will not split. A real fix is a reportlab keep-with rule binding the figure to its
preceding paragraph, and that is not written here.

The regression check is therefore narrower than the ticket asks: it catches a genuinely blank page,
which is a rendering fault, and does **not** catch a thin one, which is the reported symptom. Said
plainly in the test's own docstring so nobody reads it as covering more than it does.

## Golden master

Re-baselined once. The diff is exactly three things and nothing else: the cover subtitle removed,
five footer lines rewritten, and `48` → `47.9`. **Engine golden master untouched** — 56 golden tests
pass unchanged.


---

## Scope 4, third attempt — 2026-08-24. Still not fixed, and now bounded.

Attempted again with the "real fix" the previous note proposed. **It made the document worse**, so
nothing shipped except the record.

### What was measured

The golden-master report, rendered from the same fixture with each change in isolation:

| Change | Pages | Sparsest interior page |
|---|---|---|
| unchanged | 5 | 199 chars |
| widow/orphan control alone | 5 | 199 chars — **no effect** |
| widow control + figure bound to its paragraph | **6** | **180 chars — worse** |

`KeepTogether` cannot make a pair fit. When the paragraph-plus-figure does not fit the remaining
space it moves the *whole pair* to a fresh page, which lengthens the document and leaves the
previous page shorter still. That is the opposite of the intent.

The widow theory was also wrong. The three words beside the chart ("on inspection.") looked like a
classic widow; `allowWidows=0` changed nothing, because it is not a broken-off line — it is the
genuine end of the section's last paragraph.

### What the three attempts add up to

1. Narrow the figure → no effect.
2. Widow/orphan control → no effect.
3. Bind figure to paragraph → measurably worse.

**The diagnosis has changed.** This is not a typesetting problem. The VALUE section's prose is
short, and a short section followed by a full-width chart produces a thin page under *any* keep-with
rule. It is a content-length problem wearing a typesetting costume.

### What would actually fix it

One of three, none of them a layout change:

- a **shorter figure** for the value build-up (half-height rather than full-width),
- a **denser VALUE section** — the prose is the shortest of the six, which is arguably its own
  problem given it is the section a client reads for the number,
- or **accept the page**: a chart with a caption and a short lead-in is not a defect, and three
  attempts suggest the cost of removing it exceeds the cost of having it.

My recommendation is the third, with the second raised separately as a content question for
GRS-0211. Scope 4's regression guard (no *blank* interior page) stands and is unaffected.

**The scope stays open, now with a bounded answer rather than an untried idea.**