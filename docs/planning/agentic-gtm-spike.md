# Agentic GTM — research spike (GRS-0195)

- **Status:** Closed 2026-07-25. Time-box: two working days, opened and closed 2026-07-25.
- **Question:** the founder asked for "whatever best in class git repo there is for enabling
  agentic GTM" to help advisors run cold outreach.
- **Output:** this memo plus the follow-on ticket drafts named in §6. Docs only — no dependency,
  config, or source change anywhere in the repo.
- **Recommendation:** **build thin.** See §5.

## 0. Supply-chain attestation

The hard rule in the ticket was followed. Nothing was downloaded, installed, or executed during
this spike. Every candidate was assessed by reading its public repository page, its licence, and
its documentation. No candidate was installed into any environment holding Grassmarket credentials
or data, no dependency was added to `pyproject.toml` or `package.json`, and no lockfile changed.
A security review precedes any future adoption, and that review is a precondition written into the
follow-on ticket rather than an afterthought.

One consequence worth stating plainly: the figures in §1 are as published on the repositories at
the time of writing and were not verified by cloning or building. That is the correct trade for a
selection spike, and it is why the recommendation does not rest on any single number.

## 1. Candidate survey

### Evaluated in full

| Candidate | Repo | Licence | Signal | Stack | Hosting |
|---|---|---|---|---|---|
| **OpenOutreach** | `eracle/OpenOutreach` | GPLv3 | ~2.5k stars | Python 3.12, Django, SQLite | Self-hosted; sends via your own SMTP/IMAP mailbox |
| **n8n** | `n8n-io/n8n` | Sustainable Use Licence (fair-code, source-available) + Enterprise | ~198k stars | TypeScript, Postgres or SQLite | Self-hosted or managed |
| **Linki** | `moaljumaa/linki` | Linki Sustainable Use Licence (source-available) | ~91 stars | Next.js, Node 22, SQLite | Self-hosted via Docker, or managed on Opsily |
| **GTM Skills** | `gtm-skills/gtm` | MIT | ~123 stars | TypeScript/Next.js, plus prompt content | Prompt library; the running platform is the commercial Prospeda |
| **Mautic** | `mautic/mautic` | GPLv3 | Mature, Acquia-backed | PHP, MySQL/MariaDB | Self-hosted or managed cloud |

### Screened out, with the reason

- **`b2b-sdr-agent-template`, `OpenSales`, `AI-SDR-Agent`, `linki`-class templates built on
  hosted agent runtimes** — template repositories rather than maintained systems. Bus factor of
  one and no release history; adopting one is adopting a fork on day one.
- **Clay, Apollo, Smartlead, HeyReach and the rest of the commercial agentic-GTM tier** — not
  open source, and each puts a third-party SaaS in the send loop, which criterion 2 rules out
  before any other consideration.
- **General agent frameworks with GTM templates (CrewAI, LangGraph and similar)** — these are
  agent runtimes, not GTM systems. Choosing one answers "how do we orchestrate an LLM", which is
  not the question; the Claude Agent SDK is already the answer to that in this stack.

## 2. Evaluation matrix

Scored 0-2 against the six fixed criteria. 2 is a clean fit, 1 is a fit with work, 0 is a
structural mismatch.

| Criterion | OpenOutreach | n8n | Linki | GTM Skills | Mautic |
|---|---|---|---|---|---|
| 1. Approval-gating fit | 0 | 2 | 0 | n/a (2) | 1 |
| 2. Self-hosting on Railway | 2 | 2 | 1 | n/a | 1 |
| 3. ADR-0045 registry fit | 0 | 1 | 0 | 2 | 0 |
| 4. Licence for commercial use | 0 | 1 | 0 | 2 | 0 |
| 5. Maintenance health | 1 | 2 | 0 | 1 | 2 |
| 6. Security posture | 1 | 1 | 1 | 2 | 1 |
| **Total (max 12)** | **4** | **9** | **2** | **7 of 10 applicable** | **5** |

### Where the scores come from

**1. Approval-gating fit — can every outbound send be forced through a human approval checkpoint
without forking the send path?** This is the criterion that does most of the work, because
non-negotiable #8 is a runtime guarantee rather than a convention.

OpenOutreach and Linki both score 0, and for the same structural reason: autonomy is the product.
OpenOutreach's own framing is that it "discovers leads, qualifies them on your own machine, and
runs agentic email outreach from a mailbox you own"; its gates are a spend cap and a
confidence threshold on which leads earn a paid email lookup. Those are cost controls, not
approval controls, and a cost control does not tell you a human read the message. Inserting a
blocking human checkpoint means forking the send path in both projects.

n8n scores 2 because human approval is a first-class workflow primitive rather than something
bolted on: it advertises "multi-step AI workflows with logic, tool use, human approvals, and full
observability". Mautic scores 1 — campaigns can be staged and released by a human, but the unit of
approval is a campaign, not the individual message to a named person, which is the granularity the
compliance posture in §3b actually requires.

**2. Self-hosting on Railway.** OpenOutreach and n8n are clean: both run as ordinary containers,
and n8n speaks Postgres, which is the store this platform already runs. Mautic scores 1 because
it brings a PHP runtime and MySQL/MariaDB into a Python and TypeScript estate, which is a second
operational stack to maintain for one capability. Linki scores 1: it self-hosts via Docker, but
its SQLite-only store does not match a managed-Postgres deployment.

**3. Data-model fit with the ADR-0045 registry — can targets and contacts stay the system of
record, with provenance preserved?** Every running candidate scores 0 or 1, and this is the second
decisive result. Each ships its own contact store as its core abstraction. Adopting one means
either syncing `registry_targets`/`registry_contacts` into a parallel store, or demoting the
registry to a feeder. Both break the thing GRS-0193 was built for: a contact carries `source` and
`imported_on`, `verified` means a human confirmed it, and GRS-0194's whole two-source split rests
on that provenance surviving. A synced copy loses it at the first write. n8n scores 1 rather than
0 only because it can be driven statelessly against our API instead of owning the contacts.

**4. Licence compatibility for commercial use.** OpenOutreach (GPLv3) and Mautic (GPLv3) score 0:
this is a commercial, closed platform, and integrating GPLv3 code into it is not a decision to
take casually as a side effect of picking an outreach tool. Linki's Sustainable Use Licence is
source-available with commercial-use restrictions and scores 0 for the same class of reason.
n8n's fair-code Sustainable Use Licence scores 1: self-hosting for internal use is permitted, but
the terms restrict offering it onward as part of a commercial service, which is exactly the
question a future Holy Corner productisation would raise. Only GTM Skills (MIT) is unencumbered,
and it is content rather than software.

**5. Maintenance health.** n8n and Mautic are genuinely healthy projects with real release
histories and institutional backing. OpenOutreach's ~2.5k stars are meaningful but the project is
young. Linki, at ~91 stars, is a bus-factor-of-one dependency in the send path, which is the worst
possible place for one.

**6. Security posture.** Every candidate that parses inbound replies with an LLM carries
prompt-injection exposure, and that exposure is not hypothetical here: a reply from a prospect is
attacker-controlled text arriving in a system holding the network's contact registry. OpenOutreach
reads replies over IMAP "for agentic follow-up", which is precisely that surface. None of the
running candidates scores 2, and any adoption would need the injection boundary designed rather
than inherited.

## 3. Constraint analysis

### (a) Where the human-approval gate attaches

The seam already exists and is proven. ADR-0009 established the pattern for AI narratives: an
owned resource carrying the proposal text and the approval trail, a status moving
`proposed → approved | rejected`, an **injectable drafter port** so the generator is never a
concrete SDK, and a runtime refusal when anything unapproved reaches a client surface. Outreach is
the same shape with a different verb. The concrete seam for the recommended path is:

- an `OutreachMessage` owned resource — target, contact, channel, subject, body, the drafter and
  prompt-template versions, and the approval trail — mirroring `AINarrative` field for field;
- an injectable `MessageDrafter` port with a deterministic template drafter shipped, so the whole
  flow is exercised offline and CI never makes a model call;
- **the send function refuses any message not in `approved`**, in the same way a client-facing
  deliverable is refused when a narrative is unapproved. The gate is in the send path itself, not
  in the UI that calls it, which is what makes it a runtime guarantee.

The reason this matters for the selection: in every adopt-X path, that refusal has to be injected
into somebody else's send loop and then defended against every upstream release. In the build-thin
path it is the send function's first line.

### (b) Compliance posture for regulated and sell-side contacts

The Barclays brief carries its own caveat, and GRS-0194 now renders it on every generated map:
communications to sell-side research staff are compliance-logged by the recipient's firm, and a
warm referral through the ownership path reaches the platform owner far more reliably than an
unsolicited email to an analyst. That is not decoration. It means the highest-value contacts in the
registry are exactly the ones where volume outreach is counterproductive, and an agentic sequencer
optimised for volume is optimising the wrong quantity.

Concretely, any send capability needs: an unsubscribe path honoured across every campaign and
recorded against the contact; a record of the lawful basis for each contact, given that these are
imported business contacts rather than opted-in leads; suppression that survives re-import, since
the registry is re-imported by design and an idempotent upsert must never resurrect a suppressed
contact; and per-message audit, because "we sent this, a person approved it, here is who and when"
is the only defensible answer to a complaint. Two of those four — suppression surviving re-import,
and audit tied to our own approval record — are properties of *our* data model, not of any
candidate.

### (c) Gmail sending implications given GRS-0197

GRS-0197 requests `gmail.readonly` and **deliberately excludes any send scope**: the Studio reads
mail and never sends. Any send capability is therefore a scope escalation to `gmail.send`, which
is a separate, explicitly-approved decision and not an increment on GRS-0197. It also changes the
Google verification posture for the Workspace app.

This is worth being precise about, because it is easy to under-read. Adding a send scope to an
OAuth app that advisors have already authorised silently widens what that grant permits. The
correct sequencing is: the approval gate and the suppression model ship and are tested first, the
scope escalation is requested second, and the escalation is a founder decision recorded in an ADR.
The alternative send path — a dedicated own-domain SMTP mailbox, as OpenOutreach uses — avoids the
scope escalation entirely at the cost of sending from a different address than the advisor's, and
is worth pricing in the follow-on ticket rather than assuming.

## 4. What the evidence actually says

Two independent results point the same way.

The first is the approval row. The two purpose-built agentic outreach candidates score 0 on the
criterion that is a non-negotiable here, and they score 0 structurally rather than incidentally:
their value proposition is that a human is not in the loop. What this platform needs is a
sequencer where a human is *unavoidably* in the loop. Those are not the same product with a
setting changed.

The second is the registry row. Every running candidate wants to own the contacts. GRS-0193 spent
a whole ticket making provenance survive re-import, and GRS-0194's two-source verification split
depends on it. A parallel contact store discards that on the first sync.

The third consideration is scope. What is actually needed is not an AI SDR. It is: pick contacts
from a registry that already exists, draft a message through a port that already has a proven
pattern, route it through an approval gate that already has a proven pattern, send it, record the
result, and honour suppression. The registry, the drafter port, the approval model, the audit log,
and the owner-scoping are all built. The genuinely new work is a sequencer and a suppression list.
Adopting a platform to get those two things, and then spending the integration effort re-imposing
the constraints the platform is designed not to have, is a poor trade.

## 5. Recommendation

**Build thin.** A minimal in-house sequencer over the ADR-0045 registry, with the approval gate
native to the send path, following the ADR-0009 pattern that already works in this codebase.

The evidence for it is in §4: the two candidates built for this job fail the one constraint that
cannot be relaxed, every candidate that runs wants to own the contact record the registry exists to
be, and the components that would be inherited are mostly components already built here. The
integration cost of adopting is not lower than the build cost, and it is paid again on every
upstream release.

**Not "defer".** The registry has just landed with 584 targets and 530 contacts, and the influencer
maps give a named path into them. The capability has a use now.

**Not n8n**, despite its 9 out of 12 being the strongest score in the matrix. It is the right answer
to a different question. n8n is an excellent orchestrator, and if the requirement were to wire many
third-party systems together with human checkpoints it would win. But here it would sit between the
Studio and the Studio's own data, and its fair-code licence raises a question that has to be
answered again the moment any of this is offered onward through Holy Corner. Worth revisiting if
the requirement broadens to general workflow orchestration across the estate, which is a different
ticket.

**The trigger that reopens this question:** if the thin sequencer grows past roughly a single
bounded module — multi-channel sequencing, reply classification, branching cadences — then it has
become a workflow engine, and building one of those in-house is a worse idea than adopting n8n.
That is the point to stop and re-run this comparison, and it is written into the follow-on tickets
as an explicit scope boundary rather than left to notice.

## 6. Follow-on tickets

Drafted in this PR, `Status: Draft — not scheduled`:

- **GRS-0202** — outreach message contract, approval gate, and suppression list.
- **GRS-0203** — the thin sequencer over the registry (operator-triggered, no scheduled sends).
- **GRS-0204** — Gmail send-scope escalation decision and the own-domain SMTP alternative.

GRS-0202 is the prerequisite for both others: the gate and the suppression model exist before
anything can send. GRS-0204 is a founder decision before it is an implementation.

## Sources

- [eracle/OpenOutreach](https://github.com/eracle/OpenOutreach)
- [n8n-io/n8n](https://github.com/n8n-io/n8n)
- [moaljumaa/linki](https://github.com/moaljumaa/linki)
- [gtm-skills/gtm](https://github.com/gtm-skills/gtm)
- [Mautic](https://mautic.org/) and [the 2026 self-hosting guide](https://allthingsopen.org/articles/what-is-mautic-open-source-marketing-automation)
- [awesome-ai-gtm](https://github.com/ong/awesome-ai-gtm) and [GitHub `sales-automation` topic](https://github.com/topics/sales-automation), used to enumerate the candidate field
