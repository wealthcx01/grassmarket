/**
 * "Your Brokerages" — the advisor's portfolio home (GRS-0071). One row per assessment (server-scoped
 * by JWT): the business, its segment, its last finalised Platform Value, status, and when it was last
 * touched. Create a new one or resume a draft — a partial assessment is valid and autosaves.
 */

"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { toDisplay } from "@/lib/band";
import { ApiError, api, getToken } from "@/lib/api";
import type { BrokeragePortfolioEntry } from "@/lib/types";

const STATE_LABEL: Record<BrokeragePortfolioEntry["state"], string> = {
  draft: "Draft",
  in_progress: "In progress",
  finalised: "Finalised · locked",
};

function LastScore({ entry }: { entry: BrokeragePortfolioEntry }) {
  if (entry.v_index == null) {
    return <span style={{ color: "var(--color-ink-faint)" }}>—</span>;
  }
  return (
    <span style={{ display: "inline-flex", alignItems: "baseline", gap: "0.4rem" }}>
      <strong className="mono">{toDisplay(entry.v_index).toFixed(1)}</strong>
      {entry.uncertainty_rating ? (
        <span className="tag" title="Overall uncertainty of the finalised score">
          {entry.uncertainty_rating}
        </span>
      ) : null}
    </span>
  );
}

export default function BrokeragesPage() {
  const router = useRouter();
  const [items, setItems] = useState<BrokeragePortfolioEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [subject, setSubject] = useState("");
  const [sandbox, setSandbox] = useState(false);
  const [creating, setCreating] = useState(false);

  // Prefill the subject when arriving from an engagement's "Start an assessment" CTA (?subject=…).
  useEffect(() => {
    const s = new URLSearchParams(window.location.search).get("subject");
    if (s) setSubject(s);
  }, []);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    api
      .brokeragePortfolio(ctrl.signal)
      .then(setItems)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0) return;
        if (err instanceof ApiError && err.status === 401) return router.replace("/login");
        setError(err instanceof ApiError ? err.message : "Could not load your brokerages.");
      });
    return () => ctrl.abort();
  }, [router]);

  async function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!subject.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const created = await api.createAssessment(subject.trim(), sandbox ? "sandbox" : "production");
      router.push(`/assessments/${created.id}`);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not create the assessment.");
      setCreating(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      <section>
        <p className="eyebrow" style={{ margin: 0 }}>
          Platform Power · Path A (manual)
        </p>
        <h1 style={{ fontSize: "2rem", margin: "0.3rem 0 0.4rem" }}>Your Brokerages</h1>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", maxWidth: "40rem" }}>
          Your portfolio of assessments. Start a new one or resume a draft — a partial assessment is
          valid and autosaves. A score appears once the assessment is finalised.
        </p>
      </section>

      <form
        onSubmit={onCreate}
        style={{ display: "flex", gap: "0.5rem", alignItems: "flex-end", flexWrap: "wrap" }}
      >
        <label style={{ fontSize: "0.85rem", flex: "1 1 20rem" }}>
          <span style={{ display: "block", marginBottom: "0.3rem", fontWeight: 500 }}>
            New brokerage — subject (business name)
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
        <button type="submit" className="btn btn-primary" disabled={creating || !subject.trim()}>
          {creating ? "Creating…" : "Create & open"}
        </button>
        <label
          title="A sandbox assessment can be finalised solo (no co-rater or committee) so you can see the real deliverable drafts. It is watermarked and never client-facing."
          style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem", fontSize: "0.82rem", color: "var(--color-ink-muted)", paddingBottom: "0.55rem" }}
        >
          <input type="checkbox" checked={sandbox} onChange={(e) => setSandbox(e.target.checked)} />
          Sandbox (self-approve, non-production)
        </label>
      </form>

      {error ? (
        <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.9rem" }}>
          {error}
        </p>
      ) : null}

      <section>
        <h2 style={{ fontSize: "1.05rem", marginBottom: "1rem" }}>Portfolio</h2>
        {items === null ? (
          <p style={{ color: "var(--color-ink-muted)" }}>Loading…</p>
        ) : items.length === 0 ? (
          <p style={{ color: "var(--color-ink-muted)" }}>
            No brokerages yet. Create one above to begin.
          </p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.88rem" }}>
              <thead>
                <tr style={{ textAlign: "left", color: "var(--color-ink-muted)", fontSize: "0.78rem" }}>
                  <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }}>Brokerage</th>
                  <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }}>Segment</th>
                  <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }} title="Last finalised Platform Value (0–100)">
                    Last score
                  </th>
                  <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }}>Status</th>
                  <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }}>Last updated</th>
                </tr>
              </thead>
              <tbody>
                {items.map((e) => (
                  <tr key={e.assessment_id} style={{ borderTop: "1px solid var(--color-border)" }}>
                    <td style={{ padding: "0.55rem 0.6rem" }}>
                      <Link
                        href={`/assessments/${e.assessment_id}`}
                        style={{ fontFamily: "var(--font-serif)", fontWeight: 600, color: "inherit", textDecoration: "none" }}
                      >
                        {e.subject || "Untitled"}
                      </Link>
                    </td>
                    <td style={{ padding: "0.55rem 0.6rem", color: e.segment ? "inherit" : "var(--color-ink-faint)" }}>
                      {e.segment ?? "—"}
                    </td>
                    <td style={{ padding: "0.55rem 0.6rem" }}>
                      <LastScore entry={e} />
                    </td>
                    <td style={{ padding: "0.55rem 0.6rem" }}>
                      <span
                        className="mono"
                        style={{
                          fontSize: "0.7rem",
                          color: e.state === "finalised" ? "var(--color-accent)" : "var(--color-ink-muted)",
                        }}
                      >
                        {STATE_LABEL[e.state]}
                      </span>
                    </td>
                    <td className="mono" style={{ padding: "0.55rem 0.6rem", fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>
                      {new Date(e.updated_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <footer style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        <Link href="/">← Back to dashboard</Link>
      </footer>
    </div>
  );
}
