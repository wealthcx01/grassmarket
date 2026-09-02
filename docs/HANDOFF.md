# Grassmarket — where the build stands

**Last updated 2026-08-28.** Read this first in a new session; it is the state of play, not history.

## One line

The product is functionally complete and deployed. **Nothing meaningful is left to code.** What
remains is a small number of founder decisions and two files only the founder can supply.

## Numbers

| | |
|---|---|
| Tickets | 244 — **205 done**, 7 blocked on the founder, rest are future features |
| Tests | backend **1,797**, frontend **419** |
| Environments | production + staging, both live and healthy on current `main` |
| Open PRs | none |

## The one thing blocking real client work

**A retail assessment cannot produce a client-facing deliverable.** Wealth and exchange can.

Retail scores on `v1-draft-pending-elicitation`, whose every weight family is uniform 1.0 — every
module, power and metric equally important. That is a placeholder, not a method, so the deliverable
gate refuses it. This is the fail-loud design working.

**Both interim shortcuts were built, measured and rejected (founder decision D1, 2026-08-27):**

1. *Ratify the running weights* — would bless "everything matters equally" as a method.
2. *Activate the v1 set* — buys only four different scalars (θ, α_L, α_module, one strength step;
   every weight family is uniform in that set too), and **broke firm-ordering stability**:
   perturbing the strength encoding by ±20% reordered the showcase firms in 3 of 40 draws, where
   the draft set never did.

**GRS-0150 — the real elicitation — is the only remaining route.** `tools/weight_sensitivity.py`
caught the ordering problem and should be re-run against whatever the panel produces, *before*
activation. `tests/test_elicited_coefficients.py::test_retail_is_not_activated` will fail the
moment retail is switched on, and explains why.

## Waiting on the founder

| Item | What it unblocks |
|---|---|
| **GRS-0150 elicitation panel** | Retail client deliverables. Everything else is unblocked. |
| **Commission Schedule v7** (file) | Earnings pays from real rates, not placeholders (D2) |
| **ASX pack** (file) | House deliverable templates (D3). **There is no NSI pack** — the tickets say "ASX/NSI" and that is wrong. |
| D4 multi-currency + UK regulatory framing | Non-GBP clients; Consumer Duty / SM&CR credibility |
| D5 certification teeth · D6 OAuth scopes · D7 Helmer review | Deferred by the founder |
| Four production assessments | None matched what was authorised for deletion; the founder must name any to remove |

Files go to `/home/dev/inbox/grassmarket/` — `scp <file> dev@100.98.2.79:/home/dev/inbox/grassmarket/`.
Nothing there is in git; commercial terms and client packs must stay out of the repo.

## Loose ends, small

- **`psc.com` and `mchny.com`** — the only 2 of 128 institution names left unresolved (6 contacts).
- **The sidecar bearer token is not loading** on the founder's Windows machine, so the LSEG app key
  is reachable by anything on their tailnet. `bcap-lseg\.env` has the value; the process is not
  picking it up.
- **GRS-0234 scope 4** — the sparse PDF page. Three fixes attempted and measured; all failed, the
  third made it worse. Recommendation recorded: accept the page, and treat the VALUE section's
  thinness as a content question under GRS-0211.

## Two process lessons worth keeping

1. **`git add -A` on an uninspected tree shipped a change the founder had rejected.** It reached
   `main` inside the PR that recorded the rejection, and the test suite flagged it twice before
   anyone noticed. Check `git status` before staging; read failures against what you just changed.
2. **Five tests pinned to literal UI copy** went red on deliberate rewrites during this programme.
   `frontend/lib/retiredCopy.ts` handles deliberately-retired sentences; the general case is
   GRS-0205, unbuilt. Assert behaviour, match copy loosely.
