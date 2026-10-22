# GRS-0283 — Change the transcript encryption key without losing a transcript

**Status:** OPEN (filed 2026-10-22). **Priority:** HIGH. **Type:** Security.
**Raised by:** John, 22 October 2026, after Railway's security disclosure (cowgate CG-0042).

## Why

Railway cancelled every API token on 22 October 2026 and asked everyone to change the secrets
they keep there. `GM_TRANSCRIPT_ENCRYPTION_KEY` is one of them. It can't simply be replaced,
because grassmarket encrypts with one Fernet key (`src/grassmarket/pathb/cipher.py`). Every
stored transcript (`meeting_transcripts.text_ciphertext`) and document
(`documents.content_ciphertext`) opens only with that key. A new key alone would make all of them
unreadable, and `docs/ops/RUNBOOK.md` says not to change it without re-encrypting. So
`cowgate railway rotate` leaves this key alone, and this ticket does it safely.

## What to do, in order

**a. The code reads two keys.** `config.py` reads:
- `GM_TRANSCRIPT_ENCRYPTION_KEY`: new writes use it.
- an optional `GM_TRANSCRIPT_ENCRYPTION_KEY_PREVIOUS`: used only to read.

The cipher uses `MultiFernet([new, previous])` from the same `cryptography` library. In
production, start-up refuses a PREVIOUS key that equals the main key, or that isn't a valid
Fernet key. Ship this with the old key as the main key and no PREVIOUS, so nothing changes yet.

**b. Back up the database.**
- Take a Railway backup of grassmarket's production Postgres.
- Also take a `pg_dump`, kept off Railway.
- Restore the dump into a scratch database to prove it works.

**c. Switch keys.**
- Set PREVIOUS to the old key, and the main key to a new `Fernet.generate_key()`.
- Redeploy `grassmarket-api`.

New transcripts now use the new key, and old ones still open. Do the same on staging first, with
staging's own keys.

**d. Re-encrypt, then check.** A one-off command, `uv run python -m grassmarket.ops.rekey`:
- works through both columns in batches of 500, each batch in its own transaction;
- uses `MultiFernet.rotate`, which keeps each value's original timestamp;
- is safe to run twice;
- prints counts only.

It finishes by opening every row with the new key alone, and exits non-zero if any row fails.

**e. Drop the old key.**
- Remove `GM_TRANSCRIPT_ENCRYPTION_KEY_PREVIOUS` and redeploy.
- Run `scripts/prod_smoke.py`, and open one real transcript in the app.
- Then destroy every copy of the old key, including any password-manager entry.

## Acceptance

- [ ] With both keys set, a value encrypted with either key opens. New values use the new key.
- [ ] Production refuses to start when PREVIOUS equals the main key, or isn't a Fernet key.
- [ ] The re-encrypt command is tested on a test database. After it, every row opens with the new
      key alone. Run twice, it changes nothing the second time. It never prints text or a key.
- [ ] `docs/ops/RUNBOOK.md` gets steps a to e as the way to change this key.
- [ ] Every check in `CLAUDE.md` passes.

## Out of scope

- Steps b, c and e themselves are John's, on Railway. This ticket ships the code (a, d) and the
  runbook. Doing them is a separate sitting.
- What it can't undo: a copy of the database taken while the old key was exposed can still be
  read with that key. Re-encrypting protects what is stored from now on.
