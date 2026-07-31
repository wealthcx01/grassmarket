# GRS-0226 — The slide reader and the section gate

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: In review (2026-07-30, PR #220). **Priority:** HIGHEST. **Loop:** founder-feedback._
remediation, Wave 4. **Depends on:** GRS-0215 (the slide + section-test contracts), GRS-0216 (the
196 slides), GRS-0225 (the nine diagrams).

## Why

GRS-0216 wrote 196 slides. GRS-0225 drew nine diagrams and put them on those slides. Both are
served by the API today, and **an advisor cannot see any of it**. The Academy reader renders
`lesson.body`, `lesson.video_ref`, `lesson.references` and `lesson.assets`; `slides` is not in
`frontend/lib/types.ts` at all, so the whole rebuild is data nobody can open.

GRS-0215 put the renderer out of scope on the grounds that GRS-0190 had built it. That was wrong,
and worth recording rather than quietly fixing: GRS-0190 built a rich renderer for a lesson whose
content was a markdown *body*. GRS-0215 then moved the content to *slides* and added a section
test, which are different shapes. The renderer that exists does not render either of them.

The same sentence applies to the gate. `SectionTest` and `SectionTestAttempt` are in the contracts
package with no table, no repository method, no route and no UI. GRS-0215's test plan item 3 — "a
section does not unlock until its predecessor's test is passed" — has never run against anything.

This is the ticket that turns three shipped tickets into something the founder can open. Under the
rule the programme now works to, none of them are shipped until it lands.

## Scope

1. **Contracts to TypeScript.** `Slide`, `SlideKind`, `SectionTest`, `TestQuestion`,
   `SectionTestAttempt` mirrored into `frontend/lib/types.ts`, and `slides` / `section_test` added
   to the `Lesson` and `CourseModule` interfaces they belong to.
2. **The slide reader.** A lesson with slides reads as slides: one at a time, ordered, with its
   kind visible, its markdown body, its diagram, and its own sources. `lesson.body` stays as the
   opening — what this lesson is for — which is what the contract says it now is. A lesson with no
   slides still renders exactly as it does today, because legacy courses have to stay readable.
3. **The slide asset.** Reuse GRS-0190's sanitising `Asset` renderer rather than write a second
   one. A diagram that fails sanitisation says so, loudly, in the slide's place.
4. **The section test.** The questions, one right answer, and the explanation shown after the
   learner answers — right or wrong, because this gate exists to teach rather than to filter.
5. **The gate.** Section N+1 does not open until section N's test is passed. Recorded server-side,
   append-only, one row per attempt, owner-scoped: the record shows how many goes it took.
6. **Progress that means something.** Course progress counts passed sections, not scrolled
   lessons, per GRS-0215 scope item 6.

## What this ticket does NOT pretend

The published course tree carries `answer_index` and `explanation` to the browser, because the
learner reader downloads the whole tree. So a determined advisor can read the answers out of
devtools. Marking is still server-side — the attempt record is the auditable one, and the client
never asserts its own pass — but this is an internal training gate, not an invigilated exam, and
building answer-hiding into the publish path would be scope creep sold as rigour. Saying so here is
better than implying a secrecy the code does not provide.

## Two things found while building it

**A locked section could still be marked.** Hiding a section in the reader is not the same as
refusing it, and the first cut only did the hiding — a direct POST could record a pass on section 5
before section 1 was opened. Since scope item 5 calls the attempt record the auditable one, a row
describing a progression that never happened is worse than no row, so the rule now lives in
`record_section_test_attempt` as well as in the reader.

**The OpenBB tree numbered two sections the same.** The course is assembled from three sources —
the rebuilt sections, the canonical product module and the retained reference sections — and each
numbered itself from zero, so the product module and rebuilt section 1 both held `order` 0. The
unlock rule reads `order`, so the gate was reading a tie and opening section 2 to an advisor who
had passed nothing. Reading order is now applied once to the assembled tree, and `publish_course`
refuses any tree whose sections do not have distinct orders — a gate that fails open must be
impossible for any course, not just this one.

## Test plan

1. Repository: an attempt is scoped to its owner; another consultant cannot read it. Marking is
   computed from the published tree, never from the request body. An attempt against a section with
   no test, a locked section, or a course never published, is refused.
2. Progression: section 1 is always open; section N+1 opens only on a passed attempt at N.
3. Routes: pass, fail, retake (a second row, not an update), and a 404 for an unpublished course.
4. Frontend: a slides lesson renders slides and a legacy lesson still renders its body; a diagram
   that fails sanitisation is announced rather than dropped; a locked section does not show its
   lessons; the explanation appears after answering.
5. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- Writing course content (GRS-0216 to GRS-0218).
- The diagrams themselves (GRS-0225).
- A downloadable deck export (GRS-0215 scope item 4, still unbuilt).
- Answer-hiding at publish time, per the section above.

## Acceptance

The founder opens the OpenBB course, reads it as slides with the diagrams in place, sits the
section-1 test, and cannot reach section 2 until they pass it.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `d615dad` (GRS-0226: the slide reader and the section gate).

This ticket carried no *What shipped* record; the commits above are that record.
