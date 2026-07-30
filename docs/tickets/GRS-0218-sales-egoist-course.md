# GRS-0218 — The Sales Egoist course

**Status:** Blocked on source material (2026-07-26; 23/07 item 20). **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 4. **Depends on:** GRS-0215.

## Why

The founder gave us a lot of material on the Sales Egoist and said, of what came back:

> "You have done nothing but generically summarize some of the content I gave you. I am beyond
> disappointed."

This is the methodology course, not a product course. It is what makes an advisor good at the job
rather than knowledgeable about one vendor, so it carries more weight than any single product
course and currently has the least behind it.

## Blocked, and on what exactly

The source material is **not in the repository**. Checked again on 2026-07-29 across all branches:
`data/reference/7powers-math-extraction.md` is present; the Sales Egoist teaser deck and the
7 Powers PDF are not. The 23/07 manifest records the deck as "OneDrive source, paraphrased, not
committed".

The founder has said they will add the Helmer and Sales Egoist materials. Until they land in
`data/`, this ticket cannot start, because writing it from the existing paraphrase would repeat
exactly the failure being complained about.

**Unblocking condition:** the Sales Egoist material committed under `data/reference/`.

## Scope, once unblocked

GRS-0215 structure: sections of lessons, each lesson 20 to 40 slides, a test between sections, sources cited per lesson.

1. **The idea itself**, from the source rather than from a summary of it. What the Sales Egoist
   framing claims, where it came from, and what it argues against.
2. **The method**, broken into the moves an advisor actually makes, with worked examples drawn
   from the segments we sell into rather than generic B2B examples.
3. **Applied to our work.** How the framing maps onto an ATLAS engagement: the first meeting, the
   assessment as a sales instrument, the deliverable as the close.
4. **Practice.** Scenarios the advisor plays through, connected to the Practice Arena rebuild
   (GRS-0196) rather than a quiz.
5. **Assets.** A deck the advisor can actually study from, in the design system.

## Test plan

1. The GRS-0215 content-depth tests.
2. Source-attribution test: every lesson carries a `SourceRef` pointing at committed material, so
   the "generic summary" failure is caught by the build rather than by the founder.
3. Progression gating per section.
4. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- Product courses (GRS-0216, GRS-0217).
- The Practice Arena rebuild itself (GRS-0196), which this course feeds.

## Acceptance

The founder reads the course and recognises the material they gave us, developed rather than
compressed.
