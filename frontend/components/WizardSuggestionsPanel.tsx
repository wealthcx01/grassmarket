/**
 * AI-assisted wizard input (GRS-0101, ADR-0032). Shows deterministic AI PROPOSALS while the advisor
 * fills the assessment — a coverage nudge, a consistency check, or a conservative prefill. Nothing is
 * committed here: a GUIDANCE item is just help; a PREFILL is applied ONLY when the advisor clicks
 * Accept (they can edit it after), so no AI-proposed value counts without a visible approve step.
 */

"use client";

import type { WizardSuggestion } from "@/lib/types";

export function WizardSuggestionsPanel({
  suggestions,
  version,
  onAccept,
  onDismiss,
}: {
  suggestions: WizardSuggestion[];
  version: string;
  onAccept: (s: WizardSuggestion) => void;
  onDismiss: (id: string) => void;
}) {
  if (suggestions.length === 0) return null;
  return (
    <section
      aria-label="AI suggestions"
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        background: "var(--color-paper-raised)",
        padding: "0.8rem 0.9rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.6rem",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.5rem" }}>
        <h3 style={{ margin: 0, fontSize: "0.92rem" }}>AI suggestions</h3>
        <span className="mono" style={{ fontSize: "0.58rem", color: "var(--color-ink-faint)" }} title="The suggester version that produced these">
          {version}
        </span>
      </div>
      <p style={{ margin: 0, fontSize: "0.68rem", color: "var(--color-ink-faint)" }}>
        AI-proposed — nothing is applied until you accept it.
      </p>
      <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.55rem" }}>
        {suggestions.map((s) => (
          <li
            key={s.id}
            style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius)", padding: "0.55rem 0.6rem" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginBottom: "0.2rem" }}>
              <span
                className="mono"
                style={{
                  fontSize: "0.54rem",
                  fontWeight: 700,
                  letterSpacing: "0.05em",
                  textTransform: "uppercase",
                  color: s.kind === "prefill" ? "var(--color-accent)" : "var(--color-ink-muted)",
                  border: `1px solid ${s.kind === "prefill" ? "var(--color-accent)" : "var(--color-border)"}`,
                  borderRadius: "999px",
                  padding: "0 0.3rem",
                }}
              >
                {s.kind === "prefill" ? "Prefill" : "Check"}
              </span>
              <strong style={{ fontSize: "0.8rem" }}>{s.title}</strong>
            </div>
            <p style={{ margin: "0 0 0.45rem", fontSize: "0.72rem", color: "var(--color-ink-muted)", lineHeight: 1.45 }}>
              {s.rationale}
            </p>
            <div style={{ display: "flex", gap: "0.4rem" }}>
              {s.kind === "prefill" ? (
                <button type="button" className="btn btn-primary" style={{ fontSize: "0.68rem", padding: "0.15rem 0.5rem" }} onClick={() => onAccept(s)}>
                  Accept
                </button>
              ) : null}
              <button type="button" className="btn" style={{ fontSize: "0.68rem", padding: "0.15rem 0.5rem" }} onClick={() => onDismiss(s.id)}>
                {s.kind === "prefill" ? "Dismiss" : "Got it"}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
