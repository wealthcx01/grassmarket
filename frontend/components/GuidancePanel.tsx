/**
 * Rubric guidance for a subcomponent (Methodology §4, GRS-0008). Shows the four level anchors,
 * INCLUDING those whose status is `todo` — rendered as "guidance not yet authored", never a blank.
 */

"use client";

import { useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import type { RubricAnchor } from "@/lib/types";

export function GuidancePanel({ subcomponentKey }: { subcomponentKey: string }) {
  const [anchors, setAnchors] = useState<RubricAnchor[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    setAnchors(null);
    setError(null);
    api
      .guidance(subcomponentKey, ctrl.signal)
      .then(setAnchors)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0) return; // aborted / navigation
        setError(err instanceof ApiError ? err.message : "Could not load guidance.");
      });
    return () => ctrl.abort();
  }, [subcomponentKey]);

  if (error) return <p style={{ color: "var(--color-error)", fontSize: "0.8rem" }}>{error}</p>;
  if (!anchors) return <p style={{ color: "var(--color-ink-muted)", fontSize: "0.8rem" }}>Loading guidance…</p>;
  // A real subcomponent whose rubric ladder isn't authored yet (e.g. the draft wealth infra set)
  // returns an empty list — show a friendly note, never a blank panel or a raw error (GRS-0147f).
  if (anchors.length === 0)
    return (
      <p style={{ color: "var(--color-ink-muted)", fontSize: "0.8rem" }}>
        Guidance not yet authored for this subcomponent (draft profile).
      </p>
    );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      {anchors.map((a) => (
        <div
          key={a.level}
          style={{
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius)",
            padding: "0.5rem 0.65rem",
            background: "var(--color-paper)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <strong style={{ fontSize: "0.85rem" }}>{a.level}</strong>
            {a.status !== "authored" ? (
              <span
                className="mono"
                style={{ fontSize: "0.62rem", textTransform: "uppercase", color: "var(--color-warn)" }}
              >
                {a.status}
              </span>
            ) : null}
          </div>
          {a.status === "todo" ? (
            <p style={{ margin: "0.25rem 0 0", fontSize: "0.8rem", color: "var(--color-ink-muted)", fontStyle: "italic" }}>
              Guidance not yet authored.
            </p>
          ) : (
            <>
              <p style={{ margin: "0.25rem 0 0", fontSize: "0.82rem" }}>{a.statement}</p>
              {a.required_evidence.length > 0 ? (
                <p style={{ margin: "0.3rem 0 0", fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
                  Evidence: {a.required_evidence.join("; ")}
                </p>
              ) : null}
              {a.differentiator_questions.map((q) => (
                <p key={q} style={{ margin: "0.2rem 0 0", fontSize: "0.75rem", fontStyle: "italic" }}>
                  “{q}”
                </p>
              ))}
              {a.misgrading_notes ? (
                <p style={{ margin: "0.3rem 0 0", fontSize: "0.72rem", color: "var(--color-warn)" }}>
                  ⚠ {a.misgrading_notes}
                </p>
              ) : null}
            </>
          )}
        </div>
      ))}
    </div>
  );
}
