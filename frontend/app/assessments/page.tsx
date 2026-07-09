/**
 * Assessments index (GRS-0010) — the consultant's own assessments (server-scoped by JWT) plus a
 * "New assessment" create. Resume is a click through to the wizard. A partial draft is valid, so
 * everything here is listed regardless of state.
 */

"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { ApiError, api, getToken } from "@/lib/api";
import type { Assessment } from "@/lib/types";

const STATE_LABEL: Record<Assessment["state"], string> = {
  draft: "Draft",
  in_progress: "In progress",
  finalised: "Finalised · locked",
};

export default function AssessmentsPage() {
  const router = useRouter();
  const [items, setItems] = useState<Assessment[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [subject, setSubject] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    api
      .listAssessments(ctrl.signal)
      .then(setItems)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0) return;
        if (err instanceof ApiError && err.status === 401) return router.replace("/login");
        setError(err instanceof ApiError ? err.message : "Could not load assessments.");
      });
    return () => ctrl.abort();
  }, [router]);

  async function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!subject.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const created = await api.createAssessment(subject.trim());
      router.push(`/assessments/${created.id}`);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not create the assessment.");
      setCreating(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      <section>
        <p
          className="mono"
          style={{ margin: 0, fontSize: "0.72rem", letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--color-ink-muted)" }}
        >
          ATLAS · Path A (manual)
        </p>
        <h1 style={{ fontSize: "2rem", margin: "0.3rem 0 0.4rem" }}>Assessments</h1>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", maxWidth: "38rem" }}>
          Your assessments only. Start a new one or resume a draft — a partial assessment is valid and
          autosaves as you go.
        </p>
      </section>

      <form
        onSubmit={onCreate}
        style={{ display: "flex", gap: "0.5rem", alignItems: "flex-end", flexWrap: "wrap" }}
      >
        <label style={{ fontSize: "0.85rem", flex: "1 1 20rem" }}>
          <span style={{ display: "block", marginBottom: "0.3rem", fontWeight: 500 }}>
            New assessment — subject (business name)
          </span>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="e.g. Meridian Capital Partners"
            style={{
              width: "100%",
              padding: "0.55rem 0.7rem",
              fontFamily: "inherit",
              fontSize: "0.95rem",
              color: "var(--color-ink)",
              background: "var(--color-paper-raised)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius)",
            }}
          />
        </label>
        <button
          type="submit"
          disabled={creating || !subject.trim()}
          style={{
            padding: "0.6rem 1.2rem",
            fontSize: "0.9rem",
            fontWeight: 500,
            color: "var(--color-accent-contrast)",
            background: "var(--color-accent)",
            border: "none",
            borderRadius: "var(--radius)",
            cursor: creating || !subject.trim() ? "not-allowed" : "pointer",
            opacity: creating || !subject.trim() ? 0.6 : 1,
          }}
        >
          {creating ? "Creating…" : "Create & open"}
        </button>
      </form>

      {error ? (
        <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.9rem" }}>
          {error}
        </p>
      ) : null}

      <section>
        <h2 style={{ fontSize: "1.05rem", marginBottom: "1rem" }}>Your assessments</h2>
        {items === null ? (
          <p style={{ color: "var(--color-ink-muted)" }}>Loading…</p>
        ) : items.length === 0 ? (
          <p style={{ color: "var(--color-ink-muted)" }}>
            No assessments yet. Create one above to begin.
          </p>
        ) : (
          <ul
            style={{
              listStyle: "none",
              margin: 0,
              padding: 0,
              display: "grid",
              gap: "0.75rem",
              gridTemplateColumns: "repeat(auto-fill, minmax(18rem, 1fr))",
            }}
          >
            {items.map((a) => (
              <li key={a.id}>
                <Link
                  href={`/assessments/${a.id}`}
                  style={{
                    display: "block",
                    height: "100%",
                    padding: "0.9rem 1rem",
                    background: "var(--color-paper-raised)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius)",
                    textDecoration: "none",
                    color: "inherit",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.5rem" }}>
                    <span style={{ fontFamily: "var(--font-serif)", fontWeight: 600, fontSize: "1.05rem" }}>
                      {a.subject || "Untitled"}
                    </span>
                    <span
                      className="mono"
                      style={{
                        fontSize: "0.62rem",
                        color: a.state === "finalised" ? "var(--color-accent)" : "var(--color-ink-muted)",
                      }}
                    >
                      {STATE_LABEL[a.state]}
                    </span>
                  </div>
                  <p style={{ margin: "0.4rem 0 0", fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
                    Updated {new Date(a.updated_at).toLocaleString()}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <footer style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        <Link href="/">← Back to dashboard</Link>
      </footer>
    </div>
  );
}
