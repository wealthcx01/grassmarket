# GRS-0229 — measuring the missing non-production mark

**Date:** 2026-08-01 · **Branch:** `grs-0229-web-report-nonproduction-mark`

## What was measured, before anything was changed

`SharedReportPayload` — the snapshot the public page is served from — had exactly three fields:

```python
report: ClientReport
figures: dict[str, dict[str, list]]
tracking_notice: str
```

There was no mark on the page because **there was nothing on the page to render a mark from**. The
provenance never reached the web rendition at all: it was neither stored in the snapshot at issue
nor derivable from it at read time.

## Scope 4 — why the gap existed

The ticket asks whether GRS-0220's planned test was never written, or written and asserting the
wrong thing. **It was never written.** There is no test anywhere in the repository — backend or
frontend — that mentions a watermark, a non-production mark, or a draft mark on the shared page.
`grep` over `tests/test_report_links.py`, `tests/test_client_report_wiring.py` and
`frontend/components/SharedReport.test.tsx` for `non_production|watermark|NON-PRODUCTION` returned
nothing.

The *reason* it was missed is more interesting than the omission, and it is a design trap worth
recording. `SharedReportPayload`'s own docstring says:

> The SAME content model the PDF consumes (GRS-0219), so the two renditions cannot tell a client
> different things — the parity the ticket asks for is structural, not a convention.

That was true, and it was insufficient. **The watermark is not part of the content model.** In the
PDF it lives in `ReportMeta`, a render-time parameter passed *alongside* `ClientReport`, not inside
it. So a parity check on the content model passed with flying colours while the one thing that is
not in the content model — the mark — was absent from one rendition. Structural parity on the wrong
structure.

## A defect the ticket did not anticipate: the PDF is not correct today either

The ticket lists "the PDF watermark (GRS-0219, correct today)" as out of scope. It is correct for
the case it was tested on and wrong for a case that now exists.

`client_report.py` derived the mark as:

```python
non_production=deliverable.mode is not DeliverableMode.CLIENT
```

`DeliverableMode` comes from `resolve_mode(coefficients, client_facing=...)` — that is, from the
**coefficient set's `client_usable` flag**, not from the record's provenance. When GRS-0219 shipped,
every profile scored on the draft set (`client_usable=False`), so every deliverable was
`DRAFT_INTERNAL` and the derivation happened to be right.

Wealth and exchange have since been activated (ADR-0037/GRS-0156) with
`elicited_coefficients.py: client_usable=True`. So today a **SANDBOX record on an activated
profile, generated client-facing, resolves to `mode=CLIENT`** — and the PDF renders **no
non-production mark at all**. The exact failure GRS-0219 called "the worst failure this document can
have", on the rendition the ticket assumed was safe.

Both renditions are now keyed on `RecordProvenance`, which is set at creation and immutable, with
mode kept as an `or` so a draft-internal production record still carries its draft mark.

## Scope 3 — should a non-production record be able to issue a link at all?

**Decision: allowed, and watermarked.** Two reasons.

An advisor needs to see what a client sees, and the share link is the only rendition that shows it —
the PDF is a different medium and the in-app preview is a different layout. Refusing links on
sandbox records would remove the only way to check the client experience before a real client is on
the other end, which pushes the first real test onto a real client.

Second, refusal is a weaker guarantee than marking. If links were refused on non-production records,
the mark would still be the thing standing between a demo report and a reader for every *other*
path, and it would be less well tested for being rarely exercised. Marking is the guarantee; refusal
would be a second mechanism that makes the first one look optional.

## The evidence

Captured against a locally seeded record (`Meridian Securities`, production provenance,
`draft_internal` mode — so the draft mark applies and the non-production one does not).

| Screenshot | Viewport | Scroll | Mark visible |
|---|---|---|---|
| `desktop-top.png` | 1280×900 | top | yes |
| `desktop-scrolled.png` | 1280×900 | 1400px | **yes** |
| `phone-top.png` | 390×844 | top | yes |
| `phone-scrolled.png` | 390×844 | 1400px | **yes** |

The mid-scroll shots are the ones that matter: the acceptance is that a reader "cannot read a single
screen without knowing the numbers are not production", and a banner in the page header fails that
from the second screen onwards. The mark is `position: fixed`, so it is on screen at every scroll
position, and the shell reserves matching padding so it never covers the first heading — visible on
the phone shot, where the banner wraps to two lines and the title still clears it.

## Why the default is "show the mark"

Both new fields default to `True` on the contract, and the component treats an absent flag the same
way. A link issued before this change has neither flag in its stored JSON, and a snapshot whose
provenance nobody recorded is precisely the case where a reader should be told the numbers may not
be production. Defaulting to `False` would have let every pre-existing link render a clean, unmarked
page — silently, and only for the records nobody could check.
