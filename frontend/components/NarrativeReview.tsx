/**
 * NarrativeReview (GRS-0019 slice 2) — AI proposes, a human approves. For a deliverable, draft the
 * interpretation/commentary/recommendation sections, review each as an AI-draft-vs-your-edit view,
 * and approve. Approval is the runtime gate (non-negotiable #8): nothing reaches a client until a
 * human signs it off, and a junior-tier author's draft needs senior sign-off — the seniority
 * refusal is surfaced here as a plain-English message, not a status code.
 */

import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import type { AINarrative, NarrativeSection, NarrativeStatus } from "@/lib/types";

const SECTION_LABEL: Record<NarrativeSection, string> = {
  interpretation: "Interpretation",
  commentary: "Commentary",
  recommendation: "Recommendation",
};

const STATUS_LABEL: Record<NarrativeStatus, string> = {
  proposed: "Proposed",
  approved: "Approved",
  rejected: "Rejected",
};

function formatWhen(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "—" : d.toISOString().slice(0, 16).replace("T", " ");
}

export function NarrativeReview({
  deliverableId,
  onNarrativesChanged,
}: {
  deliverableId: string;
  onNarrativesChanged?: () => void;
}) {
  const [items, setItems] = useState<AINarrative[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<{ kind: "error" | "ok"; text: string } | null>(null);

  const reload = useCallback(
    (signal?: AbortSignal) =>
      api
        .listNarratives(deliverableId, signal)
        .then(setItems)
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0) return;
          setLoadError(err instanceof ApiError ? err.message : "Could not load AI narratives.");
        }),
    [deliverableId],
  );

  useEffect(() => {
    const ctrl = new AbortController();
    void reload(ctrl.signal);
    return () => ctrl.abort();
  }, [reload]);

  async function propose() {
    setBusy(true);
    setNotice(null);
    try {
      await api.proposeNarratives(deliverableId);
      setNotice({ kind: "ok", text: "AI drafted the interpretation, commentary and recommendation." });
      await reload();
      onNarrativesChanged?.(); // keep the parent's approval-queue count fresh
    } catch (err) {
      setNotice({
        kind: "error",
        text: err instanceof ApiError ? err.message : "Could not draft the narratives.",
      });
    } finally {
      setBusy(false);
    }
  }

  const onApproved = useCallback(
    (text: string) => {
      setNotice({ kind: "ok", text });
      void reload();
      onNarrativesChanged?.(); // an approval clears a section from the parent's queue
    },
    [reload, onNarrativesChanged],
  );

  return (
    <div style={{ marginTop: "0.6rem", paddingTop: "0.6rem", borderTop: "1px dashed var(--color-border)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h3 style={{ fontSize: "0.9rem", margin: 0 }}>AI narratives</h3>
        <span className="mono" style={{ fontSize: "0.64rem", color: "var(--color-ink-muted)" }}>
          AI proposes · a human approves
        </span>
      </div>

      {notice && (
        <p
          role={notice.kind === "error" ? "alert" : undefined}
          style={{
            fontSize: "0.78rem",
            margin: "0.4rem 0",
            color: notice.kind === "error" ? "var(--color-error)" : "var(--color-accent)",
          }}
        >
          {notice.text}
        </p>
      )}

      {loadError ? (
        <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.82rem" }}>{loadError}</p>
      ) : items === null ? (
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.82rem" }}>Loading…</p>
      ) : items.length === 0 ? (
        <div style={{ fontSize: "0.82rem" }}>
          <p style={{ color: "var(--color-ink-muted)", margin: "0.4rem 0" }}>
            No AI narratives yet.
          </p>
          <button type="button" onClick={() => void propose()} disabled={busy} style={primaryButton(busy)}>
            {busy ? "Drafting…" : "Draft AI narratives"}
          </button>
        </div>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, margin: "0.5rem 0 0", display: "flex", flexDirection: "column", gap: "0.6rem" }}>
          {items.map((n) => (
            <li key={n.id}>
              <NarrativeCard narrative={n} onApproved={onApproved} onError={(t) => setNotice({ kind: "error", text: t })} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function NarrativeCard({
  narrative,
  onApproved,
  onError,
}: {
  narrative: AINarrative;
  onApproved: (text: string) => void;
  onError: (text: string) => void;
}) {
  const [edit, setEdit] = useState(narrative.final_text ?? narrative.proposed_text);
  const [approving, setApproving] = useState(false);
  const approved = narrative.status === "approved";
  const edited = edit.trim() !== narrative.proposed_text.trim();

  async function approve() {
    setApproving(true);
    try {
      const result = await api.approveNarrative(narrative.id, { final_text: edit });
      onApproved(`${SECTION_LABEL[result.section]} approved.`);
    } catch (err) {
      // The seniority gate (a junior author needs Consultant-tier sign-off) and empty-text refusal
      // arrive as plain messages — surface them, don't swallow.
      onError(err instanceof ApiError ? err.message : "Could not approve the narrative.");
    } finally {
      setApproving(false);
    }
  }

  return (
    <div style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius)", padding: "0.6rem 0.7rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.4rem" }}>
        <strong style={{ fontSize: "0.85rem" }}>{SECTION_LABEL[narrative.section]}</strong>
        <StatusBadge status={narrative.status} />
      </div>

      {approved ? (
        <>
          <p style={{ fontSize: "0.82rem", margin: "0 0 0.4rem", whiteSpace: "pre-wrap" }}>
            {narrative.final_text}
          </p>
          <p className="mono" style={{ fontSize: "0.66rem", color: "var(--color-ink-muted)", margin: 0 }}>
            Approved by {narrative.approved_by_consultant_id?.slice(0, 8)} at{" "}
            {formatWhen(narrative.approved_at)} · {narrative.edit_summary}
          </p>
        </>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.6rem" }}>
          <div>
            <div style={labelStyle}>AI draft</div>
            <p style={draftStyle}>{narrative.proposed_text}</p>
          </div>
          <div>
            <div style={labelStyle}>
              Your edit {edited && <span style={{ color: "var(--color-warn)" }}>· edited</span>}
            </div>
            <textarea
              value={edit}
              onChange={(e) => setEdit(e.target.value)}
              aria-label={`Edit ${SECTION_LABEL[narrative.section]}`}
              rows={5}
              style={textareaStyle}
            />
            <button
              type="button"
              onClick={() => void approve()}
              disabled={approving || !edit.trim()}
              style={primaryButton(approving || !edit.trim())}
            >
              {approving ? "Approving…" : edited ? "Approve edited" : "Approve as drafted"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: NarrativeStatus }) {
  const color =
    status === "approved"
      ? "var(--color-accent)"
      : status === "rejected"
        ? "var(--color-error)"
        : "var(--color-warn)";
  return (
    <span
      className="mono"
      style={{
        fontSize: "0.62rem",
        textTransform: "uppercase",
        letterSpacing: "0.03em",
        padding: "0.1rem 0.4rem",
        borderRadius: "2px",
        border: `1px solid ${color}`,
        color,
      }}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}

function primaryButton(disabled: boolean): React.CSSProperties {
  return {
    fontFamily: "var(--font-sans)",
    fontSize: "0.8rem",
    marginTop: "0.4rem",
    padding: "0.35rem 0.8rem",
    border: "1px solid var(--color-accent)",
    borderRadius: "var(--radius)",
    background: disabled ? "var(--color-ink-muted)" : "var(--color-accent)",
    color: "var(--color-accent-contrast)",
    cursor: disabled ? "default" : "pointer",
  };
}

const labelStyle: React.CSSProperties = {
  fontSize: "0.66rem",
  color: "var(--color-ink-muted)",
  marginBottom: "0.2rem",
};

const draftStyle: React.CSSProperties = {
  fontSize: "0.8rem",
  margin: 0,
  padding: "0.4rem 0.5rem",
  background: "var(--color-paper)",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius)",
  whiteSpace: "pre-wrap",
  color: "var(--color-ink-muted)",
};

const textareaStyle: React.CSSProperties = {
  width: "100%",
  fontFamily: "var(--font-sans)",
  fontSize: "0.8rem",
  padding: "0.4rem 0.5rem",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius)",
  background: "var(--color-paper-raised)",
  color: "var(--color-ink)",
  resize: "vertical",
};
