# GRS-0215 — Rebuild the courses as courses, not paragraphs

**Status:** In review (2026-07-30, PR #220 — the reader landed in GRS-0226; a downloadable
deck export, scope item 4, is still unbuilt). **Priority:** HIGHEST.
**Loop:** founder-feedback remediation, Wave 4. **Replaces the content half of GRS-0191.**

**This ticket owns the course architecture and the depth standard.** The courses themselves are
split out so each is reviewable on its own: **GRS-0216** OpenBB (the worked standard the founder
named), **GRS-0217** the remaining product courses, **GRS-0218** Sales Egoist (blocked on source
material). This ticket ships the structure, the asset pipeline and the tests that make a thin
course fail the build.

## Why

This is the item the founder has now raised twice, in stronger terms the second time.

> "The courses are so basic?! ... You have written theses as 'lessons'. Last time i checked a
> paragraph is not a lesson. A lesson is 20-40 slides of interactive detail with a test before the
> next section."

They are right, and the reason is worth stating plainly. GRS-0190 built a rich lesson renderer:
markdown, video embeds, diagrams, source links. GRS-0191 was supposed to write the content and did
not. So the product gained the capacity to fix the complaint and none of the fix. The renderer is
not the deliverable. The content is.

The founder also gave a concrete standard, which is the only sensible acceptance criterion:

> "by the end of the OpenBB course an advisor should have been able to download, sign up to
> OpenBB, create their own workspaces (multiple) and know exactly how and when to sell it."

## Scope

1. **Course structure, per course.** Each product course is built as sections; a section is a group of
   lessons; each LESSON is 20 to 40 interactive slides; each section ends in a test the learner
   must pass before the next section opens. The founder's words were "a lesson is 20-40 slides of
   interactive detail with a test before the next section", and the unit matters: pitching it at
   the section rather than the lesson would have let a three-paragraph lesson through again. This is the shape GRS-0190's renderer already supports and nobody used.
2. **The depth tests, written here and run by every course ticket.** Minimum slides per LESSON, a test at the end of every section, at least one `SourceRef` per lesson, a minimum lesson length.
   These have to exist before the content tickets start, or "thin" stays a matter of opinion.
3. **The content sourcing rule**, applied by GRS-0216 to GRS-0218:
   - the product's own documentation, deep-linked per lesson rather than linked once at the top,
   - their YouTube material, embedded at the timestamp that matches the lesson,
   - their blog and release notes,
   - the strategy and catalogue material already committed under `data/gtm/sources/`.
   Every lesson carries at least one `SourceRef` (the field GRS-0190 added for exactly this).
4. **Generated assets.** Diagrams, slide visuals and a downloadable deck per course, produced with
   the design system rather than stock layouts. Rive is a candidate here for the interactive
   slides; see GRS-0206, and reuse its runtime if that spike says yes.
5. **Doing, not just reading.** OpenBB, as the worked standard: install it, sign up, build a first
   workspace, build a second for a different use case, then a section on qualifying and selling
   it, with the objections an advisor will actually hear. Each with a checkpoint the advisor
   completes rather than reads.
6. **Honest progress.** Course completion means passing the section tests, not scrolling to the
   end.

## On buying instead of building

The founder has asked twice whether we should import an open-source LMS, naming Canvas, Moodle and
Academy LMS. ADR-0043 said build in-house. That decision was made about the renderer, and the
renderer turned out not to be the hard part. The hard part is authoring depth, which no LMS
supplies.

So the ADR stands, but it is now recorded with the reason that actually applies: an LMS would not
have written these lessons either. If this ticket does not produce a course the founder considers
Coursera-grade, the LMS question is genuinely open and should be reopened rather than defended.

## Test plan

1. The content-depth tests themselves, proven against a deliberately thin fixture course that must
   fail them. That is the point of the ticket: "thin" becomes a build error, not an opinion.
2. Link integrity: every external link resolves at build time (the freshness watcher, GRS-0192,
   keeps them resolving afterwards).
3. Progression test: a section does not unlock until its predecessor's test is passed.
4. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- The renderer, which exists (GRS-0190).
- Writing any actual course (GRS-0216, GRS-0217, GRS-0218).
- Certification sign-off rules (unchanged).
- The freshness watcher (GRS-0192), which follows this.

## Acceptance

A course that does not meet the standard fails the build. The structure supports what GRS-0216 has
to deliver, and the founder's judgement of that course is the real verdict on this one.
