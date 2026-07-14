"use client";

/**
 * Learning library + Power Drills (GRS-0024/0027). Completing a coursework module updates the
 * advisor's certification evidence self-service (server-side); the drill grades reschedule the card
 * by SM-2. AI-drafted quizzes are not surfaced here — they reach advisors only after admin approval.
 */

import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import type { DrillCard, LearningModule } from "@/lib/types";

const GRADES = [0, 1, 2, 3, 4, 5];

export function LearningDrillsPanel() {
  const [modules, setModules] = useState<LearningModule[] | null>(null);
  const [completed, setCompleted] = useState<Set<string>>(new Set());
  const [due, setDue] = useState<DrillCard[] | null>(null);
  const [notice, setNotice] = useState<{ kind: "ok" | "error"; text: string } | null>(null);

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const [mods, dueCards] = await Promise.all([api.learningModules(signal), api.dueDrillCards(signal)]);
      setModules(mods);
      setDue(dueCards);
    } catch (err) {
      if (err instanceof ApiError && err.status === 0) return;
      setNotice({ kind: "error", text: err instanceof ApiError ? err.message : "Could not load." });
    }
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    void load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  async function complete(module: LearningModule) {
    try {
      await api.completeLearningModule(module.id);
      setCompleted((cur) => new Set(cur).add(module.id));
      setNotice({ kind: "ok", text: `Completed “${module.title}”.` });
    } catch (err) {
      setNotice({ kind: "error", text: err instanceof ApiError ? err.message : "Could not complete." });
    }
  }

  async function answer(card: DrillCard, grade: number) {
    try {
      await api.answerDrillCard(card.id, grade);
      setNotice({ kind: "ok", text: `Reviewed “${card.topic}”.` });
      await load();
    } catch (err) {
      setNotice({ kind: "error", text: err instanceof ApiError ? err.message : "Could not record." });
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {notice && (
        <p role={notice.kind === "error" ? "alert" : undefined} style={{ fontSize: "0.82rem", margin: 0, color: notice.kind === "error" ? "var(--color-error)" : "var(--color-accent)" }}>
          {notice.text}
        </p>
      )}

      <section>
        <h3 style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>Power drills due</h3>
        {due === null ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>Loading…</p>
        ) : due.length === 0 ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>Nothing due — nice work.</p>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {due.map((card) => (
              <li key={card.id} style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius)", padding: "0.7rem 0.9rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: "0.6rem", alignItems: "baseline" }}>
                  <span className="mono" style={{ fontSize: "0.8rem" }}>{card.topic}</span>
                  <span style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>streak {card.streak}</span>
                </div>
                <div style={{ display: "flex", gap: "0.3rem", marginTop: "0.5rem", flexWrap: "wrap" }}>
                  <span style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)", alignSelf: "center" }}>Recall:</span>
                  {GRADES.map((g) => (
                    <button
                      key={g}
                      type="button"
                      aria-label={`Grade ${g} for ${card.topic}`}
                      onClick={() => void answer(card, g)}
                      style={{ width: "1.9rem", height: "1.9rem", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", background: "var(--color-paper-raised)", cursor: "pointer", fontSize: "0.8rem" }}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h3 style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>Learning library</h3>
        {modules === null ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>Loading…</p>
        ) : modules.length === 0 ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>No learning content yet.</p>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {modules.map((m) => {
              const done = completed.has(m.id);
              return (
                <li key={m.id} style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius)", padding: "0.7rem 0.9rem", display: "flex", justifyContent: "space-between", gap: "0.8rem", alignItems: "center" }}>
                  <div>
                    <strong style={{ fontSize: "0.88rem" }}>{m.title}</strong>
                    <div style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
                      {m.kind.replace(/_/g, " ")}
                      {m.certification_credit === "coursework" ? " · counts toward certification" : ""}
                    </div>
                  </div>
                  <button
                    type="button"
                    disabled={done}
                    onClick={() => void complete(m)}
                    style={{ padding: "0.4rem 0.8rem", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", background: done ? "var(--color-paper)" : "var(--color-accent)", color: done ? "var(--color-ink-muted)" : "var(--color-accent-contrast)", cursor: done ? "default" : "pointer", fontSize: "0.78rem", whiteSpace: "nowrap" }}
                  >
                    {done ? "Completed" : "Mark complete"}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
