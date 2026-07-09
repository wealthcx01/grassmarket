/**
 * The live-score panel — V/L/B/P and per-module q_m, each rendered through `BandDisplay` so the
 * ADR-0008 honesty flag is honoured (an unmodelled B or P shows a point, never a tight range). When
 * the document is not yet scoreable it shows what is still blocking rather than a fake number.
 */

import { BandDisplay } from "@/components/BandDisplay";
import type { LiveScore } from "@/lib/types";

export function LiveScorePanel({
  score,
  loading,
  error,
  onRefresh,
}: {
  score: LiveScore | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}) {
  return (
    <aside
      style={{
        position: "sticky",
        top: "1rem",
        background: "var(--color-paper-raised)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        padding: "1rem",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h3 style={{ margin: 0, fontSize: "1rem" }}>Live score</h3>
        <button type="button" onClick={onRefresh} disabled={loading} style={ghostBtn}>
          {loading ? "…" : "Refresh"}
        </button>
      </div>

      {error ? (
        <p style={{ color: "var(--color-error)", fontSize: "0.85rem" }}>{error}</p>
      ) : !score ? (
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>
          Enter data to see a live score.
        </p>
      ) : !score.scoreable ? (
        <div>
          <p style={{ margin: "0.5rem 0", color: "var(--color-warn)", fontSize: "0.85rem" }}>
            Not yet scoreable:
          </p>
          <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "0.82rem" }}>
            {score.blocking.map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
          <Coverage score={score} />
        </div>
      ) : (
        <div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <BandDisplay label="V — Platform Value" band={score.v} />
            <BandDisplay label="L — Infrastructure" band={score.l_index} />
            <BandDisplay label="B — Business" band={score.b} />
            <BandDisplay label="P — Strategic Power" band={score.p} />
          </div>
          <p style={{ margin: "0.75rem 0 0", fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>
            Assessment uncertainty: <strong>{score.overall_uncertainty ?? "—"}</strong>
          </p>
          <Coverage score={score} />
        </div>
      )}
    </aside>
  );
}

function Coverage({ score }: { score: LiveScore }) {
  const pct = score.coverage != null ? Math.round(score.coverage * 100) : null;
  return (
    <p style={{ margin: "0.4rem 0 0", fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
      Coverage: {score.subcomponents_assessed}/{score.subcomponents_total} subcomponents
      {pct != null ? ` (${pct}% of applicable)` : ""}
    </p>
  );
}

const ghostBtn: React.CSSProperties = {
  border: "1px solid var(--color-border)",
  background: "transparent",
  borderRadius: "var(--radius)",
  padding: "0.2rem 0.55rem",
  fontSize: "0.75rem",
  cursor: "pointer",
};
