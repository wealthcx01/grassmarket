/**
 * DeliverablesPanel (GRS-0019) — the per-engagement deliverable library: generate a document
 * (internal draft or client-facing), list what exists (type / mode / status / generated-at), and
 * download the regenerated .docx.
 *
 * Gate refusals are shown as the backend's plain-English message, not a technical error: a
 * client-facing generation on a draft coefficient set is refused (409), and a type with its own
 * render path (roadmap / score evolution) is refused (422). Scoping is server-side; a 404 means the
 * engagement is not the advisor's and the caller has already been redirected.
 */

import { Fragment, useCallback, useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import type {
  AINarrative,
  Deliverable,
  DeliverableMode,
  DeliverableType,
  RecordProvenance,
} from "@/lib/types";
import { NarrativeReview } from "@/components/NarrativeReview";
import { ProvenanceBadge } from "@/components/ProvenanceBadge";

interface NarrativeSummary {
  total: number;
  approved: number;
  pending: number;
}

function summariseNarratives(narratives: AINarrative[]): NarrativeSummary {
  const approved = narratives.filter((n) => n.status === "approved").length;
  const pending = narratives.filter((n) => n.status !== "approved").length;
  return { total: narratives.length, approved, pending };
}

const TYPE_LABEL: Record<DeliverableType, string> = {
  executive_summary: "Executive Summary",
  platform_power_report: "Platform Power Report",
  infrastructure_heatmap: "Infrastructure Heatmap",
  modernisation_roadmap: "Modernisation Roadmap",
  technical_appendix: "Technical Appendix",
  workshop_output: "Workshop Output",
  score_evolution: "Score Evolution",
};

// The single-run types the generate endpoint accepts; the roadmap (needs the value bridge) and
// score evolution (needs multiple runs) have their own paths and are not offered here.
const GENERATABLE: DeliverableType[] = [
  "executive_summary",
  "platform_power_report",
  "infrastructure_heatmap",
  "technical_appendix",
  "workshop_output",
];

function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function formatWhen(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "—" : d.toISOString().slice(0, 16).replace("T", " ");
}

export function DeliverablesPanel({
  engagementId,
  provenance,
}: {
  engagementId: string;
  provenance?: RecordProvenance;
}) {
  const [items, setItems] = useState<Deliverable[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [type, setType] = useState<DeliverableType>("platform_power_report");
  const [clientFacing, setClientFacing] = useState(false);
  const [busy, setBusy] = useState(false);
  // A client-facing document leaves the building — generating one goes through an explicit review
  // step first (proportional friction, rubric #8). Internal drafts generate immediately.
  const [confirmingClient, setConfirmingClient] = useState(false);
  const [notice, setNotice] = useState<{ kind: "error" | "ok"; text: string } | null>(null);
  const [reviewing, setReviewing] = useState<string | null>(null);
  // Per-deliverable AI-narrative approval status — drives the "not client-ready" gate + the queue.
  const [narr, setNarr] = useState<Record<string, NarrativeSummary>>({});

  const reload = useCallback(
    async (signal?: AbortSignal) => {
      try {
        const list = await api.listDeliverables(engagementId, signal);
        setItems(list);
        // Fetch each deliverable's narrative status so the review gate + approval queue are visible.
        const summaries = await Promise.all(
          list.map(async (d): Promise<[string, NarrativeSummary]> => {
            try {
              return [d.id, summariseNarratives(await api.listNarratives(d.id, signal))];
            } catch {
              return [d.id, { total: 0, approved: 0, pending: 0 }];
            }
          }),
        );
        setNarr(Object.fromEntries(summaries));
      } catch (err) {
        if (err instanceof ApiError && err.status === 0) return; // backend unreachable
        setLoadError(err instanceof ApiError ? err.message : "Could not load deliverables.");
      }
    },
    [engagementId],
  );

  useEffect(() => {
    const ctrl = new AbortController();
    void reload(ctrl.signal);
    return () => ctrl.abort();
  }, [reload]);

  // Internal drafts generate immediately; a client-facing document opens the review step first.
  function onGenerateClick() {
    setNotice(null);
    if (clientFacing) setConfirmingClient(true);
    else void generate();
  }

  async function generate() {
    setBusy(true);
    setNotice(null);
    try {
      const created = await api.generateDeliverable(engagementId, {
        deliverable_type: type,
        client_facing: clientFacing,
      });
      setConfirmingClient(false);
      setNotice({ kind: "ok", text: `Generated ${TYPE_LABEL[created.type]} (${created.mode === "client" ? "client" : "internal draft"}).` });
      await reload();
    } catch (err) {
      // The gate refusals (409 draft-coefficients, 422 unsupported type) carry a plain-English
      // detail from the backend — show it verbatim rather than a status code.
      setNotice({
        kind: "error",
        text: err instanceof ApiError ? err.message : "Could not generate the deliverable.",
      });
    } finally {
      setBusy(false);
    }
  }

  async function download(d: Deliverable) {
    setNotice(null);
    try {
      const { blob, filename } = await api.downloadDeliverable(d.id, {
        clientFacing: d.mode === "client",
      });
      triggerBlobDownload(blob, filename);
    } catch (err) {
      setNotice({
        kind: "error",
        text: err instanceof ApiError ? err.message : "Could not download the document.",
      });
    }
  }

  return (
    <section
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        padding: "0.9rem 1rem",
        background: "var(--color-paper-raised)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.6rem", flexWrap: "wrap" }}>
        <span style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem" }}>
          <h2 style={{ fontSize: "1.05rem", margin: 0 }}>Deliverables</h2>
          {provenance ? <ProvenanceBadge provenance={provenance} /> : null}
        </span>
        <span className="mono" style={{ fontSize: "0.68rem", color: "var(--color-ink-muted)" }}>
          generated from the finalised assessment
        </span>
      </div>

      {/* Generate control */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.75rem",
          alignItems: "flex-end",
          margin: "0.8rem 0",
          paddingBottom: "0.8rem",
          borderBottom: "1px solid var(--color-border)",
        }}
      >
        <label style={{ display: "flex", flexDirection: "column", gap: "0.2rem", fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
          Document
          <select
            value={type}
            onChange={(e) => setType(e.target.value as DeliverableType)}
            aria-label="Deliverable type"
            style={selectStyle}
          >
            {GENERATABLE.map((t) => (
              <option key={t} value={t}>
                {TYPE_LABEL[t]}
              </option>
            ))}
          </select>
        </label>

        <fieldset style={{ border: 0, padding: 0, margin: 0, display: "flex", gap: "0.75rem" }}>
          <legend style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)", padding: 0, marginBottom: "0.2rem" }}>
            Audience
          </legend>
          <label style={radioStyle}>
            <input
              type="radio"
              name="audience"
              checked={!clientFacing}
              onChange={() => {
                setClientFacing(false);
                setConfirmingClient(false); // leaving client-facing cancels a pending review
              }}
            />
            Internal draft
          </label>
          <label style={radioStyle}>
            <input type="radio" name="audience" checked={clientFacing} onChange={() => setClientFacing(true)} />
            Client-facing
          </label>
        </fieldset>

        <button type="button" onClick={onGenerateClick} disabled={busy || confirmingClient} style={buttonStyle(busy || confirmingClient)}>
          {busy ? "Generating…" : clientFacing ? "Review & generate" : "Generate"}
        </button>
      </div>

      {confirmingClient && (
        <ClientReviewPanel
          documentLabel={TYPE_LABEL[type]}
          pending={Object.values(narr).reduce((s, x) => s + x.pending, 0)}
          busy={busy}
          onConfirm={() => void generate()}
          onCancel={() => setConfirmingClient(false)}
        />
      )}

      {notice && (
        <p
          role={notice.kind === "error" ? "alert" : undefined}
          style={{
            fontSize: "0.8rem",
            margin: "0 0 0.7rem",
            color: notice.kind === "error" ? "var(--color-error)" : "var(--color-accent)",
          }}
        >
          {notice.text}
        </p>
      )}

      {/* Approval queue — the review gate made visible: packs are not client-ready while any AI
          section is still awaiting sign-off. For junior-tier authors, senior review clears these. */}
      {(() => {
        const totalPending = Object.values(narr).reduce((s, x) => s + x.pending, 0);
        if (totalPending === 0) return null;
        return (
          <p
            style={{
              fontSize: "0.8rem",
              margin: "0 0 0.7rem",
              padding: "0.4rem 0.6rem",
              borderRadius: "var(--radius)",
              color: "var(--color-warn)",
              background: "rgba(138, 90, 0, 0.07)",
              border: "1px solid rgba(138, 90, 0, 0.25)",
            }}
          >
            {totalPending} AI section{totalPending === 1 ? "" : "s"} awaiting approval — the pack
            cannot be sent to a client until every section is approved.
          </p>
        );
      })()}

      {/* Library */}
      {loadError ? (
        <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.85rem" }}>{loadError}</p>
      ) : items === null ? (
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>Loading…</p>
      ) : items.length === 0 ? (
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>
          No deliverables generated yet.
        </p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
          <thead>
            <tr style={{ textAlign: "left", color: "var(--color-ink-muted)" }}>
              <th style={thStyle}>Document</th>
              <th style={thStyle}>Audience</th>
              <th style={thStyle}>Status</th>
              <th style={{ ...thStyle, textAlign: "right" }}>Generated</th>
              <th style={{ ...thStyle, textAlign: "right" }}></th>
            </tr>
          </thead>
          <tbody>
            {items.map((d) => (
              <Fragment key={d.id}>
                <tr style={{ borderTop: "1px solid var(--color-border)" }}>
                  <td style={tdStyle}>{d.title}</td>
                  <td style={tdStyle}>
                    <ModeBadge mode={d.mode} />
                  </td>
                  <td style={tdStyle}>
                    <NarrativeStatusCell summary={narr[d.id]} />
                  </td>
                  <td className="mono" style={{ ...tdStyle, textAlign: "right", fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
                    {formatWhen(d.generated_at)}
                  </td>
                  <td style={{ ...tdStyle, textAlign: "right", whiteSpace: "nowrap" }}>
                    <button
                      type="button"
                      onClick={() => setReviewing((cur) => (cur === d.id ? null : d.id))}
                      style={linkButtonStyle}
                      aria-expanded={reviewing === d.id}
                    >
                      {reviewing === d.id ? "Hide AI" : "Review AI"}
                    </button>
                    <span style={{ color: "var(--color-border)", margin: "0 0.5rem" }}>|</span>
                    <button type="button" onClick={() => void download(d)} style={linkButtonStyle}>
                      Download
                    </button>
                  </td>
                </tr>
                {reviewing === d.id && (
                  <tr>
                    <td colSpan={5} style={{ padding: "0 0.4rem 0.6rem" }}>
                      <NarrativeReview deliverableId={d.id} onNarrativesChanged={() => void reload()} />
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

/** The review-before-send step: a client-facing document can reach a client, so its generation is
 * confirmed explicitly against the release gates (rubric #8 — friction proportional to consequence). */
function ClientReviewPanel({
  documentLabel,
  pending,
  busy,
  onConfirm,
  onCancel,
}: {
  documentLabel: string;
  pending: number;
  busy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div
      role="group"
      aria-label="Review before generating a client-facing document"
      style={{
        margin: "0 0 0.8rem",
        padding: "0.9rem 1rem",
        borderRadius: "var(--radius)",
        border: "1px solid var(--color-accent)",
        background: "var(--color-accent-tint, rgba(26,59,38,0.06))",
      }}
    >
      <p className="eyebrow" style={{ margin: "0 0 0.35rem", color: "var(--color-accent)" }}>
        Review before it goes to the client
      </p>
      <p style={{ margin: "0 0 0.5rem", fontSize: "0.88rem" }}>
        You&rsquo;re about to generate the <strong>{documentLabel}</strong> as a{" "}
        <strong>client-facing</strong> document. A client-facing pack is only released when it uses
        ratified (client-usable) coefficients, every AI-drafted section is approved, and any
        high-stakes rating has committee sign-off — generation is refused if any gate is unmet.
      </p>
      {pending > 0 && (
        <p
          role="alert"
          style={{ margin: "0 0 0.5rem", fontSize: "0.82rem", color: "var(--color-warn)", fontWeight: 600 }}
        >
          {pending} AI section{pending === 1 ? "" : "s"} still await approval — approve them first, or
          this will be refused.
        </p>
      )}
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <button type="button" onClick={onConfirm} disabled={busy} style={buttonStyle(busy)}>
          {busy ? "Generating…" : "Generate client-facing document"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={busy}
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "0.85rem",
            padding: "0.4rem 0.9rem",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius)",
            background: "var(--color-paper)",
            color: "var(--color-ink)",
            cursor: busy ? "default" : "pointer",
          }}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function NarrativeStatusCell({ summary }: { summary?: NarrativeSummary }) {
  if (!summary || summary.total === 0) {
    return <span style={{ color: "var(--color-ink-muted)" }}>—</span>;
  }
  if (summary.pending === 0) {
    return <span style={{ color: "var(--color-accent)" }}>Client-ready</span>;
  }
  return (
    <span style={{ color: "var(--color-warn)" }}>
      {summary.pending} pending · {summary.approved}/{summary.total} approved
    </span>
  );
}

function ModeBadge({ mode }: { mode: DeliverableMode }) {
  const isClient = mode === "client";
  return (
    <span
      className="mono"
      style={{
        fontSize: "0.64rem",
        letterSpacing: "0.03em",
        textTransform: "uppercase",
        padding: "0.1rem 0.4rem",
        borderRadius: "2px",
        border: `1px solid ${isClient ? "var(--color-accent)" : "var(--color-border)"}`,
        color: isClient ? "var(--color-accent)" : "var(--color-warn)",
        background: isClient ? "transparent" : "rgba(138, 90, 0, 0.06)",
      }}
    >
      {isClient ? "Client" : "Draft"}
    </span>
  );
}

const selectStyle: React.CSSProperties = {
  fontFamily: "var(--font-sans)",
  fontSize: "0.85rem",
  padding: "0.35rem 0.5rem",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius)",
  background: "var(--color-paper)",
  color: "var(--color-ink)",
  minWidth: "13rem",
};

const radioStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "0.3rem",
  fontSize: "0.82rem",
};

function buttonStyle(disabled: boolean): React.CSSProperties {
  return {
    fontFamily: "var(--font-sans)",
    fontSize: "0.85rem",
    padding: "0.4rem 0.9rem",
    border: "1px solid var(--color-accent)",
    borderRadius: "var(--radius)",
    background: disabled ? "var(--color-ink-muted)" : "var(--color-accent)",
    color: "var(--color-accent-contrast)",
    cursor: disabled ? "default" : "pointer",
  };
}

const linkButtonStyle: React.CSSProperties = {
  fontFamily: "var(--font-sans)",
  fontSize: "0.8rem",
  padding: 0,
  border: 0,
  background: "none",
  color: "var(--color-accent)",
  cursor: "pointer",
  textDecoration: "underline",
};

const thStyle: React.CSSProperties = { padding: "0.3rem 0.4rem", fontWeight: 500 };
const tdStyle: React.CSSProperties = { padding: "0.4rem 0.4rem", verticalAlign: "top" };
