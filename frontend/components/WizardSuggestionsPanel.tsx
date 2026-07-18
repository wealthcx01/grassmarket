/**
 * Wizard input assistant (GRS-0101/0136, ADR-0032). Shows DETERMINISTIC, rule-based suggestions while
 * the advisor fills the assessment — a coverage nudge and a consistency check. It is honestly labelled
 * "Suggestions", not "AI": it computes nothing the scoring engine computes and proposes no maturity
 * levels (a pre-planted level would anchor a bottleneck-sensitive score — GRS-0136). Nothing is
 * committed here; a suggestion is just help. (The panel still supports a PREFILL kind for a future
 * genuinely-safe prefill; a PREFILL applies only on an explicit Accept, editable after.)
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
      aria-label="Suggestions"
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
        <h3 style={{ margin: 0, fontSize: "0.92rem" }}>Suggestions</h3>
        <span className="mono" style={{ fontSize: "0.58rem", color: "var(--color-ink-faint)" }} title="The rule-based suggester version that produced these">
          {version}
        </span>
      </div>
      <p style={{ margin: 0, fontSize: "0.68rem", color: "var(--color-ink-faint)" }}>
        Rule-based checks to sharpen your assessment — not scores, and never applied unless you act.
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
