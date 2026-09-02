# Grassmarket — the work queue

**Written 2026-09-02.** What I work through, in order, and what I need the founder for.
Companion to `docs/HANDOFF.md` (state of play) and `docs/FOUNDER-DECISIONS-2026-08.md`.

The build is functionally complete and deployed. 205 of 251 tickets are done. What follows is
everything that is not.

---

## Part 1 — What I can work through without you

Ordered. Each row says what it is and why it sits where it does.

### Now — correctness first

| # | Ticket | Why it is first |
|---|---|---|
| 1 | **GRS-0251** — production transcription is a test double | Production "transcribes" audio by decoding it as UTF-8 with `errors="replace"` and returns 201. It cannot fail, so it fabricates. **A live non-negotiable #3 violation.** Zero exposure today only because no UI reaches it. Blocks GRS-0249. |
| 2 | **GRS-0246** — dangling assessment references (scopes 1, 3) | The join table that makes the whole class of bug impossible rather than merely detected. Scopes 2 and 4 shipped; this is the structural half. |
| 3 | **GRS-0247** — document storage | Advisors have nowhere to put a client document. Needs an ADR on where bytes live. Blocks GRS-0249. |

### Next — the things advisors will actually notice

| # | Ticket | Why |
|---|---|---|
| 4 | **GRS-0242** — Workbench stops leaking internals | Contradictory, internal-facing copy in a surface advisors use weekly. |
| 5 | **GRS-0210** — smart search knows the firms advisors type | Search that misses the obvious firm is the fastest way to lose trust in the data. |
| 6 | **GRS-0198** — assessment & deliverable milestones on the pipeline | Pipeline and assessment are two halves of one story and currently do not reference each other. |
| 7 | **GRS-0249** — voice notes | Founder request. Half the plumbing exists; gated on 0251 and 0247. |
| 8 | **GRS-0214** — what the client gets free vs on engagement | Shapes what a deliverable *is*; touches many surfaces, so earlier is cheaper. |

### Then — depth

| # | Ticket | Why |
|---|---|---|
| 9 | **GRS-0184 + GRS-0213** — scenario workspace | Take together; 0213 is 0184 made drivable. **Decide GRS-0248 first** — if ActiveGraph is adopted anywhere, it is here, and building these by hand first wastes the work. |
| 10 | **GRS-0248** — ActiveGraph: adopt or amend the docs | Do the documentation half **now** regardless (one commit); the adoption spike belongs with item 9. |
| 11 | **GRS-0222** — narrative assistant on real scored data | Large. Pairs with 0213. |
| 12 | **GRS-0196** — Practice Arena v2 | Workbench depth; no dependencies. |
| 13 | **GRS-0205** — rewrite every string in the app | **Explicitly worth holding** until the founder's front-end refinement lands, so the copy pass runs over the final layouts, not the current ones. |

### Lower

GRS-0041 (gated module words in the live-score contract) · GRS-0049 (2026-07-14 audit backlog —
re-triage, some may be stale) · GRS-0192 (content freshness watcher) · GRS-0199 (bench honesty +
opportunity radar) · GRS-0224 (dormant governance coverage) · GRS-0234 scope 4 (sparse PDF page —
three fixes measured and failed; recommendation is to accept it and treat the thinness as content
under GRS-0211).

### Outreach cluster — blocked on one decision, not on me

**GRS-0207** (outreach/CRM platform: build vs buy) gates **GRS-0202** (message contract + approval
gate + suppression list), **GRS-0203** (thin sequencer over the GTM registry) and **GRS-0204** (send
path: Gmail scope escalation vs own-domain SMTP). All four are drafted and none should start until
0207 is answered — see Part 2.

---

## Part 2 — What I need you for

Nothing below can be unblocked by engineering. This is the complete list, old and new.

### Blocking client work

| | What it unblocks | What it costs you |
|---|---|---|
| **GRS-0150 — elicitation panel** | **Retail client deliverables.** The single real blocker. Retail scores on uniform 1.0 weights, so the deliverable gate correctly refuses. Both interim shortcuts were built, measured and rejected (D1, 2026-08-27). | ~1 day of 4–8 experts. Re-run `tools/weight_sensitivity.py` on the result **before** activation. |
| **Commission Schedule v7** (file) | **GRS-0067** — earnings pays from real rates instead of placeholders. | `scp` one file. **Not yet received** — the first attempt failed on a `<vm-host>` placeholder. |
| **ASX pack** (file) | **GRS-0072** — house deliverable templates. **There is no NSI pack**; tickets saying "ASX/NSI" are wrong. | `scp` one file. |

`scp <file> dev@100.98.2.79:/home/dev/inbox/grassmarket/` — nothing there is in git, and commercial
terms and client packs must stay out of the repo.

### Decisions that gate drafted tickets

| | Question | My recommendation |
|---|---|---|
| **GRS-0207** | Outreach/CRM: build the thin layer, or buy? Gates 0202/0203/0204. | Decide before any of the three start. |
| **GRS-0248** | ActiveGraph: adopt on the scenario surface, or amend the docs? | Amend the docs now; spike adoption only alongside GRS-0184. |
| **GRS-0250** | OpenClaw / Omarchy? | **Decline both.** Neither touches what is slow. If OpenClaw is reconsidered, it belongs in GRS-0207 as a product candidate. |
| **GRS-0212** | Exchange customer proposition — needs your commercial view. | — |
| **GRS-0201** | Wizard Powers step: embed the Helmer adaptation (D7). | Deferred by you already. |
| **GRS-0147** | Wealth operating model + segment-native metrics. | Needs your domain judgement, not code. |
| **GRS-0148** | Solo-path discoverability + unfinished account surfaces. | — |
| **D4** | Multi-currency + UK regulatory framing (Consumer Duty / SM&CR). | — |
| **D5 / D6** | Certification teeth · OAuth scopes. | Deferred by you. |
| **Four production assessments** | None matched what was authorised for deletion; name any to remove. | — |
| **GRS-0132** | Admin/oversight — deferred to Holy Corner, recorded only. | No action. |

### Operational, small, yours

- **Rescale the 3 GB box.** ~£10/month, needs billing access. Recurring OOM kills end sessions
  mid-task; this is the biggest throughput constraint I have.
- **The sidecar bearer token is not loading** on your Windows machine, so the LSEG app key is
  reachable by anything on your tailnet. `bcap-lseg\.env` has the value; the process ignores it.
- **`psc.com` and `mchny.com`** — the last 2 of 128 institution names unresolved (6 contacts).
- **Wispr Flow** — tell advisors they can install it and dictate into our existing fields today.
  No public API, so nothing to integrate; free tier is 2,000 words/week. Separate from GRS-0249.

---

## Part 2b — Standing infrastructure answers

- **Supabase: not yet.** Founder decision 2026-09-02. Keep Railway Postgres.
  **GRS-0252 records six triggers for when to revisit** — the load-bearing ones are stored document
  bytes past ~2 GB, a restore taking over 15 minutes, or a second Bruntsfield product needing the
  same identity. Until one fires, the answer stays no.
- **Transcription: OpenAI Whisper**, founder-directed 2026-09-02, behind the existing `Transcriber`
  port (GRS-0251). Client speech leaves our infrastructure, so it needs a UI line and a compliance
  note.

## Part 3 — Front-end refinement

The founder's stated next step. Two notes so the work is not wasted:

1. **Hold GRS-0205** (the app-wide copy rewrite) until the layouts settle. Rewriting strings over
   screens that are about to change is the one sequencing mistake available here.
2. **Five tests have been pinned to literal UI copy** and went red on deliberate rewrites during
   the last programme. `frontend/lib/retiredCopy.ts` handles deliberately-retired sentences;
   the general fix is GRS-0205 and is unbuilt. **Assert behaviour, match copy loosely** — and
   expect a red E2E when copy changes, not a real regression. A copy sweep kept the deliverables
   E2E red on `main` for nine days once already.
