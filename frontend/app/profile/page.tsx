"use client";

import { useEffect, useState, type FormEvent } from "react";

import { ApiError, api } from "@/lib/api";
import { getSession, type Session } from "@/lib/session";

/**
 * Profile page (GRS-0087; change-password GRS-0148d). Confirms who you are signed in as (from the
 * client session) and lets you rotate your own password — the one account control a compliance-
 * minded advisor expects. Richer editing (name, photo) is a later ticket.
 */
export default function ProfilePage() {
  const [session, setSession] = useState<Session | null | undefined>(undefined);
  useEffect(() => setSession(getSession()), []);

  return (
    <div className="stack" style={{ gap: "1.5rem", maxWidth: "38rem" }}>
      <div>
        <p className="eyebrow">Account</p>
        <h1 style={{ margin: "0.4rem 0 0.4rem" }}>Profile</h1>
        <p style={{ margin: 0, color: "var(--color-ink-muted)" }}>
          Your account identity. Editing your name and credentials is coming soon.
        </p>
      </div>
      <div className="card" style={{ padding: "1.25rem 1.35rem" }}>
        <dl style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "0.5rem 1.5rem", margin: 0 }}>
          <dt style={{ color: "var(--color-ink-soft)", fontSize: "0.85rem" }}>Email</dt>
          <dd style={{ margin: 0, fontSize: "0.9rem" }}>{session?.email ?? "—"}</dd>
          <dt style={{ color: "var(--color-ink-soft)", fontSize: "0.85rem" }}>Role</dt>
          <dd style={{ margin: 0, fontSize: "0.9rem", textTransform: "capitalize" }}>
            {session ? session.role.replace(/_/g, " ") : "—"}
          </dd>
          <dt style={{ color: "var(--color-ink-soft)", fontSize: "0.85rem" }}>Assessor level</dt>
          <dd style={{ margin: 0, fontSize: "0.9rem", textTransform: "capitalize" }}>
            {session ? session.assessorLevel.replace(/_/g, " ") : "—"}
          </dd>
        </dl>
      </div>

      <ChangePasswordCard />
    </div>
  );
}

function ChangePasswordCard() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const tooShort = next.length > 0 && next.length < 12;
  const mismatch = confirm.length > 0 && confirm !== next;
  const canSubmit = !!current && next.length >= 12 && next === confirm && !busy;

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setDone(false);
    try {
      await api.changePassword(current, next);
      setDone(true);
      setCurrent("");
      setNext("");
      setConfirm("");
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not change your password.");
    } finally {
      setBusy(false);
    }
  }

  const field: React.CSSProperties = {
    display: "block",
    width: "100%",
    marginTop: "0.3rem",
    padding: "0.5rem 0.7rem",
    fontFamily: "inherit",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius)",
    background: "var(--color-paper-raised)",
  };
  const label: React.CSSProperties = { fontSize: "0.85rem", display: "block" };

  return (
    <div className="card" style={{ padding: "1.25rem 1.35rem" }}>
      <h2 style={{ margin: "0 0 0.3rem", fontSize: "1.05rem" }}>Change password</h2>
      <p style={{ margin: "0 0 0.9rem", color: "var(--color-ink-muted)", fontSize: "0.82rem" }}>
        Choose a new password of at least 12 characters. You&rsquo;ll stay signed in on this device.
      </p>
      <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: "0.7rem" }}>
        <label style={label}>
          Current password
          <input
            type="password"
            autoComplete="current-password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            style={field}
          />
        </label>
        <label style={label}>
          New password
          <input
            type="password"
            autoComplete="new-password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            style={field}
          />
          {tooShort ? (
            <span style={{ color: "var(--color-warn)", fontSize: "0.72rem" }}>
              At least 12 characters.
            </span>
          ) : null}
        </label>
        <label style={label}>
          Confirm new password
          <input
            type="password"
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            style={field}
          />
          {mismatch ? (
            <span style={{ color: "var(--color-warn)", fontSize: "0.72rem" }}>
              Passwords don&rsquo;t match.
            </span>
          ) : null}
        </label>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <button type="submit" className="btn btn-primary" disabled={!canSubmit}>
            {busy ? "Saving…" : "Update password"}
          </button>
          {done ? (
            <span role="status" style={{ color: "var(--color-accent)", fontSize: "0.82rem" }}>
              Password updated.
            </span>
          ) : null}
        </div>
        {error ? (
          <p role="alert" style={{ margin: 0, color: "var(--color-error)", fontSize: "0.82rem" }}>
            {error}
          </p>
        ) : null}
      </form>
    </div>
  );
}
