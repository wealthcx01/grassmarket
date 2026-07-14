/**
 * Engagement detail (GRS-0014): the linked assessments, the deliverables-progress shell (Loop 4
 * fills the content), and the append-only communication log in chronological order — plus a form to
 * add a comms entry.
 */

"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

import { ApiError, api, getToken } from "@/lib/api";
import { COMMS_CHANNELS, type CommsChannel, type Engagement } from "@/lib/types";
import { DeliverablesPanel } from "@/components/DeliverablesPanel";

export default function EngagementDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(
    (signal?: AbortSignal) =>
      api
        .getEngagement(id, signal)
        .then(setEngagement)
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0) return;
          if (err instanceof ApiError && err.status === 404) return router.replace("/engagements");
          setError(err instanceof ApiError ? err.message : "Could not load the engagement.");
        }),
    [id, router],
  );

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    reload(ctrl.signal);
    return () => ctrl.abort();
  }, [router, reload]);

  if (error) return <p style={{ color: "var(--color-error)" }}>{error}</p>;
  if (!engagement) return <p>Loading…</p>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem", maxWidth: "48rem" }}>
      <div>
        <Link href={`/prospects/${engagement.prospect_id}`} style={{ fontSize: "0.82rem" }}>
          ← Prospect
        </Link>
        <p className="eyebrow" style={{ marginTop: "0.5rem" }}>
          Engagement
        </p>
        <h1 style={{ fontSize: "1.7rem", margin: "0.3rem 0 0.5rem" }}>{engagement.title}</h1>
        <span className="tag">{engagement.status}</span>
      </div>

      <section>
        <h2 style={{ fontSize: "1.1rem", marginBottom: "0.6rem" }}>Assessments</h2>
        {engagement.assessment_ids.length === 0 ? (
          <div className="card" style={{ padding: "1.1rem 1.25rem", display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
            <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "0.9rem", maxWidth: "30rem" }}>
              No assessment yet. Start an ATLAS assessment for{" "}
              <strong style={{ color: "var(--color-ink)" }}>{engagement.title}</strong> — the deliverables
              below generate from it once it&rsquo;s finalised.
            </p>
            <Link
              href={`/assessments?subject=${encodeURIComponent(engagement.title)}`}
              className="btn btn-primary"
            >
              Start an assessment →
            </Link>
          </div>
        ) : (
          <ul className="stack" style={{ listStyle: "none", margin: 0, padding: 0, gap: "0.5rem" }}>
            {engagement.assessment_ids.map((aid, i) => (
              <li key={aid}>
                <Link href={`/assessments/${aid}`} className="card-link" style={{ padding: "0.8rem 1rem", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.5rem" }}>
                  <span style={{ fontWeight: 500 }}>Assessment {i + 1}</span>
                  <span aria-hidden className="mono" style={{ color: "var(--color-ink-faint)" }}>
                    Open →
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <DeliverablesPanel engagementId={id} />

      <CommsLog engagement={engagement} onAdded={reload} />
    </div>
  );
}

function CommsLog({ engagement, onAdded }: { engagement: Engagement; onAdded: () => Promise<unknown> }) {
  const [channel, setChannel] = useState<CommsChannel>("note");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function add(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!body.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api.appendComms(engagement.id, { channel, body: body.trim() });
      setBody("");
      await onAdded();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not add the entry.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h2 style={{ fontSize: "1.05rem", marginBottom: "0.4rem" }}>Communication log</h2>
      {engagement.comms_log.length === 0 ? (
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>No entries yet.</p>
      ) : (
        <ol style={{ listStyle: "none", padding: 0, margin: "0 0 0.75rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
          {engagement.comms_log.map((entry) => (
            <li key={entry.id} style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius)", padding: "0.5rem 0.7rem", background: "var(--color-paper-raised)" }}>
              <div className="mono" style={{ fontSize: "0.68rem", color: "var(--color-ink-muted)" }}>
                {new Date(entry.at).toLocaleString()} · {entry.channel}
              </div>
              <div style={{ fontSize: "0.88rem", marginTop: "0.2rem", whiteSpace: "pre-wrap" }}>{entry.body}</div>
            </li>
          ))}
        </ol>
      )}
      <form onSubmit={add} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "flex-start" }}>
        <select value={channel} onChange={(e) => setChannel(e.target.value as CommsChannel)} style={inputStyle}>
          {COMMS_CHANNELS.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <input type="text" value={body} onChange={(e) => setBody(e.target.value)} placeholder="Log a communication…" style={{ ...inputStyle, flex: "1 1 18rem" }} />
        <button type="submit" className="btn btn-primary" disabled={busy || !body.trim()}>
          Add entry
        </button>
      </form>
      {error ? <p style={{ color: "var(--color-error)", fontSize: "0.8rem" }}>{error}</p> : null}
    </section>
  );
}

// Controls inherit the global form styling; we only nudge the size for this dense log.
const inputStyle: React.CSSProperties = {
  fontSize: "0.85rem",
};
