"use client";

/**
 * Calibration (GRS-0022/0027). BLIND while OPEN: an assessor enters their own ratings and can see
 * only that their set is submitted — never co-raters' ratings and never the agreement result. The
 * result panel is rendered ONLY once the session is CLOSED (server enforces the same gate: results
 * 404 while open). This mirror keeps the UI from ever implying blindness is broken.
 */

import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import { MATURITY_LEVELS } from "@/lib/types";
import type {
  CalibrationResult,
  CalibrationSession,
  MaturityLevel,
  RatingEntry,
} from "@/lib/types";

export function CalibrationPanel() {
  const [sessions, setSessions] = useState<CalibrationSession[] | null>(null);
  const [selected, setSelected] = useState<CalibrationSession | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    api
      .calibrationSessions(ctrl.signal)
      .then(setSessions)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0) return;
        setError(err instanceof ApiError ? err.message : "Could not load calibration sessions.");
      });
    return () => ctrl.abort();
  }, []);

  if (error) {
    return <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.9rem" }}>{error}</p>;
  }
  if (selected) {
    return <CalibrationSessionView session={selected} onBack={() => setSelected(null)} />;
  }
  return (
    <section>
      <h3 style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>Calibration sessions</h3>
      {sessions === null ? (
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>Loading…</p>
      ) : sessions.length === 0 ? (
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>No calibration sessions.</p>
      ) : (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {sessions.map((s) => (
            <li key={s.id}>
              <button
                type="button"
                onClick={() => setSelected(s)}
                style={{
                  width: "100%",
                  textAlign: "left",
                  padding: "0.7rem 0.9rem",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius)",
                  background: "var(--color-paper-raised)",
                  cursor: "pointer",
                  display: "flex",
                  justifyContent: "space-between",
                  gap: "0.6rem",
                }}
              >
                <span style={{ fontWeight: 500 }}>{s.title}</span>
                <span className="mono" style={{ fontSize: "0.68rem", color: s.status === "open" ? "var(--color-warn)" : "var(--color-accent)", textTransform: "uppercase" }}>
                  {s.status}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function CalibrationSessionView({ session, onBack }: { session: CalibrationSession; onBack: () => void }) {
  const isOpen = session.status === "open";
  const [levels, setLevels] = useState<Record<string, MaturityLevel>>({});
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<CalibrationResult | null>(null);
  const [notice, setNotice] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  const key = (vi: number, sc: string) => `${vi}::${sc}`;

  const load = useCallback(
    async (signal?: AbortSignal) => {
      try {
        const mine = await api.myCalibrationRating(session.id, signal);
        setSubmitted(mine.submitted);
      } catch {
        setSubmitted(false); // no rating yet
      }
      // The result is fetched ONLY for a closed session — blindness while open.
      if (!isOpen) {
        try {
          setResult(await api.calibrationResult(session.id, signal));
        } catch (err) {
          if (!(err instanceof ApiError && err.status === 0)) setResult(null);
        }
      }
    },
    [session.id, isOpen],
  );

  useEffect(() => {
    const ctrl = new AbortController();
    void load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  async function submit() {
    const entries: RatingEntry[] = [];
    session.vignettes.forEach((v, vi) => {
      v.anchors.forEach((a) => {
        const level = levels[key(vi, a.subcomponent_key)];
        if (level) entries.push({ vignette_index: vi, subcomponent_key: a.subcomponent_key, level });
      });
    });
    setBusy(true);
    setNotice(null);
    try {
      const saved = await api.submitCalibrationRating(session.id, entries);
      setSubmitted(saved.submitted);
      setNotice({ kind: "ok", text: "Your blind rating is submitted and locked." });
    } catch (err) {
      setNotice({ kind: "error", text: err instanceof ApiError ? err.message : "Could not submit." });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
      <button type="button" onClick={onBack} style={{ alignSelf: "flex-start", background: "none", border: "none", color: "var(--color-accent)", cursor: "pointer", fontSize: "0.82rem", padding: 0 }}>
        ← All sessions
      </button>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.6rem" }}>
        <h3 style={{ fontSize: "1.05rem", margin: 0 }}>{session.title}</h3>
        <span className="mono" style={{ fontSize: "0.68rem", textTransform: "uppercase", color: isOpen ? "var(--color-warn)" : "var(--color-accent)" }}>
          {session.status}
        </span>
      </div>

      {notice && (
        <p role={notice.kind === "error" ? "alert" : undefined} style={{ fontSize: "0.82rem", margin: 0, color: notice.kind === "error" ? "var(--color-error)" : "var(--color-accent)" }}>
          {notice.text}
        </p>
      )}

      {isOpen ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
            Blind rating — co-raters&apos; entries and the agreement result stay hidden until the
            facilitator closes the session.
          </p>
          {submitted ? (
            <p style={{ fontSize: "0.85rem", fontWeight: 500 }}>
              ✓ Your rating is submitted and locked. Results appear when the session closes.
            </p>
          ) : (
            <>
              {session.vignettes.map((v, vi) => (
                <div key={vi} style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius)", padding: "0.9rem" }}>
                  <strong style={{ fontSize: "0.9rem" }}>{v.title}</strong>
                  <p style={{ margin: "0.3rem 0 0.6rem", fontSize: "0.82rem", color: "var(--color-ink-muted)" }}>{v.excerpt}</p>
                  {v.anchors.map((a) => (
                    <label key={a.subcomponent_key} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem", fontSize: "0.82rem", padding: "0.2rem 0" }}>
                      <span className="mono" style={{ fontSize: "0.72rem" }}>{a.subcomponent_key}</span>
                      <select
                        aria-label={`Rate ${a.subcomponent_key} in ${v.title}`}
                        value={levels[key(vi, a.subcomponent_key)] ?? ""}
                        onChange={(e) =>
                          setLevels((cur) => ({ ...cur, [key(vi, a.subcomponent_key)]: e.target.value as MaturityLevel }))
                        }
                      >
                        <option value="" disabled>
                          Rate…
                        </option>
                        {MATURITY_LEVELS.map((m) => (
                          <option key={m} value={m}>
                            {m}
                          </option>
                        ))}
                      </select>
                    </label>
                  ))}
                </div>
              ))}
              <button
                type="button"
                onClick={() => void submit()}
                disabled={busy}
                style={{ alignSelf: "flex-start", padding: "0.5rem 1rem", background: "var(--color-accent)", color: "var(--color-accent-contrast)", border: "none", borderRadius: "var(--radius)", cursor: busy ? "wait" : "pointer" }}
              >
                {busy ? "Submitting…" : "Submit blind rating"}
              </button>
            </>
          )}
        </div>
      ) : (
        <section>
          <h4 style={{ fontSize: "0.9rem", margin: "0 0 0.5rem" }}>Agreement (session closed)</h4>
          {result === null ? (
            <p style={{ color: "var(--color-ink-muted)", fontSize: "0.82rem" }}>No result available.</p>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
              <thead>
                <tr style={{ textAlign: "left", color: "var(--color-ink-muted)" }}>
                  <th style={{ padding: "0.3rem 0" }}>Anchor</th>
                  <th style={{ padding: "0.3rem 0", textAlign: "right" }}>κ_w</th>
                  <th style={{ padding: "0.3rem 0", textAlign: "right" }}>AC1</th>
                  <th style={{ padding: "0.3rem 0", textAlign: "right" }}>Flag</th>
                </tr>
              </thead>
              <tbody>
                {result.anchors.map((a) => (
                  <tr key={a.subcomponent_key} style={{ borderTop: "1px solid var(--color-border)" }}>
                    <td className="mono" style={{ padding: "0.3rem 0", fontSize: "0.72rem" }}>{a.subcomponent_key}</td>
                    <td style={{ padding: "0.3rem 0", textAlign: "right" }}>{a.kappa_w.toFixed(2)}</td>
                    <td style={{ padding: "0.3rem 0", textAlign: "right" }}>{a.ac1.toFixed(2)}</td>
                    <td style={{ padding: "0.3rem 0", textAlign: "right", color: a.flagged ? "var(--color-error)" : "var(--color-accent)" }}>
                      {a.flagged ? "rewrite" : "ok"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </div>
  );
}
