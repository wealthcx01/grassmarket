# GRS-0248 — Adopt ActiveGraph for the agent layer, or drop it from the docs

**Status:** OPEN (2026-09-02). **Priority:** MED. **Type:** Architecture decision.
**Loop:** post-wave. **Relates to:** ADR-0009, non-negotiable #8, PRD §84.

## The discrepancy

`CLAUDE.md` and the PRD both name ActiveGraph as the agent layer. **It is not installed.**
`pyproject.toml` has no such dependency; `src/grassmarket/` has no `agents/` package. The word
appears only in prose and in a few contract docstrings.

This is not an oversight — **ADR-0009 decided it deliberately**: *"A minimal, in-repo
proposal/approval model now; an ActiveGraph adapter later... the ActiveGraph state machine and the
SDK adapter are additive, not rewrites."* The approval semantics of non-negotiable #8 were built
by hand, and they work: extraction, deliverable drafts and quizzes all carry recorded approvals.

The problem is that the documents read as though the library is in use. Anyone joining would look
for it and not find it.

## What ActiveGraph actually is (checked 2026-09-02)

`github.com/yoheinakajima/activegraph` — Apache 2.0, Python 3.11+, v1.10.0 (July 2026), ~625 stars.
An **event-sourced reactive graph runtime**: append-only event log as source of truth, the graph as
a deterministic projection, behaviours that react to the graph rather than calling each other,
fork-and-diff for branching runs, deterministic replay. The accompanying paper is Nakajima, *"The
Log is the Agent: Event-Sourced Reactive Graphs for Auditable, Forkable Agentic Systems"*
(arXiv 2605.21997).

**It is not a graph database and does not require one.** Its `EventStore` backs onto SQLite or
**Postgres** — the database we already run. The materialised graph is in-memory by default, with
FalkorDB as an optional backend. So adopting it needs no new datastore.

## Why it might be worth it

Three properties map onto things we already care about:

- **Deterministic replay** is what non-negotiable #6 asks of scoring runs, done generally.
- **Fork-and-diff** is exactly the scenario-vs-finalised-assessment distinction (#6 again), and
  GRS-0184/GRS-0213 (scenario workspace) are both open and both want it.
- **Append-only audit** is what the approval gate proves by hand today.

## Why it might not

We already have all three, narrowly, and they are tested. Adopting a runtime to re-express working
behaviour is the "re-invent, don't implement" failure in reverse. The honest question is whether
the *scenario workspace* is easier to build on it — not whether the approval gate should move.

## Scope

1. **Decide.** Either (a) adopt for the scenario/agent surface specifically, with an ADR
   superseding ADR-0009's "later", or (b) amend `CLAUDE.md` and the PRD to say the approval model
   is in-repo and ActiveGraph is a candidate, not a component. **Doing neither is the only wrong
   answer** — the docs currently misdescribe the system.
2. **If (a):** spike it behind the existing repository interface on one surface only — recommend
   the scenario workspace, not the approval gate. Measure whether GRS-0213 gets smaller.
3. **If (b):** one commit, two files.

## Note on the founder's framing

The 2026-09-02 request was *"if we don't have a database we need to implement a graphical one so we
can fully realise ActiveGraph."* Two corrections: we **do** have a database (Postgres, live in
production and staging, readiness green), and ActiveGraph **runs on it** — a graph database is an
optional backend for one component, not a prerequisite. Nothing about the storage layer is blocking
ActiveGraph adoption; only the decision above is.
