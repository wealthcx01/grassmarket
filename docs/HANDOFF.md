# Grassmarket — where the build stands

**Last updated 2026-09-03.** Read this first in a new session; it is the state of play, not history.

## One line

The product is functionally complete and deployed. The four-ticket backend wave **has merged**;
GRS-0249 (voice notes) is **half built** — an advisor can record, consent is gated, the audio and
transcript are kept — and the remaining half is turning a transcript into a pipeline proposal.
After that, the front-end redesign, which has a full design handoff and a generated API contract.

## Read these before touching anything

| File | What it is |
|---|---|
| `docs/WORK-QUEUE.md` | The ordered queue, and everything that needs the founder |
| `docs/API-SURFACE.md` | 178 endpoints, generated from the app. Regenerate with `scripts/dump_api_surface.py` |
| `docs/openapi.json` | The same, machine-readable — import this into design tooling |
| `docs/REDESIGN-PROGRAMME.md` | The Advisor Studio redesign: ticket allocation 0253–0278, build order, what is contractual |
| `docs/tickets/GRS-02*.md` | 0247–0252 are the current wave; 0253–0264 are the design's backend requests |

## THE STACK — merged 2026-09-03

```
main → #272 (GRS-0246) → #271 (GRS-0251) → #273 (GRS-0247)
```

All three are on `main`, in that order. Migration `0044` (documents) follows `0043`
(engagement_assessments), and `0045` (voice notes) follows `0044`.

A `main` push auto-deploys **both** production services and runs migrations at app import, so it
stays a deliberate act.

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

#271 has merged, so **media ingestion works in production now.** Any advisor voice note is
transcribed by hosted OpenAI Whisper — see the consent note under GRS-0249 below, which is a live
founder question, not a settled one.

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

## GRS-0249 (voice notes) — half built, on `grs-0249-voice-notes`

**What works now.** An advisor opens a prospect on their phone, presses record, sees a level meter
and a timer, presses stop, and gets a transcript back. The audio is kept beside it. A failed upload
stays on the device and can be sent later, because the car park has one bar.

**The consent gate, and the decision inside it.** The advisor says who is in the room *before*
anything records, and this is not a formality:

- **A voice note** is the advisor alone. No consent line, because there is nobody to ask.
- **A recorded session** has somebody else present. The founder-approved wording from GRS-0255 is
  shown verbatim and both `consent_confirmed_at` and `consent_wording` are stored, or the recording
  is refused outright. *No consent, no recording kept* — never stored-and-flagged.

Both directions are refused: a session without consent, and a voice note claiming consent nobody
gave. The rule lives in the contract, the repository and a table CHECK, so no future caller can
route around it. The wording itself is served by `GET /transcripts/consent-line` — one copy in the
system — and an upload carrying different text is refused.

**Two founder questions this opened, neither of them engineering calls:**

1. **The approved wording tells the client "the recording … isn't shared outside the engagement
   team". The transcriber is hosted OpenAI Whisper, so the audio does leave our infrastructure.**
   The wording is used verbatim and unchanged, as instructed. The advisor-facing UI says plainly
   where the audio goes, so whoever presses record is not misled — but the client hears the
   approved line. Reconciling those two sentences is a founder decision.
2. Whether a solo voice note should show the client-consent line anyway. Today it does not.

**What is left: scope 4, the second half.** The transcript comes back to be read; it does not yet
propose a stage change, a next action and date, a comms-log entry or an engagement note for the
advisor to correct and confirm. Path A maps a transcript to an `AssessmentDocument`; a pipeline
equivalent does not exist yet. Until it does, non-negotiable #8 holds trivially — a voice note
proposes nothing, so it changes nothing.

**Absorbed on the way:** GRS-0254 build 1 and 2. Transcripts now hang off a prospect or workshop,
not only an engagement, because a car-park note has no engagement. `engagement_id` became a real
foreign key at the same time. GRS-0254's re-parent path (build 3) is still open.

**Also deliberately deferred:** streaming, speaker labels and moment marks stay in GRS-0255 for R3.
The hosted Whisper API takes a whole file, so v1 cannot stream and does not pretend to.

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
| **Consent vs. OpenAI Whisper** | The approved wording says the recording is not shared outside the engagement team; the transcriber is a third party. GRS-0249/0255 |
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
