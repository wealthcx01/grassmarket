# GRS-0248 — Adopt ActiveGraph for the agent layer, or stop saying we have

**Status:** OPEN (2026-09-02). **Priority:** MED. **Type:** Architecture decision.
**Loop:** post-wave. **Relates to:** ADR-0009, GRS-0184, GRS-0213, GRS-0222, PRD §84.
**Non-negotiables in play:** #2 (implement, don't re-invent), #6 (immutable versioned runs), #8 (AI proposes, humans approve).

## The discrepancy

`CLAUDE.md` names ActiveGraph as the agent layer. The PRD names it four times, including
§84: *"ActiveGraph agent layer: meeting-intelligence extraction, deliverable drafting,
practice-arena simulation — all event-sourced with approval policies."*

**It is not installed.** `pyproject.toml` has no such dependency. `src/grassmarket/` has no
`agents/` package. The word survives only in prose and a few contract docstrings.

This is not drift. **ADR-0009 decided it deliberately** — *"A minimal, in-repo proposal/approval
model now; an ActiveGraph adapter later... the ActiveGraph state machine and the SDK adapter are
additive, not rewrites."* The approval semantics of non-negotiable #8 were built by hand and they
work: `ai_narratives`, `extractions`, `founder_approvals` and `generated_quizzes` all carry
recorded approvals, with `PROMPT_TEMPLATE_VERSION` and `DRAFTER_VERSION` persisted per proposal.

The problem is only that the documents read as though the library is in use. Anyone joining the
project would go looking for it, not find it, and mistrust the rest of the documentation. That is
the actual cost today.

## What ActiveGraph is (checked 2026-09-02)

`github.com/yoheinakajima/activegraph` — Apache 2.0, Python 3.11+, v1.10.0 (July 2026), ~625 stars,
core dependencies `click` and `pydantic` only. An **event-sourced reactive graph runtime**:

- append-only event log as the source of truth;
- the materialised graph is a deterministic projection of that log;
- behaviours (plain functions, classes, or LLM-backed) react to the graph instead of calling one
  another;
- **fork-and-diff** for branching a run and comparing outcomes;
- deterministic replay from the log.

Companion paper: Nakajima, *"The Log is the Agent: Event-Sourced Reactive Graphs for Auditable,
Forkable Agentic Systems"* (arXiv 2605.21997), which demonstrates the architecture against BabyAGI.

## Correcting the founder's framing (2026-09-02)

The request was *"if we don't have a database we need to implement a graphical one so we can fully
realise ActiveGraph."* Two corrections, from reading the repo:

**1. We do have a database.** PostgreSQL on Railway: 47 tables, Alembic migrations through `0042`,
everything routed through `src/grassmarket/data/repository.py` per non-negotiable #5, per-consultant
scoping enforced there and tested. Production `/health/ready` — which pings the database rather than
returning a constant — was green on 2026-09-02.

**2. ActiveGraph does not need a graph database.** Its `EventStore` protocol backs onto **SQLite or
Postgres** — what we already run. The materialised graph is **in-memory by default**; FalkorDB is an
*optional* backend for one component. Adopting it requires no new datastore and no migration of
existing data.

So nothing in the storage layer blocks this. Only the decision below does.

## The honest case for adopting

Three properties map onto things we already care about, and two open tickets want them:

| ActiveGraph gives | We already have | Where it would help |
|---|---|---|
| Deterministic replay | Scoring runs are immutable + versioned (#6), narrowly | Generalised beyond scoring |
| Fork-and-diff | Scenario vs finalised assessment, hand-rolled | **GRS-0184, GRS-0213** — both open, both want branch-and-compare |
| Append-only audit | Approval trails per table, hand-rolled | Uniform instead of per-feature |

**The question worth asking is narrow: does the scenario workspace get smaller if built on it?**
GRS-0184 (scenario workspace v2) and GRS-0213 (scenarios an advisor can drive) are the two tickets
whose core is "fork this assessment, change some inputs, compare the outcomes, keep the lineage".
That is fork-and-diff, which is a first-class ActiveGraph primitive and would otherwise be written
by hand for the third time.

## The honest case against

We already have replay, forking and audit — narrowly, working, and tested by 1,798 tests. Adopting
a runtime to re-express behaviour that works is the "re-invent, don't implement" failure running
backwards. **The approval gate should not move**: it is load-bearing for non-negotiable #8, it is
proven, and there is no defect to fix there.

Adoption also adds a dependency that must stay compatible with a codebase the founder intends to
keep for years, for a v1.x project one maintainer deep.

## Scope

1. **Decide, and record it.** Either:
   - **(a) Adopt narrowly** — for the scenario/agent surface only. Requires an ADR superseding
     ADR-0009's "later" clause and stating what stays in-repo (answer: the approval gate).
   - **(b) Amend the documents** — `CLAUDE.md` and the PRD say the approval model is in-repo per
     ADR-0009, and ActiveGraph is a candidate for the scenario surface, not a current component.
     One commit, two files.

   **Doing neither is the only wrong answer**, because the documents currently misdescribe the
   system regardless of which way the build goes.

2. **If (a): spike before committing.** Build one surface — the scenario fork in GRS-0184 — behind
   the existing repository interface, with its `EventStore` on our Postgres. Measure whether
   GRS-0213 gets smaller. If it does not, close as (b).

3. **Either way, do (b)'s documentation fix now.** It costs a commit and stops the docs lying while
   the larger decision waits.

## Done when

`CLAUDE.md` and the PRD describe what is actually in the repo, and the adopt/decline decision is
recorded as an ADR with its reasoning.
