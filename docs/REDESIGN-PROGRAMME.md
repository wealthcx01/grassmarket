# The Advisor Studio redesign — ticket allocation

**Filed 2026-09-03.** The design handoff suggested ticket numbers that collide with live tickets
(GRS-0250, 0251 and 0252 are taken by OpenClaw/Omarchy, the transcription bug, and Supabase). The
handoff says to renumber to the live sequence; the founder confirmed **file from 0253**. This is
that allocation, recorded so nothing collides again.

## Source documents

| | |
|---|---|
| `Backend-Requests.pdf` | 12 requests R1–R12, in build order. In `/home/dev/inbox/grassmarket/`, **not in git** |
| `Backend-Gap-Audit-v2.pdf` | Gaps G1–G15 with repo anchors. Same location |
| The mockup | An artifact; renders locally in Chromium from the bundle |
| `docs/API-SURFACE.md` · `docs/openapi.json` | 178 endpoints — what the design binds to |

## Backend — GRS-0253 … GRS-0264 (R1–R12)

| Ticket | R | Gap | What |
|---|---|---|---|
| **0253** | R1 | G5 | One needs-you queue, `GET /queue` |
| **0254** | R2 | G13 | Recordings before an engagement exists |
| **0255** | R3 | G12 | Recorder: consent, marks, speaker labels, streaming |
| **0256** | R4 | G14 | Per-section approval on report prose |
| **0257** | R5 | G7 | Admin network ledger |
| **0258** | R6 | G6 | Founder review: return with a note |
| **0259** | R7 | G8 | Contingent earnings: name the blocker |
| **0260** | R8 | G15 | The pocket's one push event |
| **0261** | R9 | G3 | Gmail connection — **founder gate D6** |
| **0262** | R10 | G11 | Booking: availability + webhook |
| **0263** | R11 | G1/G10 | Agents: run store, held plans, spend |
| **0264** | R12 | G2/G9 | Contacts base + capability gating |

**Build order** (from the requests document, not ticket order): cheap joins first —
**0253 → 0259 → 0257**, each building on the last. Then the small state changes — **0258, 0256,
0254**. Then the subsystems that share one OAuth flow — **0261 → 0262 → 0255**. **0260** is a day.
**0263** and **0264** wait on the G2 memo and gate nothing.

## Frontend — GRS-0265 … GRS-0278

Reserved for the handoff's suggested cut, renumbered. One ticket = one branch = one PR.

| Ticket | What | Consumes |
|---|---|---|
| **0265** | Tokens + rail shell (retire radius/shadow, status vocabulary) | — |
| **0266** | The desk | — |
| **0267** | Needs-you queue UI | 0253 |
| **0268** | Cases list + case file | — |
| **0269** | Wizard restyle + step behaviours | — |
| **0270** | Deliverables list, report editor, shared report | 0256 |
| **0271** | Workbench tabs, blind rating, drill/arena/calibration | — |
| **0272** | Earnings with contingent rows | 0259 |
| **0273** | Admin ledger + review detail | 0257, 0258 |
| **0274** | Day-one mode + demo case | 0264 |
| **0275** | Pocket pass | 0260 |
| **0276** | Workshop detail (brief + output filing) | 0261 |
| **0277** | Booking UI | 0262 |
| **0278** | Recorder + extraction review | 0255 |

**Nothing frontend waits on a backend ticket.** Every panel has a truthful "not yet enabled" state
already written into the mockup — agents idle, Gmail not connected, contingency shown as an
estimate. Ship the frontend ahead and let the placeholders retire themselves.

## What is contractual, and what is not

**Contractual:** information architecture and nav order; the screen inventory; the copy voice and
its specific microcopy (serif summary sentences stating counts and consequences; British English;
sentence case; no hype); state transitions; empty, degraded and day-one states; and the honesty
rules — scores as ranges, Not Assessed ≠ zero, benefit and barrier recorded only as a pair,
unverified names marked and never guessed, nothing sends itself, **no dead UI: anything unbuilt
says so in words**.

**Indicative:** exact pixel values (rebuild spacing in rem), the invented prospect names, the
pixel-office plate.

## Two things already absorbed by the frontend, permanently

- **The case timeline** is merged client-side from `/prospects/{id}/history`, `comms_log` and
  `/workshops`. Permanent, by decision — not a gap.
- **The needs-you queue** is composed client-side from three endpoints **until 0253 lands**, then
  the merge is deleted.
