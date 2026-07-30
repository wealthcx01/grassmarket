"use client";

/**
 * Where this assessment stands with the founder (GRS-0188, ADR-0041).
 *
 * Three states. The subtlety is that an approval covers the version of the document it was given
 * for, so editing after approval quietly stops it counting — the advisor has to be told that in
 * plain words, or they hit a 409 at finalisation and have no idea why.
 *
 * The server tells us whether an approval matches the CURRENT document, which is the only thing
 * the gate cares about. It does not tell an advisor whether an older, superseded approval exists;
 * that distinction is on the founder's queue, where it belongs. So "approved then edited" reads
 * here as "waiting for review", which is accurate about what has to happen next.
 */

import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import type { FounderApproval } from "@/lib/types";

type State = "loading" | "not-submitted" | "submitted" | "approved";

export function FounderReviewStatus({
  assessmentId,
  reviewRequestedAt,
  onChanged,
}: {
  assessmentId: string;
  reviewRequestedAt: string | null;
  onChanged?: () => void;
}) {
  const [approval, setApproval] = useState<FounderApproval | null>(null);
  const [state, setState] = useState<State>("loading");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      try {
        const current = await api.currentFounderApproval(assessmentId, signal);
        setApproval(current);
        if (current) setState("approved");
        else if (reviewRequestedAt) setState("submitted");
        else setState("not-submitted");
      } catch (err: unknown) {
        if (err instanceof ApiError && err.status === 0 && err.aborted) return;
        setError("Could not check the review status.");
        setState("not-submitted");
      }
    },
    [assessmentId, reviewRequestedAt],
  );

  useEffect(() => {
    const ctrl = new AbortController();
    void load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await api.submitForFounderReview(assessmentId);
      await load();
      onChanged?.();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not submit for review.");
    } finally {
      setBusy(false);
    }
  }

  const copy: Record<State, { heading: string; body: string }> = {
    loading: { heading: "Checking…", body: "" },
    "not-submitted": {
      heading: "Not yet sent for review",
      body: "Before this can be finalised or turned into anything a client sees, John needs to read it and sign it off. Send it when you are happy with it.",
    },
    submitted: {
      heading: "With John for review",
      body: "He has it. You will be able to finalise once he has signed off this version. If you change anything in the meantime, send it again so he is reading what you actually want to go out.",
    },
    approved: {
      heading: "Approved",
      body: approval
        ? `Signed off on ${new Date(approval.approved_at).toLocaleDateString()}. This covers the assessment exactly as it stands now, so you can finalise it and produce client work from it.`
        : "",
    },
  };

  const { heading, body } = copy[state];

  return (
    <section
      style={{
        border: "1px solid var(--color-rule)",
        borderRadius: "0.4rem",
        padding: "0.9rem 1.1rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
      }}
    >
      <h4 style={{ margin: 0, fontSize: "0.95rem" }}>{heading}</h4>
      {body && (
        <p
          style={{
            margin: 0,
            fontSize: "0.85rem",
            color: "var(--color-ink-muted)",
            maxWidth: "44rem",
          }}
        >
          {body}
        </p>
      )}
      {error && (
        <p role="alert" style={{ fontSize: "0.85rem", color: "var(--color-danger, #a3312a)" }}>
          {error}
        </p>
      )}
      {state !== "approved" && state !== "loading" && (
        <div>
          <button type="button" onClick={() => void submit()} disabled={busy}>
            {busy
              ? "Sending…"
              : state === "not-submitted"
                ? "Send to John for review"
                : "Send again"}
          </button>
        </div>
      )}
    </section>
  );
}
