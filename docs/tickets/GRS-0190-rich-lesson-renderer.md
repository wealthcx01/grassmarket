# GRS-0190 — Rich lesson renderer + content contracts

**Status:** Planned (2026-07-23, founder feedback items 20/21). **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 4. Carries ADR-0043 (in-house build — founder
decision 23/07: no external LMS).

## Why

Academy lessons render as plain paragraphs with `**bold**` only — no markdown engine, no video,
no links out, no assets. The `Lesson.video_ref` field exists in the contract and is unused by
every seeded course. This ticket builds the rendering and contract capacity that the content
depth program (GRS-0191) fills.

## Scope

1. **Contract** (`packages/bcap_contracts/src/bcap_contracts/learning.py`):
   - `SourceRefKind(StrEnum)`: `DOCS = "docs"`, `VIDEO = "video"`, `BLOG = "blog"`,
     `REPO = "repo"`.
   - `SourceRef(BaseModel, frozen, extra="forbid")`: `title: str = Field(min_length=1)`,
     `url: str = Field(pattern=r"^https://")` (https enforced at the contract — schema
     validation refuses `http://` and non-URL strings), `kind: SourceRefKind`.
   - `LessonAsset(BaseModel, frozen, extra="forbid")`: `caption: str = Field(min_length=1)`,
     `alt: str = Field(min_length=1)`, `svg: str = Field(min_length=1)`. Decision: assets are
     inline SVG strings inside the content data, not files — the published `CourseVersion`
     snapshot stays fully self-contained and immutable, and no asset storage/pipeline is
     introduced. Raster images are out of contract; a photo belongs behind a `SourceRef`.
   - `Lesson` gains `references: tuple[SourceRef, ...] = ()` and
     `assets: tuple[LessonAsset, ...] = ()`.
   - JSON schemas regenerated under `packages/bcap_contracts/.../json_schema/`; TS mirror in
     `frontend/lib/types.ts` gains `SourceRefKind`, `SourceRef`, `LessonAsset`, and the two new
     `Lesson` fields. No migration: lessons persist inside `CourseTree` JSON, so the DB schema
     is unchanged.

2. **Markdown renderer** (new `frontend/lib/markdown.tsx`): a hand-written parser for a
   sanctioned subset, building React elements directly — no `dangerouslySetInnerHTML`, no new
   dependency. Decision: in-house subset over a markdown library because the injection surface
   must be zero and the subset is small. Supported: `#`/`##`/`###` headings (rendered h3–h5
   inside the lesson card), paragraphs, `**bold**`, `*italic*`, `` `inline code` ``, fenced
   code blocks, ordered/unordered lists (one nesting level), GFM pipe tables, and links
   `[text](https://…)`. Rules: link URLs must start `https://` (anything else renders as plain
   text); raw HTML tags render as literal text; images via markdown syntax are not supported
   (assets are the image mechanism). External links render with `target="_blank"`,
   `rel="noopener noreferrer"`, and a visible external-link marker.

3. **SVG sanitiser** (new `frontend/lib/svg.ts`): `sanitizeSvg(svg: string): string | null`
   allowlisting SVG structural/shape/text elements and presentation attributes; strips
   `<script>`, `<foreignObject>`, `<use>` with external href, event-handler attributes
   (`on*`), and any `href`/`xlink:href` that is not a fragment. Returns `null` (renderer shows
   a loud "asset failed sanitisation" note, never silently drops) on disallowed content.
   Assets render via an inline `<svg>` produced from the sanitised string.

4. **Lesson body component** (new `frontend/components/workbench/LessonBody.tsx`): composes
   the markdown renderer, a `video_ref` embed, reference link cards, and assets. `video_ref`
   handling: a YouTube URL or bare 11-char ID renders a `youtube-nocookie.com` iframe
   (privacy-enhanced, lazy-loaded); any other https URL renders as a video link card, not an
   embed (decision: only YouTube is embeddable — every current source is YouTube and iframing
   arbitrary origins is not acceptable). References render as link cards (title, kind badge,
   host) via new `frontend/components/workbench/LessonReferences.tsx`.

5. **Reader + authoring integration.** `frontend/app/workbench/academy/[slug]/page.tsx`:
   `Body`/`inline` (lines ~17–41) are replaced by `LessonBody`; completion flow, the
   active-recall check gate, progress bar, and course-complete section are unchanged.
   `frontend/app/workbench/courses/[slug]` (authoring): the lesson preview renders through the
   same `LessonBody` component so author preview and learner view are pixel-identical; the
   draft editor gains fields for `video_ref`, references (title/url/kind rows), and assets
   (caption/alt/svg textarea).

6. **Backend:** no endpoint changes. `PUT /workbench/courses/{slug}/draft` already validates
   the tree through the contract, so malformed references/assets are refused 422 by existing
   machinery. Publishing, lesson approval (ADR-0009), completion, and certification credit
   wiring are untouched.

## Test plan

Backend (pytest):
- `tests/test_academy_courses.py` additions: a draft containing markdown structure, a
  `video_ref`, three references, and one SVG asset round-trips through save → publish →
  published fetch; `url: "http://…"` → 422; unknown `kind` → 422; empty `svg` → 422; existing
  seeded courses (plain text, no new fields) still publish and serve unchanged.
- `tests/test_contract_invariants.py`: regenerated schemas include the new models; schema
  drift check green.

Frontend (vitest, per-file):
- `frontend/lib/markdown.test.tsx`: headings, lists, tables, links, code render; `<script>`
  and inline HTML render as literal text (no element injected); `javascript:` and `http://`
  link URLs render as plain text; bold/italic nesting.
- `frontend/lib/svg.test.ts`: strips `script`/`onload`/`foreignObject`/external `href`;
  passes a clean diagram; returns null on disallowed content.
- `frontend/components/workbench/LessonBody.test.tsx`: YouTube URL and bare ID produce a
  `youtube-nocookie` iframe; non-YouTube video_ref produces a link card; references render as
  cards with external marker; sanitised asset renders with caption and alt.
- `frontend/app/workbench/academy/[slug]/page.test.tsx`: updated — an existing plain-text
  lesson renders the same paragraphs as before; check-question gate still gates completion.

## Out of scope

- Authoring any new course content (GRS-0191).
- Source freshness watching (GRS-0192).
- Raster image assets, file uploads, or an asset store.
- Any change to publishing/approval flow, completion semantics, drill topics, or
  certification credits.

## Acceptance

- A lesson authored with markdown structure, a YouTube video, three reference links, and one
  SVG diagram renders correctly and identically in learner and authoring views (test-covered).
- Every existing seeded lesson renders unchanged (regression test).
- Contract validation refuses non-https reference URLs, unknown kinds, and empty assets (422).
- No `dangerouslySetInnerHTML` and no new runtime dependency is introduced; the sanitiser
  strips scripted SVG (test-covered).
- JSON schemas and the TS mirror are regenerated in the same PR.
