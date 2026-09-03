# Grassmarket — where the build stands

**Last updated 2026-09-03.** Read this first in a new session; it is the state of play, not history.

## One line

The product is functionally complete and deployed. A four-ticket backend wave is **in review as a
stack of three PRs**; after they merge, the next work is GRS-0249 (voice notes) and then the
front-end redesign, which now has a full design handoff and a generated API contract to build on.

## Read these before touching anything

| File | What it is |
|---|---|
| `docs/WORK-QUEUE.md` | The ordered queue, and everything that needs the founder |
| `docs/API-SURFACE.md` | 178 endpoints, generated from the app. Regenerate with `scripts/dump_api_surface.py` |
| `docs/openapi.json` | The same, machine-readable — import this into design tooling |
| `docs/REDESIGN-PROGRAMME.md` | The Advisor Studio redesign: ticket allocation 0253–0278, build order, what is contractual |
| `docs/tickets/GRS-02*.md` | 0247–0252 are the current wave; 0253–0264 are the design's backend requests |

## THE STACK — merge order matters

```
main → #272 (GRS-0246) → #271 (GRS-0251) → #273 (GRS-0247)
```

**Merge #272 first, then #271, then #273.** Migration `0044` (documents) follows `0043`
(engagement_assessments); out of order it breaks. Each PR's diff shows the ones beneath it until
they land — normal for a stack, not a mistake.

Nothing was merged to `main` to unblock the work. A `main` push auto-deploys **both** production
services and runs migrations at app import, so that stays a deliberate act.

| PR | Ticket | What it is |
|---|---|---|
| **#272** | GRS-0246 | `engagement_assessments` join table; foreign keys finally enforced in tests |
| **#271** | GRS-0251 | Real transcription + a scanner that inspects bytes |
| **#273** | GRS-0247 | Document upload — 5 endpoints, 178 total |

## Railway is already configured — the code is not merged yet

Set on **staging and production**, `grassmarket-api`, with `--skip-deploys`:

- `GM_TRANSCRIBER_PROVIDER=openai-whisper`
- `GM_MEDIA_SCANNER_PROVIDER=content-type`
- `GM_OPENAI_API_KEY` (the founder's key, piped via stdin — never echoed)

These are inert until #271 merges (pydantic ignores unknown env). **After it merges, media
ingestion works in production.** Before it merges, that endpoint returns 503 — which is correct,
not broken.

`GM_OPENAI_API_KEY` is GM-prefixed **only**, deliberately: a bare `OPENAI_API_KEY` alias would let
whatever key sits in a developer's or CI runner's environment become the one billed and sent client
audio, unchosen.

## What the wave actually found

Three defects that were not what the tickets described:

1. **Production fabricated transcripts.** `EchoTranscriber` — `media.decode("utf-8",
   errors="replace")` — was the transcriber in every environment. An MP3 could not fail: every
   undecodable byte became U+FFFD, the endpoint returned 201, and mojibake was stored as that
   meeting's transcript. Exposure was zero only because no UI reaches the endpoint.
2. **Foreign keys were inert in every test.** SQLite ignores them unless asked per connection;
   Postgres always enforces them. Every referential constraint held in production and did nothing
   in CI.
3. **A cascade bug that would already fail on Railway.** `delete_assessment` deleted deliverables
   while `client_report_links`, `client_report_prose`, `founder_approvals` and `ai_narratives`
   still pointed at them. On Postgres that raises `IntegrityError`. Found only because (2) was
   fixed.

Also fixed: migrations no longer replace the process's logging configuration. `env.py` called
`fileConfig` unconditionally and `run_migrations` runs at app import, so every production boot had
been handing the running service `alembic.ini`'s logging setup.

## Next: GRS-0249 (voice notes)

Most of it is now built. What remains:

1. **Browser `MediaRecorder`** in the advisor UI, working on a phone — that is where the car park is.
2. **Consent gate.** The design is explicit: *no consent, no recording kept.* Store
   `consent_confirmed_at` **and `consent_wording`** — the exact text shown, not a reference to it.

   **Founder-approved wording, 2026-09-03:**

   > *"I'd like to record this session so I can write it up accurately. The recording stays in the
   > Bruntsfield advisor system, is transcribed for my notes, and isn't shared outside the
   > engagement team. Are you happy for me to record?"*

   Any change to this is a founder decision, not an engineering one. See GRS-0255.
3. **Extraction to a proposal, never straight to state.** Reuse Path B exactly: per-field
   confidence, advisor corrects, then confirms. Non-negotiable #8 — a voice note must never move a
   prospect stage on its own.
4. **v1 is record → stop → upload → "transcribing…" → review.** Streaming, speaker labels and
   moment marks are R3, deliberately deferred: the hosted Whisper API takes a whole file, and this
   is the ship order the requests document specifies.

## The design handoff (2026-09-02/03)

The founder supplied a full Advisor Studio redesign: a persistent-rail **desk of cases**. Files in
`/home/dev/inbox/grassmarket/` (NOT in git): `Backend-Requests.pdf`, `Backend-Gap-Audit-v2.pdf`.
The interactive mockup is an artifact; it renders locally in Chromium from the bundle.

**12 backend requests, R1–R12, filed as GRS-0253 … GRS-0264** (founder-confirmed 2026-09-03;
their suggested numbers collided with live tickets). **GRS-0265 … GRS-0278 are reserved for the
frontend cut** — the handoff proposed 0260–0273, which now collide too. Full allocation and build
order in `docs/REDESIGN-PROGRAMME.md`.

Build order is by cost, not number: **0253 → 0259 → 0257**, then **0258, 0256, 0254**, then the
OAuth-sharing subsystems **0261 → 0262 → 0255**. 0260 is a day. 0263/0264 wait on the G2 memo and
gate nothing. **0261 (Gmail) is founder-gated on D6** — the build is cheap, the scope decision is
not.

The design contract is token-level and **contractual, not indicative**: square corners, no shadows,
hairline rules, a 250px rail, exactly three status colours (amber = waiting on a person, red =
broken/overdue, green = healthy), machine values in mono, serif summary sentences stating counts and
consequences. Pixel values are indicative; rebuild spacing in rem.

## Waiting on the founder

| Item | Unblocks |
|---|---|
| **GRS-0150 elicitation panel** | Retail client deliverables. Still the only real blocker |
| **Consent wording** | GRS-0249 |
| **GRS-0207** outreach build-vs-buy | Gates 0202/0203/0204 |
| **GRS-0248** ActiveGraph: adopt or amend the docs | Doing neither is the only wrong answer |
| D4 multi-currency · D5–D7 | Deferred by the founder |

**Received and unused so far:** `Bruntsfield_Consultant_CommissionSchedule_TEMPLATE_v7.docx`
(unblocks GRS-0067) and `ASX_Outside_Read_Deck_v3.pdf` (unblocks GRS-0072). Both in
`/home/dev/inbox/grassmarket/`. **There is no NSI pack** — tickets saying "ASX/NSI" are wrong.

## Process lessons worth keeping

1. **`git add -A` on an uninspected tree shipped a change the founder had rejected.** It reached
   `main` inside the PR that recorded the rejection. Stage explicit paths; check `git status`.
2. **Never switch branches while a background suite is running.** pytest reads source as it walks,
   so a mid-run switch produced 78 phantom failures from a file combination that exists on no
   branch. Verify a suspicious result against the branch before believing it.
3. **A test can pass for the wrong reason.** One asserting the database refuses a delete passed
   because raw SQL used a dashed UUID while SQLAlchemy stores 32-char hex — it matched no rows and
   deleted nothing. Use typed constructs.
4. **Five tests are pinned to literal UI copy** and go red on deliberate rewrites.
   `frontend/lib/retiredCopy.ts` handles retired sentences; the general fix is GRS-0205, unbuilt.
   **Hold GRS-0205 until after the redesign** — rewriting copy over screens about to change is the
   one clear sequencing mistake available.
