# GRS-0250 — OpenClaw / Omarchy: evaluate, with a recommendation to decline

**Status:** OPEN (2026-09-02) — decision ticket, no build. **Priority:** LOW. **Type:** Tooling decision.

## The question

Founder, 2026-09-02: would build performance on Grassmarket improve if we installed OpenClaw 2.0
and Omarchy?

## What they are (checked 2026-09-02)

- **OpenClaw** (`openclaw.ai`) — open-source platform for building personal AI agents ("Claws").
  2.0 shipped 2026-08-30: 933 contributors, 16,000+ PRs, rebuilt browser app, multiplayer cloud
  sessions. Works with existing Claude/ChatGPT subscriptions, API keys or local models. It is for
  wiring agents across email, messaging and APIs.
- **Omarchy** (`omarchy.org`) — a Linux distribution from DHH, incubated at 37signals: *"the
  malleable OS for the age of agents."* Arch-based, ships as an ISO.

## Recommendation: **decline both, for this project**

Neither touches the thing that is actually slow.

- **Omarchy is an operating system.** Grassmarket builds on a headless Hetzner CX22 running Ubuntu
  and deploys to Railway containers. Replacing the OS on the build box changes nothing about
  FastAPI, Postgres, or a 15-minute pytest run, and it costs a rebuild of a working environment.
  Omarchy is a *desktop* distribution; this box has no desktop. If the founder wants it on their
  own Windows machine as a daily driver, that is a genuinely separate question with no bearing
  here.
- **OpenClaw is an agent platform**, and we already have one — Claude Code, in this repo, with the
  project's own skills and a tested workflow. Adding a second agent runtime to orchestrate the
  first is overhead, not leverage. Where OpenClaw would genuinely fit is *inside the product* —
  advisor-facing automation across email and calendar — and that overlaps GRS-0197
  (Gmail/Calendar) and GRS-0203 (outreach sequencer), which should be decided on their own merits.

## What would actually speed the build up

Named honestly, since the question was about performance:

1. **The 3 GB box.** `oom-kills-on-3gb-hetzner-box` is a recurring session-killer. A rescale is
   ~£10/month and needs the founder. This is the single biggest real constraint.
2. **The 15-minute backend suite.** `pytest -n auto` (pytest-xdist) is a one-line dependency and
   would cut the loop that gates every merge.
3. **The founder-gated items.** GRS-0150, Commission Schedule v7, the ASX pack. No tool moves these.

## Done when

The founder says yes or no. If no, close as declined and record why, so it is not re-asked.
