# GRS-0250 — OpenClaw / Omarchy: evaluate, with a recommendation to decline

**Status:** OPEN (2026-09-02) — decision ticket, no build. **Priority:** LOW. **Type:** Tooling decision.
**Founder question:** 2026-09-02 — *"would your performance improve in building Grassmarket if we installed OpenClaw and Omarchy?"*

## What they are (checked 2026-09-02)

**OpenClaw** (`openclaw.ai`) — open-source platform for building personal AI agents ("Claws").
2.0 shipped 2026-08-30: 933 contributors, 16,000+ PRs, simplified install, rebuilt browser app,
multiplayer cloud sessions. Works with existing Claude or ChatGPT subscriptions, API keys, or local
models. Its use case is wiring agents across email, messaging and APIs.

**Omarchy** (`omarchy.org`) — a Linux distribution by DHH, incubated at 37signals: *"the malleable
OS for the age of agents."* Arch-based, ships as an ISO, with a manual, plugins and a Discord.

## Recommendation: decline both for this project

Neither touches what is actually slow.

**Omarchy is a desktop operating system.** Grassmarket builds on a headless Hetzner CX22 running
Ubuntu and deploys to Railway containers. Omarchy's value is in the desktop environment — the
window manager, the theming, the local agent integration — and this box has no desktop. Replacing
the OS changes nothing about FastAPI, Postgres, or a 15-minute pytest run, and costs a rebuild of a
working, reproducible environment. **On the founder's own Windows machine as a daily driver it is a
genuinely separate and reasonable question, with no bearing on this repo.**

**OpenClaw is an agent platform, and we already have one** — Claude Code, running in this repo,
with the project's skills, the gstack workflow, and a merge process that has shipped 205 tickets.
Adding a second agent runtime to orchestrate the first is overhead, not leverage.

Where OpenClaw *would* genuinely fit is **inside the product**: advisor-facing automation across
email and calendar. That is real, and it is already ticketed — **GRS-0197** (Gmail + Calendar),
**GRS-0203** (thin outreach sequencer), **GRS-0204** (send path), **GRS-0207** (outreach/CRM
platform decision). If OpenClaw is to be considered, it belongs as a candidate *in GRS-0207's
platform comparison*, judged against the alternatives on that ticket's own terms — not as
development tooling.

## What would actually speed the build up

Named honestly, since the question was about performance:

1. **The 3 GB box.** `oom-kills-on-3gb-hetzner-box` is a recurring session-killer: CX22, no swap,
   RAM-backed `/tmp`. A rescale is roughly £10/month and **needs the founder** (billing access).
   This is the single biggest real constraint on throughput.
2. **The 15-minute backend suite.** `pytest -n auto` via `pytest-xdist` is a one-line dev
   dependency and gates every merge. On a bigger box this compounds with (1). *Caveat worth
   testing:* several suites share an in-memory SQLite via `StaticPool`, so parallelising may need
   per-worker databases — measure before promising the speedup.
3. **The founder-gated items.** GRS-0150 (elicitation panel), Commission Schedule v7, the ASX pack.
   No tool moves these; they are the actual critical path.

## Done when

The founder says yes or no. If no, close as declined and record why, so the question is not
re-litigated in six months. If OpenClaw is to be reconsidered, it moves to GRS-0207 as a candidate
platform rather than staying here.
