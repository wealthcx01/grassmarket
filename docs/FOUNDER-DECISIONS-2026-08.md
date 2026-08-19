# Founder decisions — August 2026

Seven decisions only the founder can make. Each one blocks real, specified work that is otherwise
ready to build. Nothing here needs code written first; everything here is waiting on a judgement, a
value, or an access grant.

This file is the single list. When a decision is taken, record it here with the date, then the
blocked tickets move in `docs/BACKLOG.md`. **Engineering does not invent values or structures to
unblock itself** — that is precisely the silent-fallback failure the whole codebase is built to make
impossible (CLAUDE.md non-negotiable #3).

| # | Decision | Blocks | Cost of not deciding |
|---|---|---|---|
| **D1** | Elicitation: fill the worksheets, or ratify the starter values as interim | GRS-0150, 0212, 0237(3) | Non-retail scores stay indicative; our own provenance records overstate their evidence |
| **D2** | Commission Schedule v7 as the earnings config source | GRS-0067 | Earnings pays from placeholder config |
| **D3** | Harvest the ASX/NSI pack structure as house templates | GRS-0072/0073 | No house deliverable types; advisors improvise |
| **D4** | Multi-currency and UK regulatory framing | GRS-0147 residue | GBP-locked; wealth firms see no Consumer Duty framing |
| **D5** | Certification teeth, doctrine naming, independence disclosure | GRS-0148 residue | "Certified" means self-assessed recall; no conflict record |
| **D6** | Google Workspace OAuth scopes | GRS-0197 | No Gmail/Calendar integration |
| **D7** | Schedule the Helmer review | GRS-0201, ADR-0046 | Permission grant's condition unmet |
| **D8** | Curate 120 institution names the LSEG roster stored as domain stems | GRS-0238 residue | Prospecting lists `gs`, `db`, `uk` — real firms an advisor cannot recognise |

---

## D1 — Elicitation: fill the worksheets, or ratify what we have as an interim

**Ticket:** GRS-0150 · **Also unblocks:** GRS-0212, GRS-0237 scope 3 · **ADR:** ADR-0037

### The exact question

The wealth and exchange profiles score today on **uniform placeholder weights**. Two worksheets exist
and are **empty** — `docs/elicitation/wealth-elicitation-worksheet.md` and
`exchange-elicitation-worksheet.md` both still have blank `___` cells for every θ, α, δ and critical
row. Which of these do you want?

**Option A — run the elicitation.** Fill both worksheets (θ headline weights, α bottleneck aggression,
δ module weights, critical-module flags, plus a one-line dispersion note per family). Engineering
wires them into `elicited_{wealth,exchange}_coefficient_set` and activates in one recorded commit.

**Option B — ratify the current starter values as founder-decided interim.** The numbers stay as they
are, but their provenance is rewritten to say what actually happened: founder-directed starter values,
panel pending. Re-elicitation becomes a scheduled future ADR.

### The provenance half is DONE — and this section overstated it

**Corrected 2026-08-19 (GRS-0237 scope 3).** This section previously said that
`elicited_coefficients.py` "stamps **every** weight family" with
`set_by="bruntsfield-elicitation-panel-2026"`. That was wrong, and measuring it before fixing it is
what found the error. What was actually true:

| Set | In production? | Provenance said | Status |
|---|---|---|---|
| retail `v1-elicited-2026` | **No** — built, client-usable, but not active | `bruntsfield-elicitation-panel-2026`, "elicited by the Bruntsfield weight panel" | **was false; now corrected** |
| wealth / exchange starters | **Yes** — active since 2026-07-20 (ADR-0037) | `engineering-starter-research-validated-2026-07`, "founder-activated, panel ratification scheduled" | was already honest |

So the false claim sat in a **dormant** set, not in the records reaching clients today. It was still
worth fixing — that set is the one that activates when the panel signs off, so the lie was queued
rather than live — but it was less severe than this file claimed.

The correction has shipped: the retail record now names
`bruntsfield-engineering-provisional-2026-07` and says plainly that no panel has convened, and
`test_no_provenance_record_claims_a_panel_that_has_not_met` fails if any of the three sets
reintroduces the claim under any wording. **No coefficient value changed.**

**What still needs your decision is the values themselves**, not the record — Option A or Option B
below. Note the related fact the white paper now states: because retail scores on
`v1-draft-pending-elicitation` with `client_usable=False`, **the default profile cannot produce a
client-facing deliverable at all.** Only wealth and exchange can. That is the fail-loud design
working, but it is probably not what you expect the product to do.

### Recommendation

**Option B now, Option A scheduled.** The numbers are not obviously wrong, and B is honest, immediate,
and unblocks the white paper. A real panel is worth doing, but making it a precondition has already
cost weeks; ratifying an interim converts a blocker into a dated commitment.

---

## D2 — Commission Schedule v7 as the earnings config source

**Ticket:** GRS-0067 · **ADR:** ADR-0026 (amends ADR-0017)

### The exact question

Three parts, all needed together:

1. **Confirm** Commission Schedule v7 is the authoritative source for earnings configuration.
2. **Supply the v7 template values** from OneDrive for ingestion. These are commercial terms and
   **must never be committed to this repo** — hand them over for ingestion into config, the same way
   the LSEG dataset was handled.
3. **Answer the structural question:** does *consultant tier* survive as a Stream-B axis, or is it
   replaced by *delivery type*? GRS-0075/0076 built the two-stream engine against tier; if tier is
   going away, the change is small now and expensive after advisors are paid against it.

### Recommendation

Confirm v7 and hand over the values. On the third part I have no basis to recommend — it is a
commercial-model question about how you want advisors to see their own earnings, not a technical one.

---

## D3 — Harvest the ASX/NSI pack structure as house deliverable templates

**Ticket:** GRS-0072/0073

### The exact question

The estate sweep found the *real* house output is the **Outside Read Deck, Note, Primer, and Strategic
Assessment / 7 Powers Brief** — the ASX and NSI packs — and that the PRD's seven deliverable types do
not include them. Two asks:

1. **Approve** harvesting the pack *structure* (section order, exhibit grammar, house voice),
   anonymised, as templates in this repo.
2. **Make the packs available** as reference material. They live in OneDrive and are not in the repo.

The client-identifying content stays out; what is harvested is the shape.

### Recommendation

Approve. This is the single highest-leverage content decision open: advisors currently improvise the
document that represents the firm, and GRS-0211/0219/0220 just built the machinery to render a
house-standard report properly.

---

## D4 — Multi-currency and UK regulatory framing

**Ticket:** GRS-0147 residue (verified unbuilt during the 2026-08-01 reconciliation)

### What the reconciliation found

GRS-0147's other scope items shipped — the wealth operating model is live and client-usable, the
wealth infrastructure taxonomy is in, exchange is native, per-profile metrics work. **Two scope items
were never built:**

1. **Multi-currency.** The GBP lock the mock-advisor personas hit is still in place: there is no
   currency field or normalisation anywhere in the registry or the assessment contracts. A US
   neobroker's metrics still have to be entered as though they were sterling.
2. **UK regulatory framing** (Consumer Duty / SM&CR / MiFID suitability). The only trace in the whole
   product is a placeholder string in `frontend/components/steps.tsx:222`. Both wealth personas
   expected this front-and-centre.

### The exact question

Is multi-currency in scope for the advisor product now, or is the book UK/GBP-only for the
foreseeable? And should Consumer Duty / SM&CR framing be a first-class part of the wealth assessment,
or is it out of scope for a platform-power tool?

### Recommendation

**Multi-currency: yes, and soon** — it is a hard blocker on any non-UK engagement, and it gets more
expensive to retrofit with every scored assessment. **UK regulatory framing: scope it small** — a
named section in the wealth rubric rather than a compliance module. We are not a compliance product
and should not imply we are.

---

## D5 — Certification teeth, doctrine naming, independence disclosure

**Ticket:** GRS-0148 residue (verified unbuilt during the 2026-08-01 reconciliation)

Three separate calls that arrived together from the mock-advisor stress test.

### D5a — Does "Certified" require a server-enforced pass?

Today the comprehension gate is **UX-level self-assessed recall**: the learner tells the app they
understood. "Certified" is not currently tied to a minimum drill or arena record. Should it be?

*Recommendation: yes.* A certification an advisor can award themselves is not a certification, and it
is the one Academy claim that a hire will test. This needs MC auto-grading design, so it is a real
build, not a copy change.

### D5b — Does the "weapons / zero-sum" doctrine naming survive?

The Sales Egoist doctrine's "own the zero-sum pipeline" and "Relationship / Challenger / Demo
**weapons**" branding clashes with fiduciary wealth culture. The content is strong; the naming is the
issue.

*Recommendation: keep the vocabulary inside the course (it is internal training and the doctrine's own
voice is part of its force), and bar it from every client-adjacent surface.* **This is live right
now** — GRS-0218 builds the Sales Egoist course in Phase 1, and I am building it to that rule unless
you say otherwise.

### D5c — Is there a conflict/independence disclosure record?

An advisor assesses a client and earns commission selling that client third-party products
(Benzinga / OpenBB / Brandfetch), with no client-facing disclosure of that relationship anywhere.

*Recommendation: build a disclosure record.* This is the item most likely to be raised by a
sophisticated client, and the cheapest to fix before rather than after it is raised.

---

## D6 — Google Workspace OAuth scopes

**Ticket:** GRS-0197 · **Founder-side console work**

### The exact question

GRS-0197 is specified and buildable, but needs scopes granted in the Google Cloud console for
`@bruntsfield.capital` Workspace accounts. Sign-in stays as it is (`openid email`); the integration
adds incremental consent for `gmail.readonly` and `calendar.readonly`.

**`gmail.readonly` deliberately excludes any send scope** — the Studio reads mail and never sends. A
send path would be GRS-0204 and its own decision.

You need to: enable the Gmail and Calendar APIs on the project, add the two read scopes to the consent
screen, and confirm whether the app stays internal to the Workspace (no Google verification review) or
goes external (which triggers review).

### Recommendation

Grant the two read scopes, keep the app internal to the Workspace. Internal avoids the verification
review entirely, and every intended user is on a managed account anyway.

---

## D7 — Schedule the Helmer review

**Ticket:** GRS-0201 · **ADR:** ADR-0046

### The exact question

Your permission from Hamilton Helmer to use the 7 Powers mathematics is **conditional on his reviewing
the resulting work** (ADR-0046, recorded 2026-07-23). That review has not been scheduled. GRS-0201
produces the review packet — the adaptation document, marked to distinguish his mathematics from our
application of it.

When does the review happen, and in what form (written packet, or a session)?

### Recommendation

Schedule it before GRS-0201 embeds the adaptation in the wizard. The packet is most of the way there:
`docs/ATLAS-7Powers-Adaptation.md` shipped under GRS-0180, and
`data/reference/7powers-math-extraction.md` is being verified against the now-committed audiobook
supplement as part of Phase 1. Sending a packet that is already accurate is a better first contact
than sending one we plan to correct.

---

## What is *not* on this list

For the avoidance of doubt, these are engineering's to do and are not waiting on you: the GRS-0229–0245
wave (client-trust, report workflow, first-run experience), GRS-0218 (the Sales Egoist course — source
material landed 2026-07-31), and the legacy open queue in `docs/BACKLOG.md`. If any of those turns out
to need a decision, it comes here rather than being guessed at.


---

## D8 — 120 institutions in the registry are named `gs`, `db`, `citi`

**Ticket:** GRS-0238 residue · **Raised:** 2026-08-19 while building the Prospecting page

### What the measurement found

`data/gtm/lseg/contributor_institution_map.csv` has an `inferred_institution` column that holds
**the stem of each firm's domain**, not its name — `barclays`, `gs`, `jefferies`, `db`. 124 of 129
are all-lowercase. So 128 of the registry's 576 institutions are listed under a string no advisor
would recognise, and a handful (`uk`, `us`, `hk`) come from source rows that are simply broken.

Eight of them matched a properly-named bank-list row and have been **merged automatically**. The
other **120 have no counterpart**, and nothing engineering can do resolves them: turning `gs` into
"Goldman Sachs" is a guess, and a guess written into the database is indistinguishable from a fact
afterwards. They currently render with a `name unverified` badge, which is honest but not useful.

### The exact question

Who curates the 120? It needs someone who knows the market to confirm `htsc` is Huatai Securities
and `zkb` is Zürcher Kantonalbank. Three options:

**Option A — you curate the list.** I export the 120 stems with their domains and analyst counts as
a CSV; you fill in the names; I load it as a curated override with its own provenance record.
Probably an hour of your time, and it makes the Prospecting page fully usable.

**Option B — curate only what matters.** The 120 are not equal: some carry 50 analyst contacts,
others carry one. Curate the top 20 by contact count and leave the tail marked.

**Option C — leave them marked.** The page is honest as it stands; the rows are just less useful
than they could be.

### Recommendation

**Option B.** The value is concentrated in the firms with real contact coverage, and it converts a
1-hour task into a 15-minute one without pretending the tail is solved. I can produce the ranked
export whenever you want it.

### Note

Whatever you choose, the fix is a **curated override table with its own provenance**, never an edit
to the imported rows. Re-running the importer must not silently undo a human's curation, and a
curated name must be distinguishable from an imported one.
