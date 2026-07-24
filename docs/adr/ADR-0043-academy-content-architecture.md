# ADR-0043 — Academy content architecture: rich in-house content, no external LMS

- **Status:** Proposed (2026-07-23). Founder decision 23/07/2026 (feedback items 20/21/25;
  build-in-house chosen over Canvas/Moodle/headless-CMS); ratifies with GRS-0190.
- **Deciders:** Founder (build vs adopt), Engineering (architecture).
- **Normative source:** ADR-0028 (Academy programme), ADR-0009 (AI content approval),
  ESTATE-RECONCILIATION policy (partner material never committed).

## Context

The Academy's machinery is sound — versioned courses, approval-gated publishing, active-recall
checks, certification credits — but its content capacity is a plain-paragraph renderer and its
content depth a fraction of what serious enterprise B2B training requires. The founder
considered adopting an open-source LMS (Canvas, Moodle, Academy LMS). Evaluation: both are
separate applications (Rails/PHP) with their own auth, UX, and hosting — a second system that
breaks the single-Studio experience and adds permanent operational burden for features
(SCORM, cohorts) the network does not need. Decision: build in-house.

## Decision

1. **The lesson is a rich document:** markdown body (sanitised subset), rendered video
   (`video_ref`, at last used), per-lesson **source references** (docs/video/blog/repo link
   cards), and shipped visual assets. Contracts extended accordingly (GRS-0190).
2. **Content is data, authored from sources, cited per lesson.** Courses are rebuilt to real
   depth from the operator's source material (GRS-0191); commission figures stay live-from-
   config; partner-confidential text stays out of the repo.
3. **Freshness is watched, not assumed:** per-course source watchlists with hash-compare
   flagging feed a stale-lesson authoring queue (GRS-0192).
4. **The existing spine is retained unchanged:** draft → approve → publish versioning, the
   active-recall completion gate, drill topics, and certification credit wiring.

## Consequences

- One studio, one login, one design system; no second application to run.
- Content quality becomes a reviewable, versioned artefact — the founder signs off per course.
- The cost accepted: features an LMS would give free (cohort management, SCORM import) are out
  of scope until a real need appears.
