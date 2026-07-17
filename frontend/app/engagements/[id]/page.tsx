/**
 * Engagement detail (GRS-0014): the linked assessments, the deliverables-progress shell (Loop 4
 * fills the content), and the append-only communication log in chronological order — plus a form to
 * add a comms entry.
 */

"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

import { ApiError, api, clearToken, getToken } from "@/lib/api";
import {
  COMMS_CHANNELS,
  type BrokeragePortfolioEntry,
  type CommsChannel,
  type Engagement,
} from "@/lib/types";
import { DeliverablesPanel } from "@/components/DeliverablesPanel";
import { LinkAssessmentControl } from "@/components/LinkAssessmentControl";
import { Breadcrumb } from "@/components/Breadcrumb";

const STATE_LABEL: Record<string, string> = {
  draft: "Draft",
  in_progress: "In progress",
  finalised: "Finalised",
};

function LinkedAssessment({ id, index, entry }: { id: string; index: number; entry?: BrokeragePortfolioEntry }) {
  const subject = entry?.subject ?? `Assessment ${index + 1}`;
  const v = entry?.v_index != null ? Math.round(entry.v_index * 100) : null;
  const coverage = entry?.coverage != null ? Math.round(entry.coverage * 100) : null;
  const updated = entry ? new Date(entry.updated_at).toLocaleDateString() : null;
  return (
    <Link href={`/assessments/${id}`} className="card-link" style={{ padding: "0.9rem 1.1rem", display: "block" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.75rem", flexWrap: "wrap" }}>
        <span style={{ fontWeight: 600 }}>{subject}</span>
        <span aria-hidden className="mono" style={{ color: "var(--color-ink-faint)", fontSize: "0.8rem" }}>Open →</span>
      </div>
      <div style={{ display: "flex", gap: "0.5rem 1.1rem", flexWrap: "wrap", marginTop: "0.45rem", fontSize: "0.82rem", color: "var(--color-ink-muted)" }}>
        {entry ? <span className="tag" style={{ fontSize: "0.66rem" }}>{STATE_LABEL[entry.state] ?? entry.state}</span> : null}
        {v != null ? (
          <span>
            V <strong style={{ color: "var(--color-ink)" }}>{v}</strong>
            {entry?.uncertainty_rating ? ` · ${entry.uncertainty_rating}` : ""}
          </span>
        ) : (
          <span>Not yet finalised</span>
        )}
        {coverage != null ? <span>Coverage <strong style={{ color: "var(--color-ink)" }}>{coverage}%</strong></span> : null}
        {updated ? <span>Updated {updated}</span> : null}
      </div>
    </Link>
  );
}

export default function EngagementDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [portfolio, setPortfolio] = useState<BrokeragePortfolioEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(
    (signal?: AbortSignal) =>
      api
        .getEngagement(id, signal)
        .then(setEngagement)
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0) return;
          if (err instanceof ApiError && err.status === 401) {
            clearToken();
            return router.replace("/login");
          }
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
    // The lightweight portfolio summary gives each linked assessment its live state (V, coverage,
    // status) without a per-assessment fetch (GRS-0116). A failure here is non-fatal — the links
    // still work, they just show less state.
    api.brokeragePortfolio(ctrl.signal).then(setPortfolio).catch(() => {});
    return () => ctrl.abort();
  }, [router, reload]);

  if (error) return <p style={{ color: "var(--color-error)" }}>{error}</p>;
  if (!engagement) return <p>Loading…</p>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem", maxWidth: "48rem" }}>
      <div>
        <Breadcrumb
          trail={[
            { label: "Pipeline", href: "/pipeline" },
            { label: "Prospect", href: `/prospects/${engagement.prospect_id}` },
          ]}
          current={engagement.title}
        />
        <p className="eyebrow" style={{ marginTop: "0.5rem" }}>
          Engagement
        </p>
        <h1 style={{ fontSize: "1.7rem", margin: "0.3rem 0 0.5rem" }}>{engagement.title}</h1>
        <span className="tag">{engagement.status}</span>
      </div>

      <section>
        <h2 style={{ fontSize: "1.1rem", marginBottom: "0.3rem" }}>Assessment</h2>
        <p style={{ margin: "0 0 0.7rem", color: "var(--color-ink-muted)", fontSize: "0.85rem", maxWidth: "34rem" }}>
          This engagement is delivered <em>from</em> a Platform Power assessment — the scored analysis of
          the client&rsquo;s platform. The deliverables below are generated from it once it is finalised.
        </p>
        {engagement.assessment_ids.length === 0 ? (
          <div className="card" style={{ padding: "1.1rem 1.25rem", display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
            <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "0.9rem", maxWidth: "30rem" }}>
              No assessment yet. Start a Platform Power assessment for{" "}
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
                <LinkedAssessment
                  id={aid}
                  index={i}
                  entry={portfolio.find((p) => p.assessment_id === aid)}
                />
              </li>
            ))}
          </ul>
        )}
        <LinkAssessmentControl engagement={engagement} onLinked={reload} />
      </section>

      <DeliverablesPanel engagementId={id} />

      <CommsLog engagement={engagement} onAdded={reload} />
    </div>
  );
}

// Link an already-finalised assessment to this engagement (GRS-0039). Offers the advisor's own
// finalised assessments that aren't linked here yet — closing the contract -> assessment ->
// deliverable loop that engagement-open alone couldn't (assessment_ids was create-time only).
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
        <select aria-label="Channel" value={channel} onChange={(e) => setChannel(e.target.value as CommsChannel)} style={inputStyle}>
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
