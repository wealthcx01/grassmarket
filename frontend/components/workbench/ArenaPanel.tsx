"use client";

/**
 * Practice Arena (GRS-0025/0027). The advisor picks a scenario, conducts a discovery role-play
 * (entered here as advisor turns), submits, and sees a deterministic completeness score plus
 * AI-DRAFTED coaching feedback — always labelled as a machine draft, never authoritative (#8).
 */

import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import type { ArenaScenario, ArenaSession, ArenaTurn } from "@/lib/types";

export function ArenaPanel() {
  const [scenarios, setScenarios] = useState<ArenaScenario[] | null>(null);
  const [history, setHistory] = useState<ArenaSession[]>([]);
  const [active, setActive] = useState<{ session: ArenaSession; scenario: ArenaScenario } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const [sces, sessions] = await Promise.all([api.arenaScenarios(signal), api.arenaSessions(signal)]);
      setScenarios(sces);
      setHistory(sessions);
    } catch (err) {
      if (err instanceof ApiError && err.status === 0 && err.aborted) return;
      setError(err instanceof ApiError ? err.message : "Could not load the arena.");
    }
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    void load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  async function start(scenario: ArenaScenario) {
    try {
      const session = await api.startArenaSession(scenario.id);
      setActive({ session, scenario });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start a session.");
    }
  }

  if (error) {
    return <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.9rem" }}>{error}</p>;
  }
  if (active) {
    return (
      <ArenaSessionView
        session={active.session}
        scenario={active.scenario}
        onDone={() => {
          setActive(null);
          void load();
        }}
      />
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <section>
        <h3 style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>Scenarios</h3>
        {scenarios === null ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>Loading…</p>
        ) : scenarios.length === 0 ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>No scenarios published yet.</p>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {scenarios.map((s) => (
              <li key={s.id} style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius)", padding: "0.7rem 0.9rem", display: "flex", justifyContent: "space-between", gap: "0.8rem", alignItems: "center" }}>
                <div>
                  <strong style={{ fontSize: "0.88rem" }}>{s.title}</strong>
                  <p style={{ margin: "0.2rem 0 0", fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>{s.brief}</p>
                </div>
                <button type="button" onClick={() => void start(s)} style={{ padding: "0.4rem 0.9rem", background: "var(--color-accent)", color: "var(--color-accent-contrast)", border: "none", borderRadius: "var(--radius)", cursor: "pointer", fontSize: "0.78rem", whiteSpace: "nowrap" }}>
                  Practise
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h3 style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>Your history</h3>
        {history.length === 0 ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>No sessions yet.</p>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {history.map((s) => (
              <li key={s.id} style={{ fontSize: "0.82rem", display: "flex", justifyContent: "space-between", gap: "0.6rem" }}>
                <span className="mono" style={{ color: "var(--color-ink-muted)", fontSize: "0.72rem" }}>
                  {s.scored_at ? s.scored_at.slice(0, 10) : "in progress"}
                </span>
                <span>{s.score ? `${Math.round(s.score.completeness * 100)}% complete` : s.status}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function ArenaSessionView({
  session,
  scenario,
  onDone,
}: {
  session: ArenaSession;
  scenario: ArenaScenario;
  onDone: () => void;
}) {
  const [draft, setDraft] = useState("");
  const [turns, setTurns] = useState<ArenaTurn[]>([]);
  const [scored, setScored] = useState<ArenaSession | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function addTurn(speaker: "advisor" | "client") {
    if (!draft.trim()) return;
    setTurns((cur) => [...cur, { speaker, text: draft.trim() }]);
    setDraft("");
  }

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      setScored(await api.submitArenaSession(session.id, turns));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit.");
    } finally {
      setBusy(false);
    }
  }

  if (scored && scored.score) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <h3 style={{ fontSize: "1.05rem", margin: 0 }}>Scored: {scenario.title}</h3>
        <p style={{ fontSize: "1.4rem", fontWeight: 600, margin: 0 }}>
          {Math.round(scored.score.completeness * 100)}%
          <span style={{ fontSize: "0.8rem", fontWeight: 400, color: "var(--color-ink-muted)" }}> extraction completeness</span>
        </p>
        <p style={{ fontSize: "0.82rem", color: "var(--color-ink-muted)", margin: 0 }}>
          Powers fully probed: {scored.score.powers.filter((p) => p.benefit_probed && p.barrier_probed).map((p) => p.power_key).join(", ") || "none"} ·
          Modules evidenced: {scored.score.modules_evidenced.join(", ") || "none"} ·
          Evidence questions: {scored.score.evidence_questions}
        </p>
        {scored.feedback && (
          <div style={{ border: "1px dashed var(--color-border)", borderRadius: "var(--radius)", padding: "0.9rem" }}>
            {scored.feedback_is_ai_drafted && (
              <span className="mono" style={{ fontSize: "0.62rem", textTransform: "uppercase", color: "var(--color-warn)", letterSpacing: "0.08em" }}>
                AI-drafted coaching · review before you rely on it
              </span>
            )}
            <p style={{ margin: "0.4rem 0 0", fontSize: "0.85rem", whiteSpace: "pre-wrap" }}>{scored.feedback}</p>
          </div>
        )}
        <button type="button" onClick={onDone} style={{ alignSelf: "flex-start", padding: "0.5rem 1rem", background: "var(--color-accent)", color: "var(--color-accent-contrast)", border: "none", borderRadius: "var(--radius)", cursor: "pointer" }}>
          Back to arena
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      <div>
        <h3 style={{ fontSize: "1.05rem", margin: 0 }}>{scenario.title}</h3>
        <p style={{ margin: "0.3rem 0 0", fontSize: "0.82rem", color: "var(--color-ink-muted)" }}>{scenario.client_persona}</p>
      </div>
      {error && <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.85rem", margin: 0 }}>{error}</p>}

      <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.35rem" }}>
        {turns.map((t, i) => (
          <li key={i} style={{ fontSize: "0.84rem", alignSelf: t.speaker === "advisor" ? "flex-end" : "flex-start", maxWidth: "80%", background: t.speaker === "advisor" ? "var(--color-accent)" : "var(--color-paper-raised)", color: t.speaker === "advisor" ? "var(--color-accent-contrast)" : "inherit", padding: "0.4rem 0.7rem", borderRadius: "var(--radius)", border: "1px solid var(--color-border)" }}>
            {t.text}
          </li>
        ))}
      </ul>

      <textarea
        aria-label="Turn text"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        rows={2}
        placeholder="Type a turn, then add it as your line or the client's…"
        style={{ width: "100%", padding: "0.5rem", borderRadius: "var(--radius)", border: "1px solid var(--color-border)", fontFamily: "inherit", fontSize: "0.85rem" }}
      />
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <button type="button" onClick={() => addTurn("advisor")} style={{ padding: "0.4rem 0.8rem", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", background: "var(--color-paper-raised)", cursor: "pointer", fontSize: "0.8rem" }}>
          Add my line
        </button>
        <button type="button" onClick={() => addTurn("client")} style={{ padding: "0.4rem 0.8rem", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", background: "var(--color-paper-raised)", cursor: "pointer", fontSize: "0.8rem" }}>
          Add client line
        </button>
        <button type="button" onClick={() => void submit()} disabled={busy || turns.length === 0} style={{ padding: "0.4rem 0.9rem", marginLeft: "auto", background: "var(--color-accent)", color: "var(--color-accent-contrast)", border: "none", borderRadius: "var(--radius)", cursor: turns.length === 0 ? "not-allowed" : "pointer", fontSize: "0.8rem", opacity: turns.length === 0 ? 0.5 : 1 }}>
          {busy ? "Scoring…" : "Submit for scoring"}
        </button>
      </div>
    </div>
  );
}
