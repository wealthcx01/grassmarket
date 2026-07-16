"use client";

import { useEffect, useState } from "react";

import { getSession, type Session } from "@/lib/session";

/**
 * Profile page (GRS-0087). A minimal, honest surface reachable from the header account menu: it
 * confirms who you are signed in as (from the client session — no re-fetch). Richer profile editing
 * (name, photo, credentials) is a later Part-2 ticket; this is the destination the menu links to so
 * there is no dead link.
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
    </div>
  );
}
