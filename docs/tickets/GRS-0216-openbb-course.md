# GRS-0216 — The OpenBB course, built to the founder's standard

**Status:** In review (2026-07-30, PR #220 — 196 slides, eight sections, and since GRS-0226
an advisor can actually read them). **Priority:** HIGHEST.
**Loop:** founder-feedback remediation, Wave 4. **Depends on:** GRS-0215 (course architecture),
GRS-0190 (renderer, shipped).

## Why

The founder named this course as the worked standard, so it gets its own ticket rather than a line
in a batch:

> "by the end of the OpenBB course an advisor should have been able to download, sign up to
> OpenBB, create their own workspaces (multiple) and know exactly how and when to sell it."

They also said they expected **1000x** the current depth for OpenBB specifically. The course today
is a handful of paragraphs. It is the deepest product in the catalogue and the thinnest course.

If this course is not something the founder would put in front of a paying advisor, the rest of the
Academy plan is not worth building.

## Scope

Built on the section-and-slide structure GRS-0215 defines. Eight sections. Each lesson inside them is 20 to 40 slides;
each section ends in a test the learner passes before the next opens.

1. **What OpenBB is and why it exists.** The problem it solves, who built it, where it sits against
   Bloomberg, Refinitiv and the retail tools. The commercial shape: open source core, Terminal Pro,
   Enterprise. Sourced from OpenBB's own docs and posts, cited per slide.
2. **Install it.** The advisor installs OpenBB and gets to a working environment. Real steps, real
   screenshots, the failure modes they will actually hit. Checkpoint: a screenshot of their own
   running install.
3. **Sign up and get oriented.** Account, workspace concepts, data connections. Checkpoint: account
   created.
4. **Build your first workspace.** A guided build for one concrete use case, end to end. Checkpoint:
   their own workspace, saved.
5. **Build a second, different workspace.** A different use case so the advisor generalises rather
   than copies. The founder asked for "workspaces (multiple)" for this reason.
6. **The data.** What OpenBB gives you, what it does not, what the licensing implications are for a
   client. This is where an advisor gets caught out in front of a prospect.
7. **Who buys it and why.** The segments, the buying centre, the triggers. Mapped to our own
   `RegistryTarget` segments so the advisor can go from lesson to pipeline.
8. **How and when to sell it.** Qualification, the pitch, the objections they will hear and the
   answers, the pricing conversation, what a good first meeting looks like. Ends in a practice
   scenario, not a quiz.

**Assets.** Diagrams and slide visuals in the Bruntsfield design system. A downloadable deck the
advisor can take to a client. Where OpenBB has published video, the lesson embeds it at the right
timestamp rather than linking to the channel.

**Every lesson carries at least one `SourceRef`** (the field GRS-0190 added). If a claim has no
source, it does not go in the course.

## Test plan

1. The GRS-0215 content-depth tests, run against this course: slide counts per lesson, a test at
   the end of every section, at least one `SourceRef` per lesson, minimum lesson length.
2. Link integrity at build time for every doc, blog and video link.
3. Progression: section N+1 locked until section N's test is passed.
4. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- The other product courses (GRS-0217) and Sales Egoist (GRS-0218).
- The renderer (GRS-0190, shipped).
- Certification rules.

## Acceptance

The founder takes the course end to end and finishes with OpenBB installed, two workspaces built,
and a clear view of how and when to sell it. Not a summary of OpenBB. The thing itself.
