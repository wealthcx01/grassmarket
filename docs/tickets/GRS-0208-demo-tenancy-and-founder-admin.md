# GRS-0208 — One clean demo account, and a founder admin who can act as any advisor

**Status:** PARTIAL — scopes 1 and 2 shipped; 3 and 4 open (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-26, staging review item 6). **Priority:** HIGH._
**Loop:** founder-feedback remediation, Wave 1.

## Why

The founder cannot follow a single example client through the platform end to end, even from the
admin account. The example data is spread across six seeded advisors, each holding one assessment,
so no account shows a pipeline, an assessment, a deliverable and an earnings line that belong to
the same story. Admin sees everything and therefore shows nothing coherent.

They asked for two accounts with different jobs:

- a **demo account** holding all the example profiles, so a walkthrough is one login,
- **john@bruntsfield.capital** as an admin who can act as any other advisor, so review means
  seeing exactly what that advisor sees.

The cross-advisor management view belongs in Holy Corner, not here. This ticket builds only what
Grassmarket needs to be demonstrable.

## Scope

1. **A single demo advisor holding the full worked example.** `scripts/seed_demo.py` seeds one
   account (`demo@bruntsfield.capital`) with a coherent story: prospects at every pipeline stage,
   two assessments finalised and one in progress, the deliverables generated from them, an
   engagement with workshops and stage history, and the earnings lines that follow. Every record
   is DEMO provenance and watermarked. The per-advisor scatter that exists today is replaced, not
   added to.
2. **Act-as, not impersonate-silently.** An admin principal may open a session scoped to another
   consultant. Implemented in the repository layer where scoping already lives (non-negotiable #9),
   so the acting-as principal is a real scoped principal and every existing scoping test still
   holds. Requirements:
   - only an admin may start it, and only against an existing consultant,
   - the UI shows a persistent banner naming the advisor being viewed and offering one click back,
   - every act-as session start and end is written to the audit log with both identities,
   - writes performed while acting as someone else are recorded with the acting admin's id as
     well as the subject's. No silent authorship.
3. **john@bruntsfield.capital provisioned as admin** through the domain SSO path (GRS-0173), not
   as a hand-seeded row.
4. **Staging seeded to match** and the two production strays currently on the advisor account
   (`Revolut` draft at 0% and `Meridian Securities` finalised at 2%) resolved by the founder's
   decision, since the cleanup tool will not remove production records (ADR-0047).

## Test plan

1. Scoping tests, extended: an admin acting as advisor A sees exactly what A sees and nothing
   more, and an admin not acting-as still cannot read A's records through advisor endpoints.
2. A non-admin cannot start an act-as session. Asserted at the repository layer.
3. Audit test: starting and ending act-as writes both identities.
4. `seed_demo.py` twice produces identical counts, extending the idempotence assertion GRS-0177
   added.
5. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- The cross-advisor management dashboard. That is Holy Corner.
- Deleting production records (ADR-0047 says no; the founder decides those two by hand).
- Any change to what advisors themselves can see.

## Acceptance

The founder logs in as john@bruntsfield.capital, switches to the demo advisor, and walks one
client from prospect to signed deliverable to commission without changing accounts or hitting a
gap.

---

## Status reconciliation — 2026-08-01

**PARTIAL.** Scopes 1 and 2 are complete. Scopes 3 and 4 are not built and the ticket stays open.

## What shipped: scope 2, act-as

**The safety argument is one property, and it is what most of the tests hold up: act-as NARROWS,
it never widens.** `begin_act_as` returns a principal that IS the subject — their id, their role,
their founder status — with `acting_admin_id` carried alongside purely as attribution.
`_assert_can_access` does not read that field and is unchanged, so every pre-existing scoping test
still passes untouched (1499 green). An admin acting as an advisor is genuinely *less* privileged
than that admin was a moment earlier, and there is no path by which acting as someone shows more
than being them would.

Enforced in the repository layer, where scoping already lives (non-negotiable #9), not in a router.

**The token says who is at the keyboard.** `sub` stays the admin; a new `act_as` claim narrows the
session. That direction was chosen deliberately — the identity that authenticated is the identity
in `sub`, and act-as is a restriction layered on top rather than a substitution underneath. The
principal is rebuilt per request from the subject's stored row, so a role change or a deleted
account takes effect immediately instead of living on inside an issued token, and the admin check
is re-run on every request rather than trusted from mint time.

**Three refusals**, each for a stated reason: only an admin may start it; nobody may act as
themselves (it would record a lie); and no chaining, because acting as A and then as B leaves the
log ambiguous about who authorised the second hop. Worth noting how the first two interact — while
acting as a consultant the principal is not an admin at all, so the narrowing refuses a chained hop
before the specific guard is reached. The guard still matters for admin-acting-as-admin, and both
paths are tested.

**Recorded with both identities.** `ACT_AS_STARTED` / `ACT_AS_ENDED` carry the admin as actor and
the subject as resource. `record_audit` gained an `acting_admin_id` that annotates rather than
replaces the actor, because the record has to say both things: the work is the subject's, and a
named admin did it. Dropping either half is how an audit log stops answering the question it exists
for.

**A persistent banner.** Fixed above the sticky header, naming the advisor, warning that the work is
recorded against both accounts, with one click back. Not dismissible — and when the name cannot be
fetched it degrades to a banner *without* a name rather than to no banner, because the dangerous
version of this state is the invisible one.

**Not issued a refresh token.** An act-as session is short-lived and non-renewable on purpose: it
should end because the admin finished looking, not because a background refresh quietly kept it
alive for a day.

## What shipped: scope 1, the coherent story

**The scatter was already gone** — every seed path had been consolidated onto one owner before this
ticket ran. What was missing was not tenancy but *shape*: three finalised firms is three cards in one
column, nothing in flight, and no workshop ever held. A filing cabinet rather than a business.

`demo_story.py` adds, on the same account:

- **A prospect at every one of the ten pipeline stages**, each walked through its stage path one
  transition at a time rather than placed. That is slower than writing rows and it is the point — a
  card teleported into `delivered` carries no transition history, so the board's time-in-stage
  flags, its most useful signal, would show nothing. The seed produces 55 history rows with a real
  spread (one card has 8 transitions behind it).
- **One assessment left in progress** (Dalkeith Asset Management), so the portfolio shows a state
  other than finalised and the wizard has something to resume. A demo where everything is finished
  says nothing about the part an advisor actually spends their time in.
- **Six delivered workshops**, created *before* the stage walk reaches `workshop_delivered` so the
  record and the history agree. A stage claiming a workshop happened with no workshop to open is the
  quiet inconsistency a careful viewer checks first.
- **A loss and a nurture.** A demo with no closed-lost card teaches an advisor to expect the wrong
  thing.

It **adds to** the showcase rather than replacing it: the three scored firms are the part with real
data behind them, and recreating that here would mean two sources of truth for one story. The story
prospects are deliberately different names, so a viewer can tell at a glance which records carry a
scored assessment and which are pipeline colour — there is a test for that.

Seed results are now tagged `showcase` or `story`, so callers distinguish the two without
pattern-matching company names. **No commissions on the story prospects**: they are pipeline shape,
not closed business, and inventing sales would put money-shaped numbers behind cards that never sold.

## What is NOT built

- **Scope 3 — `john@bruntsfield.capital` provisioned as admin via domain SSO (GRS-0173)** rather
  than a hand-seeded row.
- **Scope 4 — staging seeded to match, and the two production strays.** The strays (`Revolut` draft
  at 0%, `Meridian Securities` finalised at 2%) are **explicitly a founder decision** under
  ADR-0047, which forbids deleting production records. Not mine to make.

Note that scope 1 and scope 4 now also gate the **production showcase seed** — see the production
seeding note on GRS-0236.

## The act-as starter, added 2026-08-01

The mechanism shipped without a way to begin: the API, the narrowing, the audit and the exit banner
all existed, and starting a session needed an API call. **A capability an admin cannot reach from
the browser is a capability they do not have**, so this was the missing half rather than a nicety.

- **`GET /auth/act-as/candidates`** — admin only, excludes the caller (acting as yourself is refused
  anyway, so offering it would be a choice the gate then rejects) and excludes inactive accounts.
  Named for its one purpose rather than as a general directory: a consultant roster is not something
  anyone asked for on a product whose scoping discipline is that advisors do not see each other.
- **The picker lives in the account menu**, because acting as someone is a change to who you are for
  the next few minutes, and that is where a person looks to see and change who they are signed in as.
- **It names the consequence before it happens** — the session is recorded against their account and
  yours. The banner says it again once the session starts. Saying it twice is cheap; the surprise of
  discovering it later is not.

One routing detail worth keeping: `/act-as/candidates` is declared **before** `/act-as/{consultant_id}`
so the literal path wins the match. Without that ordering "candidates" is parsed as a UUID and every
request 422s — a routing bug that presents as a permissions bug. There is a test for it.

