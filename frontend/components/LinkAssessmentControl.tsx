/**
 * Link a finalised assessment to an engagement (GRS-0039). Lists the advisor's finalised assessments
 * that aren't already linked. It distinguishes loading / empty / error explicitly: a failed load
 * shows an error + Retry rather than an invisible control that reads as "nothing to link".
 */

"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";

import { ApiError, api } from "@/lib/api";
import type { Assessment, Engagement } from "@/lib/types";

const inputStyle: React.CSSProperties = { fontSize: "0.85rem" };

export function LinkAssessmentControl({
  engagement,
  onLinked,
}: {
  engagement: Engagement;
  onLinked: () => Promise<unknown>;
}) {
  const [available, setAvailable] = useState<Assessment[]>([]);
  const [loaded, setLoaded] = useState(false); // distinguishes "still loading" from "loaded, none"
  const [loadError, setLoadError] = useState<string | null>(null);
  const [target, setTarget] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const linked = new Set(engagement.assessment_ids);
  const refresh = useCallback(
    (signal?: AbortSignal) =>
      api
        .listAssessments(signal)
        .then((all) => {
          setAvailable(all.filter((a) => a.state === "finalised" && !linked.has(a.id)));
          setLoaded(true);
          setLoadError(null);
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0) return; // aborted
          // Surface the failure instead of silently rendering nothing (which looked identical to
          // "you have no finalisable assessments"). Keeps the advisor from thinking it's empty.
          setLoadError(err instanceof ApiError ? err.message : "Could not load your assessments.");
        }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [engagement.assessment_ids.join(",")],
  );

  useEffect(() => {
    const ctrl = new AbortController();
    refresh(ctrl.signal);
    return () => ctrl.abort();
  }, [refresh]);

  if (loadError) {
    return (
      <p role="alert" style={{ marginTop: "0.75rem", fontSize: "0.8rem", color: "var(--color-error)" }}>
        Couldn&rsquo;t load your finalised assessments.{" "}
        <button
          type="button"
          onClick={() => refresh()}
          style={{ background: "none", border: "none", padding: 0, font: "inherit", color: "var(--color-accent)", textDecoration: "underline", cursor: "pointer" }}
        >
          Retry
        </button>
      </p>
    );
  }
  // Still loading, or genuinely nothing to link → render nothing (no false empty-state).
  if (!loaded || available.length === 0) return null;

  async function link(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!target) return;
    setBusy(true);
    setError(null);
    try {
      await api.linkAssessment(engagement.id, target);
      setTarget("");
      await onLinked();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not link the assessment.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={link} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center", marginTop: "0.75rem" }}>
      <label className="eyebrow" htmlFor="link-assessment" style={{ width: "100%", margin: 0 }}>
        Link a finalised assessment
      </label>
      <select id="link-assessment" value={target} onChange={(e) => setTarget(e.target.value)} style={{ ...inputStyle, flex: "1 1 16rem" }}>
        <option value="">Choose an assessment…</option>
        {available.map((a) => (
          <option key={a.id} value={a.id}>
            {a.subject}
          </option>
        ))}
      </select>
      <button type="submit" className="btn btn-secondary" disabled={busy || !target}>
        {busy ? "Linking…" : "Link"}
      </button>
      {error ? (
        <p role="alert" style={{ width: "100%", margin: 0, color: "var(--color-error)", fontSize: "0.8rem" }}>
          {error}
        </p>
      ) : null}
    </form>
  );
}
