# GRS-0252 — Supabase: evaluated, recommend declining

**Status:** OPEN (2026-09-02) — decision ticket, no build. **Priority:** LOW. **Type:** Infrastructure decision.
**Founder question:** 2026-09-02 — *"do we need a Supabase database to support this or will our Postgres do fine?"*
**Relates to:** GRS-0247 (document storage), non-negotiable #5.

## Short answer

**Our Postgres does fine. Supabase is not needed and would cost more than it returns here.**

## What we run today

PostgreSQL on Railway, two environments (production + staging), both live. 47 tables, Alembic
migrations through `0042`, all access through `src/grassmarket/data/repository.py` per
non-negotiable #5, per-consultant scoping enforced there and tested. Production `/health/ready`
pings the database and was green on 2026-09-02. Nothing about the current storage layer is
constraining any open ticket.

## What Supabase would add, and whether we want it

| Supabase gives | Our position |
|---|---|
| **Managed Postgres** | We have managed Postgres. Migrating hosts is work with no functional gain. |
| **Auth** (GoTrue) | We have our own: JWT shaped to Holy Corner's future claim structure, Google OAuth, Workspace domain SSO (ADR-0044), invite flow. Adopting Supabase auth means **rewriting the thing that already works** and abandoning the Holy Corner claim shape — the specific reason ours is shaped as it is. |
| **Storage** (S3-backed blobs) | **The one genuinely attractive piece**, and the only real argument for Supabase. It would give GRS-0247 a blob store for free. |
| **Realtime** | No current requirement. |
| **Studio / dashboard** | Nice; not worth a migration. |

## Why Storage does not carry the decision

GRS-0247 needs somewhere to put client documents. Supabase Storage would do it. So would:

- **Postgres `LargeBinary`** — zero new infrastructure, reuses the Fernet encryption already
  written for transcripts, and keeps every byte behind the repository layer. The recommendation in
  GRS-0247, with a hard per-file cap.
- **A Railway volume** — also zero new vendors.

Adopting a second backing service, a second auth system and a second place for non-negotiable #9
to be got wrong, in order to avoid writing one table, is the wrong trade.

## The local-development problem, which is decisive

The founder's link was `supabase.com/docs/guides/local-development`. That flow runs the full
Supabase stack locally in **Docker** — Postgres, GoTrue, PostgREST, Realtime, Storage, Studio,
Kong. That is several containers and well over a gigabyte of resident memory.

**This build box is a Hetzner CX22: 2 vCPU, ~3 GB RAM, no swap, with a RAM-backed `/tmp`.** OOM
kills already end sessions mid-task (see `oom-kills-on-3gb-hetzner-box`), and the backend test
suite alone takes 15 minutes. Running the Supabase stack alongside it would make the box unusable.

Our current local story is `sqlite+pysqlite:///:memory:` for tests and Railway Postgres for real
environments. It is fast, it needs no daemon, and 1,798 tests run against it.

## If it is adopted anyway

Should the founder want Supabase for reasons beyond this repo — one platform across Bruntsfield
projects, say, which is a legitimate reason this ticket cannot weigh — then:

1. **Use it as Postgres only.** Point `GM_DATABASE_URL` at the Supabase connection string. Alembic,
   SQLAlchemy and the repository layer do not care. This is genuinely a one-line change and is
   reversible.
2. **Do not adopt Supabase Auth.** It would replace working, tested, Holy-Corner-shaped auth.
3. **Storage is worth revisiting at that point** for GRS-0247, since the dependency would already
   be paid for.
4. **Do not run the local stack on this box.** Develop against the hosted project or keep SQLite.

The CLI is connected to the founder's `wealthcx` GitHub account, so step 1 is available whenever
wanted.

## Done when

The founder says yes or no. **Recommendation: no** — keep Railway Postgres, and give GRS-0247 a
`documents` table rather than a new vendor.
