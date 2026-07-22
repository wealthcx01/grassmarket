/**
 * Rating Committee sign-off (Methodology §8, GRS-0061). Shows an assessment's high-stakes items
 * (power Established+, triad above None, module gate Frontier) and each one's committee decision.
 *
 * The owner sees the status (read-only — a consultant can never sign off their own high-stakes
 * ratings; peer challenge). A committee member or admin gets an approve/reject control with a
 * required rationale and optional dissent. The server enforces both rules — this UI mirrors them.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, api } from "@/lib/api";
import { getSession } from "@/lib/session";
import { humanizeKey } from "@/lib/labels";
import type { CommitteeDecisionStatus, CommitteeQueueEntry } from "@/lib/types";

type Status = "pending" | "approved" | "rejected" | "stale";

function entryStatus(e: CommitteeQueueEntry): Status {
  if (!e.decision) return "pending";
  if (e.decision.rating !== e.item.rating) return "stale"; // re-rated since the call
  return e.decision.status;
}

const STATUS_STYLE: Record<Status, { label: string; color: string; bg: string }> = {
  pending: { label: "Awaiting sign-off", color: "var(--color-warn)", bg: "rgba(138,90,0,0.08)" },
  approved: { label: "Approved", color: "var(--color-accent)", bg: "var(--color-accent-tint, rgba(26,59,38,0.07))" },
  rejected: { label: "Rejected", color: "var(--color-error)", bg: "rgba(158,58,46,0.08)" },
  stale: { label: "Stale — re-rated since sign-off", color: "var(--color-warn)", bg: "rgba(138,90,0,0.08)" },
};

export function CommitteeReviewPanel({ assessmentId }: { assessmentId: string }) {
  const [queue, setQueue] = useState<CommitteeQueueEntry[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const mounted = useRef(true);
  // Read the session only after mount (localStorage isn't available server-side; avoids a mismatch).
  const [canDecide, setCanDecide] = useState(false);
  const [ownAssessment, setOwnAssessment] = useState(false);

  const reload = useCallback(
    (signal?: AbortSignal) =>
      api
        .committeeQueue(assessmentId, signal)
        .then((q) => {
          if (!mounted.current) return;
          setQueue(q);
          setLoadError(null);
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0 && err.aborted) return;
          setLoadError(err instanceof ApiError ? err.message : "Could not load the committee queue.");
        }),
    [assessmentId],
  );

  useEffect(() => {
    mounted.current = true;
    const session = getSession();
    setCanDecide(session?.isCommittee ?? false);
    // The queue rows are owner-scoped; a committee member deciding on their OWN assessment is
    // refused by the server, so we only surface the control when it isn't theirs (best-effort;
    // the server is the real gate — it 409s a self sign-off).
    const ctrl = new AbortController();
    void reload(ctrl.signal);
    return () => {
      mounted.current = false;
      ctrl.abort();
    };
  }, [reload]);

  // Detect own-assessment lazily from the first decision's owner (if any) vs the session.
  useEffect(() => {
    if (!queue) return;
    const session = getSession();
    const anyOwner = queue.find((e) => e.decision)?.decision?.owner_consultant_id;
    if (anyOwner && session) setOwnAssessment(anyOwner === session.consultantId);
  }, [queue]);

  if (loadError) {
    return (
      <p role="alert" style={{ fontSize: "0.82rem", color: "var(--color-error)" }}>
        {loadError}
      </p>
    );
  }
  if (queue === null) return null; // loading — the finalise blockers already convey status
  if (queue.length === 0) return null; // no high-stakes items on this assessment

  const outstanding = queue.filter((e) => entryStatus(e) !== "approved").length;

  return (
    <section
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        padding: "0.9rem 1rem",
        background: "var(--color-paper-raised)",
        display: "flex",
        flexDirection: "column",
        gap: "0.7rem",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.5rem" }}>
        <h3 style={{ margin: 0, fontSize: "1rem" }}>Rating Committee sign-off</h3>
        <span className="mono" style={{ fontSize: "0.68rem", color: outstanding ? "var(--color-warn)" : "var(--color-accent)" }}>
          {outstanding ? `${outstanding} awaiting sign-off` : "all cleared"}
        </span>
      </div>
      <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        High-stakes ratings (§8) need a committee member&rsquo;s peer sign-off before this assessment
        can be finalised.
        {canDecide && !ownAssessment ? " Approve or reject each with a recorded rationale." : ""}
      </p>

      <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {queue.map((e) => (
          <CommitteeRow
            key={`${e.item.item_type}:${e.item.item_key}`}
            entry={e}
            status={entryStatus(e)}
            canDecide={canDecide && !ownAssessment}
            onDecided={() => void reload()}
            assessmentId={assessmentId}
          />
        ))}
      </ul>
    </section>
  );
}

function CommitteeRow({
  entry,
  status,
  canDecide,
  onDecided,
  assessmentId,
}: {
  entry: CommitteeQueueEntry;
  status: Status;
  canDecide: boolean;
  onDecided: () => void;
  assessmentId: string;
}) {
  const [open, setOpen] = useState(false);
  const [rationale, setRationale] = useState("");
  const [dissent, setDissent] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const s = STATUS_STYLE[status];
  const { item } = entry;
  const name = item.item_type === "triad" ? humanizeKey(item.item_key) : item.label;

  async function decide(decisionStatus: CommitteeDecisionStatus) {
    if (!rationale.trim()) {
      setError("A rationale is required to record a committee decision (§8).");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.decideCommitteeItem(assessmentId, {
        item_type: item.item_type,
        item_key: item.item_key,
        rating: item.rating,
        status: decisionStatus,
        rationale: rationale.trim(),
        dissent_note: dissent.trim() || null,
      });
      setOpen(false);
      onDecided();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not record the decision.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <li style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius)", padding: "0.55rem 0.7rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
        <span style={{ fontSize: "0.88rem" }}>
          <strong>{name}</strong>{" "}
          <span className="mono" style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
            {item.rating}
          </span>
        </span>
        <span
          className="mono"
          style={{ fontSize: "0.66rem", color: s.color, background: s.bg, borderRadius: "999px", padding: "0.12rem 0.5rem" }}
        >
          {s.label}
        </span>
      </div>
      <p style={{ margin: "0.25rem 0 0", fontSize: "0.76rem", color: "var(--color-ink-faint)" }}>{item.reason}</p>
      {entry.decision?.rationale && status !== "pending" ? (
        <p style={{ margin: "0.3rem 0 0", fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>
          <em>“{entry.decision.rationale}”</em>
          {entry.decision.dissent_note ? ` · dissent: ${entry.decision.dissent_note}` : ""}
        </p>
      ) : null}

      {canDecide ? (
        !open ? (
          <button
            type="button"
            onClick={() => setOpen(true)}
            style={{ marginTop: "0.4rem", background: "none", border: "none", padding: 0, color: "var(--color-accent)", textDecoration: "underline", cursor: "pointer", fontSize: "0.78rem" }}
          >
            {status === "pending" || status === "stale" ? "Review this rating" : "Change the decision"}
          </button>
        ) : (
          <div style={{ marginTop: "0.5rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            <textarea
              value={rationale}
              onChange={(ev) => setRationale(ev.target.value)}
              placeholder="Rationale — why this rating holds (or doesn't) against the moat-duration rubric…"
              rows={2}
              style={{ fontFamily: "inherit", fontSize: "0.82rem", padding: "0.4rem 0.5rem", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", background: "var(--color-paper)", color: "var(--color-ink)", resize: "vertical" }}
            />
            <input
              type="text"
              value={dissent}
              onChange={(ev) => setDissent(ev.target.value)}
              placeholder="Dissent note (optional)"
              style={{ fontFamily: "inherit", fontSize: "0.82rem", padding: "0.4rem 0.5rem", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", background: "var(--color-paper)", color: "var(--color-ink)" }}
            />
            <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
              <button type="button" className="btn btn-primary" disabled={busy} onClick={() => void decide("approved")} style={{ fontSize: "0.8rem" }}>
                {busy ? "Recording…" : "Approve"}
              </button>
              <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => void decide("rejected")} style={{ fontSize: "0.8rem" }}>
                Reject
              </button>
              <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => setOpen(false)} style={{ fontSize: "0.8rem" }}>
                Cancel
              </button>
            </div>
            {error ? <p role="alert" style={{ margin: 0, fontSize: "0.78rem", color: "var(--color-error)" }}>{error}</p> : null}
          </div>
        )
      ) : null}
    </li>
  );
}
