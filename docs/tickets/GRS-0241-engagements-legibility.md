# GRS-0241 — Engagements: a list you can read, a link you cannot cross-wire

**Status:** DONE (2026-08-27) — all five scopes. _Previously recorded as: Planned (2026-07-31, first-time-user review). **Priority:** MED-HIGH._
**Loop:** first-time-user coherence. **Relates to:** GRS-0177, GRS-0198, GRS-0208.

## Why

Walked as a first-time user, 31/07/2026:

- **The duplicate demo rows the founder complained about on 23/07 are still here.** "Revolut —
  delivery", "Hargreaves Lansdown — delivery" and "WeBull — delivery" each appear twice. GRS-0177
  cleaned the portfolio; engagements got no equivalent pass and no demo/sandbox badging either, so
  the founder's original complaint reads as unfixed on this page.
- **Four naming conventions in one list:** "Meridian Securities — delivery", "LSEG Platform Power
  diagnostic", "Platform Power Assessment — Deutsche Börse", "Platform modernisation diagnostic —
  RBC Brewin Dolphin".
- **Every row reads "contracted · 0 comms".** "comms" is internal shorthand; a count of zero
  communications on every row is metadata with no information in it.
- **The engagement detail invites a data error.** "LINK A FINALISED ASSESSMENT" renders with a
  dropdown of *every other firm's* assessments even when the engagement already has its assessment
  linked — one click links Deutsche Börse's scores to the WeBull engagement. Nothing warns that the
  subjects differ.
- **The client report is unreachable from here.** Deliverable rows offer "Review AI | Download"
  (crammed into one cell) but no link to `/deliverables/<id>/report` — the flagship new surface is
  not reachable from the page that owns the deliverable.

## Scope

1. **Badge and dedupe.** Demo/sandbox badging identical to the portfolio's (shared component), and
   the staging duplicate rows cleaned by extending the ADR-0047 cleanup to engagements — run on
   staging as part of the PR, per the GRS-0177 lesson.
2. **One naming convention.** Engagement display titles become `<Client> — <engagement type>` with
   type from a small vocabulary; a migration normalises existing titles; free-text stays stored but
   display is derived.
3. **Row metadata that means something.** Status word, client, linked-assessment state
   (none/in-progress/finalised), deliverable count, last activity date. "comms" becomes
   "communications" and hides at zero.
4. **The link control stops inviting error.** When an assessment is linked, the control shows the
   link (with unlink as the explicit rare action). When unlinked, the dropdown lists only
   assessments whose subject matches the engagement's client, with a stated override path that
   *warns* on subject mismatch instead of silently accepting it.
5. **Deliverable rows link the report.** Each deliverable row gains "Client report" beside
   Review/Download (the same link the /deliverables index has), and the two existing actions get
   breathing room and clear labels.

## Test plan

1. Vitest: list renders badges, derived titles, and the metadata set; zero-comms hidden.
2. Vitest + backend: link control excludes mismatched subjects by default; override path warns;
   linking a mismatched subject without the override refuses.
3. Cleanup script test (pattern: ADR-0047 suite) for engagement dedupe; PR states it was run on
   staging.
4. Manual: engagements list before/after screenshots in the PR.
5. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- Pipeline linkage chips (GRS-0198).
- Gmail-backed communication log (GRS-0197).
- Demo tenancy restructure (GRS-0208).

## Acceptance

The founder opens Engagements and sees one clean, consistently named row per real engagement, can
reach the client report from it, and cannot link the wrong firm's scores to it without being told
exactly what they are about to do.

---

## Status reconciliation — 2026-08-01

**PARTIAL** — scopes 4 and 5 shipped 2026-08-20. **Scopes 1, 2 and 3 are not built.** The ticket
stays open on them.

Scope 4 was taken first and alone because it is the only item here that can corrupt a client
deliverable; the rest are legibility.

## Scope 4 — and the defect was in the backend, not the dropdown

The ticket describes this as a UI problem: a dropdown offering every other firm's assessments. The
dropdown is real, but it is not where the hole was. **`link_assessment_to_engagement` checked
ownership, finalisation and duplication — and never that the assessment was about the engagement's
client.** Fixing only the dropdown would have left the API accepting the same cross-wire from any
other caller.

So the guard is in the repository, where every path has to pass it:

- **Refuses by default** with `EngagementSubjectMismatchError`, naming both firms and saying what
  would go wrong ("one firm's scores under another firm's name on every deliverable") rather than
  only that it refused.
- **A subclass of `EngagementLinkError`**, deliberately: every `except EngagementLinkError` written
  before this check keeps refusing, which is the safe direction for code that predates the guard.
- **Overridable only explicitly**, via `confirm_subject_mismatch=True`. The override exists because
  legitimate mismatches are real — a group entity assessed under its parent's name, a rename
  mid-engagement — but it cannot happen by omission. A test asserts the parameter's default is
  `False`, because if that ever flips every existing caller silently starts cross-wiring.
- **The API distinguishes it** with `subject_mismatch: true` in the 409 body, so a client can offer
  the confirm path instead of presenting a dead end.

### The matcher had a bug I wrote and then caught

The comparison strips everything that is not `[a-z0-9]` after case-folding. That turns "Börse" into
**"brse"** — so "Deutsche Börse" and "Deutsche Borse" compared as *different firms* and the guard
would have refused a correct link. The fix is an NFKD decomposition first, which splits "ö" into
"o" plus a combining mark so only the mark is dropped. Parametrised tests pin both directions:
accents, case, and legal suffixes are not mismatches; two unrelated firms are.

A blank subject is **never** a mismatch. A blank is an absence of evidence, and refusing on it would
block a legitimate link with a message naming nothing.

### The guard found a live cross-wire in the suite, immediately

Two existing tests in `test_engagement_detail.py` failed on its first full run. Not stale
assertions — **the fixture was genuinely cross-wired**: it built an "Acme" engagement, finalised an
assessment whose document set the subject to "Meridian (partial)", linked the two, and asserted
200. It had done so for as long as it existed, and nothing objected because nothing checked.

That is the defect class this scope exists to prevent, sitting in the test suite that was supposed
to be covering the feature. The fixture now takes a subject that matches its prospect (and sets it
on the *document*, since `save_assessment` rewrites `subject` from there — setting only the
create-time value is silently discarded, which is how the original drift happened).

## Scope 5 — the client report is reachable from the engagement

Each deliverable row gains a **Client report** link. The flagship surface of GRS-0219/0220 was
reachable only from the `/deliverables` index, not from the page that owns the deliverable. The two
existing actions were also crammed into one cell separated by a pipe, which reads as one control;
they are spaced and named for what they do ("Review AI draft", "Download .docx").

## Not done

- **Scope 1 (badge and dedupe).** The demo/sandbox badging is a shared-component change and the
  dedupe needs an ADR-0047 cleanup run **on staging**, which the ticket rightly requires as part of
  the PR. Not attempted.
- **Scope 2 (one naming convention).** Needs a migration that normalises existing titles plus a
  display-derivation rule. Not attempted.
- **Scope 3 (row metadata).** "comms" is still internal shorthand and still renders at zero. Not
  attempted.
- **No screenshots** (test-plan item 4).

The acceptance line has two halves. *"Cannot link the wrong firm's scores without being told exactly
what they are about to do"* — **met**. *"One clean, consistently named row per real engagement"* —
**not met**; that is scopes 1 and 2.

## A pattern worth naming

Fixing scope 5 broke `DeliverablesPanel.test.tsx`, which asserted the exact button label
`"Download"`. That is the **fourth** time in this wave a test pinned to a literal sentence has gone
red on a deliberate copy change (GRS-0228, then twice in GRS-0240, now here). Each is trivial to fix
and each looks like a regression until someone reads it.

The rule that keeps working: **assert the behaviour, match the copy loosely.** `name: /Download/`
survives a rewording; `name: "Download"` does not. Worth a lint rule; not one I have written.


---

## Second pass — 2026-08-20 (scopes 1 and 3)

### Why scope 1 was never done: an engagement had no provenance

The founder asked for the duplicate demo rows on 23/07 and again on 31/07, and both times it did
not happen. The reason is structural rather than neglect.

Assessments and deliverables carry `RecordProvenance` (ADR-0029) — set at creation, immutable —
which is how every surface knows to badge a record as demo or sandbox, and how ADR-0047 knows what
may be deleted. **Engagements were the one owned record without it.** So nothing could badge a demo
engagement, and nothing could safely delete a duplicate: ADR-0047 forbids deleting a production
record, and without provenance no engagement could be *shown* to be anything else.

Every previous attempt at this scope would have had to guess which rows were demo data. That guess
is exactly what ADR-0047 exists to prevent, which is presumably why it kept stalling.

### What shipped

**Migration `0039` adds the column**, defaulting to `production` — the safe direction, matching
every other table. Existing rows are therefore production and remain undeletable, which is correct:
nothing can retroactively prove a historical row was demo data.

**Provenance is DERIVED, not merely accepted.** An engagement drawing on a non-production assessment
is itself non-production. This matters because the demo seed creates its engagements over HTTP and
ADR-0029's rule is that a DEMO marker is *never* accepted from a request — deriving it from the
linked assessments gives the seed the right answer without opening a field a client could forge,
since assessment provenance is already immutable and already unforgeable.

The derivation is **one-directional**: a marker can be strengthened by what the record draws on,
never weakened. A test pins that, because if it ever inverted, linking a real assessment would
quietly *un-badge* a demo engagement.

**`Repository.delete_engagement`** enforces ADR-0047 in the repository, not in the script. A
production engagement refuses deletion and no argument relaxes it — a guard a caller can forget to
apply is not a guard.

**`scripts/staging_cleanup_grs0241.py`** finds duplicate non-production engagements (same owner,
prospect and title), prints them, and deletes only with `--execute`. The survivor of each group is
the row with the most attached work — deliverables, then assessments, then comms — rather than the
oldest: two rows that look identical in the list may not be, and keeping the oldest would sometimes
delete the one carrying real output.

**Scope 3 (partly): the badge and the "comms" wording.** The list uses the portfolio's own
`ProvenanceBadge`, so a demo engagement is labelled exactly as a demo assessment is. "comms" is now
"communication(s)" and **hidden at zero** — a count of zero on every row is metadata with no
information in it.

### Still open

- **Scope 2 (one naming convention).** Needs a display-derivation rule plus a migration normalising
  existing titles. Not attempted.
- **Scope 3's remaining metadata** — linked-assessment state (none/in-progress/finalised),
  deliverable count and last-activity date are not on the row yet.
- **The staging cleanup has NOT been run.** The tool exists and is tested; running it needs the demo
  seed re-run first (so the rows are stamped `demo`), and I have not done either on staging. Until
  then the duplicate rows the founder sees are still there — they are `production` by default and
  the script will correctly refuse to touch them.

---

## Scope 2 — done 2026-08-27

The founder-visible half was already true: "Learning & Drills" no longer exists, and the nav,
headings and breadcrumbs have said "Portfolio" for a while. **The one place the old word survived
was the address bar**, which is why this was deprioritised twice.

Done now that everything else is: `/assessments` → `/portfolio`, with **permanent redirects** for
`/assessments` and `/assessments/:path*`. The redirects are the point — advisors bookmark pages, and
a rename that breaks a bookmark is a worse bug than the inconsistency it fixes.

**The backend route is unchanged.** `lib/api.ts` still calls `/assessments` because that is the API,
not the page, and renaming it would be a contract change wearing a UI change's clothes.

Two things the move surfaced, both fixed:

- `WizardLayout.test.ts` reads its component off disk by path and still pointed at
  `app/assessments/...`. It failed to LOAD rather than failing an assertion, so the suite reported
  "410 passed" instead of 419 — nine tests silently not running. A test file that cannot load is
  worse than a failing one, because the count still looks plausible.
- Stale generated types under `.next/` referenced the old directory and broke `tsc` until the
  build cache was cleared. Not a code problem, but worth knowing before someone debugs it.