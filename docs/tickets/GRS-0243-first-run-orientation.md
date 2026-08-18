# GRS-0243 — First-run orientation: every section says what it is for, and the home page finally gets reworded

**Status:** PARTIAL — scope 1 shipped; 2-5 open (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-31, founder: "I have tried to use each section of the studio … and._
none of it makes sense. Not in my account or the demo account.").
**Priority:** HIGH. **Loop:** first-time-user coherence. **Relates to:** GRS-0175, GRS-0205, GRS-0208.

## Why

Three feedback rounds have now said the same thing in different words: a competent first-time user
cannot orient. Specifics verified 31/07/2026:

- **The home hero is still the exact sentence the founder flagged on 26/07** — "Your home for the
  Bruntsfield Advisory Network — manage your pipeline, run Platform Power assessments, generate
  client deliverables, and grow in the Workbench." — verbatim, plus the also-flagged "New to
  Platform Power? Start with the primer" banner. GRS-0174 swept copy and GRS-0205 is planned, but
  the two sentences the founder actually quoted survived both. That must not survive a third round.
- **Home is static.** Five cards that are links, no live state — no "you have 1 draft assessment",
  no "2 deliverables awaiting prose", no recent activity. A returning user gets nothing to resume.
- **Jargon precedes definition everywhere:** B · P · L · V on the home banner, "diagnostic packs,
  heatmaps", "bench queue", "kanban stages" — all before any surface has explained a term.
  Navigation says **Portfolio** while the page and URL say **assessments** and the card says
  "PORTFOLIO · THE PLATFORM POWER WIZARD" — three names for one thing on the first screen.
- **Section empty states do not teach.** Deliverables in a fresh account is a near-empty table with
  no "deliverables are generated from a finalised assessment — run one first, or open a demo
  example"; Engagements is a bare list; the wizard assumes the Guide has been read.

This ticket is the orientation layer. It does not restructure accounts (GRS-0208) or rewrite every
string (GRS-0205); it makes each section teach itself at the moment of first contact.

## Scope

1. **Reword the flagged copy, this time actually.** New hero and primer-banner copy written to the
   voice guide, reviewed against the founder's two quoted sentences as a checklist item in the PR.
   Add both old sentences to the copy-register lint (GRS-0205's mechanism) so they cannot return.
2. **One name per concept.** Decide Portfolio vs Assessments (recommendation: "Portfolio"
   everywhere, `/portfolio` route with redirect from `/assessments`), and align nav, card, page
   title and breadcrumbs. Same pass for "Learning & Drills" vs Academy (founder already asked for
   "just the Academy" on 23/07 — rename the tab).
3. **Home shows state.** Each card carries its live one-liner: drafts in progress, deliverables
   awaiting prose, next Workbench action, stale pipeline cards — the counts all exist behind the
   Bench and section pages already. Empty states on the cards say what would put a number there.
4. **Section empty states teach.** Every section's zero/thin state explains in two sentences what
   the section is for, where its contents come from, and the one action to take — with the demo
   examples (GRS-0236) linked where they exist. Deliverables' empty state names the actual chain:
   assessment → finalise → engagement → deliverable → report.
5. **A ten-minute first-run path.** A dismissible, resumable checklist for a new advisor: read the
   primer's three-lens section → open the demo report example → step through one demo assessment's
   Summary → find your commission schedule. Four links, state persisted, gone when done. Not a
   modal tour; a checklist card on home.

## Test plan

1. Copy-register lint: both flagged sentences banned; new copy present; jargon-before-definition
   sweep on the home page (B·P·L·V only with the primer link adjacent).
2. Vitest: home cards render live counts from their endpoints; empty states render the teaching
   copy; checklist persists dismissal and completion.
3. Route test: old path redirects, nav/breadcrumb/title agree on the chosen name.
4. Manual: fresh-account walkthrough screenshots (home, each section's empty state), in the PR.
5. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- Demo tenancy and act-as (GRS-0208).
- The full string sweep (GRS-0205) — this ticket owns the flagged sentences, names and empty
  states only.
- Guide content (GRS-0244).

## Acceptance

The founder logs into a fresh account, and within ten minutes — without opening the Guide — has
seen a finished example report, knows what each nav item is for, and knows the one thing each
section wants them to do next. And the sentence they complained about twice is gone.

---

## Status reconciliation — 2026-08-01

**PARTIAL.** Read this section before assuming the ticket is closed — three of its five scopes are
still open, and the ticket stays open with them.

## What shipped

**Scope 1 — the flagged copy, and the mechanism that keeps it flagged.** Both sentences the founder
quoted are rewritten. The hero no longer reads the navigation back to the reader; the primer banner
states what reading it changes instead of asking a question whose answer is yes for everyone.

The part that matters more than the rewrite: `frontend/lib/retiredCopy.ts` is a register of retired
wording with the **reason** each was rejected, and `retiredCopy.test.ts` scans the app source and
fails the build if any returns. Rewriting copy is easy; *keeping* it rewritten is what failed twice,
because a sentence carries no record of having been objected to. The test was verified to fail by
putting the old hero back — a register that cannot fail is decoration.

**Scope 2 — one name per concept, partly.** "Learning & Drills" is now **Academy**, which the
founder asked for on 23/07. The home card's kicker no longer introduces a third spelling of
Portfolio on the first screen.

**The route rename was considered and NOT done, deliberately.** The ticket recommends `/portfolio`
with a redirect from `/assessments`. The wizard's deep links live at `/assessments/<id>`, so
renaming only the list route would leave the list at `/portfolio` and every record under
`/assessments/…` — which is a worse inconsistency than the one being fixed, and a bigger one to
unpick later. Every user-visible name is now "Portfolio"; the URL is the one place the old word
survives, and it is the place a first-time user is least likely to read. Renaming the whole
hierarchy is a real change and deserves its own ticket rather than being smuggled into this one.

**Scope 4 — the deliverables empty state, which the ticket named specifically.** It now teaches the
chain: *assessment → finalise → engagement → deliverable → client report*, says why the page stays
empty until an assessment is finalised and attached, and offers both ways forward — start one, or
read a worked example (GRS-0236). Tested against the real page rather than a copy of its markup.

## What is NOT built

- **Scope 3 — home shows live state.** The five cards are still static links. No draft counts, no
  "awaiting prose", no recent activity, no empty-state one-liners on the cards.
- **Scope 5 — the ten-minute first-run checklist.** Not started. Needs a persisted, resumable,
  dismissible state and four linked destinations.
- **Scope 4, the rest.** Only Deliverables was rewritten. Engagements, Pipeline, Portfolio and the
  Workbench still have their original thin or bare empty states.

Those three are the larger half of this ticket and they are genuinely unbuilt. The ticket stays
open.
