"use client";

/**
 * Learning library + Power Drills (GRS-0024/0027). Completing a coursework module updates the
 * advisor's certification evidence self-service (server-side); the drill grades reschedule the card
 * by SM-2. AI-drafted quizzes are not surfaced here — they reach advisors only after admin approval.
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

import { ApiError, api } from "@/lib/api";
import type { CourseVersion, DrillCard, LearningModule } from "@/lib/types";

const GRADES = [0, 1, 2, 3, 4, 5];

// One spaced-repetition drill (GRS-0139): a real flashcard — try to recall the answer to the
// question, reveal the model answer, then self-grade. Falls back to the topic for legacy cards.
function DrillItem({ card, onGrade }: { card: DrillCard; onGrade: (grade: number) => void }) {
  const [revealed, setRevealed] = useState(false);
  const question = card.prompt || `Recall the key idea of ${card.topic}.`;
  return (
    <li style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius)", padding: "0.7rem 0.9rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: "0.6rem", alignItems: "baseline" }}>
        <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>{question}</span>
        <span className="mono" style={{ fontSize: "0.66rem", color: "var(--color-ink-muted)", whiteSpace: "nowrap" }}>streak {card.streak}</span>
      </div>
      <div className="mono" style={{ fontSize: "0.6rem", color: "var(--color-ink-faint)", marginTop: "0.15rem" }}>{card.topic}</div>
      {revealed ? (
        <>
          {card.answer ? (
            <p style={{ margin: "0.5rem 0 0", fontSize: "0.8rem", color: "var(--color-ink-muted)", borderLeft: "2px solid var(--color-accent)", paddingLeft: "0.6rem" }}>
              <strong style={{ color: "var(--color-ink)" }}>Answer:</strong> {card.answer}
            </p>
          ) : null}
          <div style={{ display: "flex", gap: "0.3rem", marginTop: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
            <span style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>How well did you recall it?</span>
            {GRADES.map((g) => (
              <button
                key={g}
                type="button"
                aria-label={`Grade ${g} for ${card.topic}`}
                onClick={() => onGrade(g)}
                style={{ width: "1.9rem", height: "1.9rem", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", background: "var(--color-paper-raised)", cursor: "pointer", fontSize: "0.8rem" }}
              >
                {g}
              </button>
            ))}
          </div>
        </>
      ) : (
        <button type="button" className="btn" onClick={() => setRevealed(true)} style={{ marginTop: "0.5rem", fontSize: "0.74rem" }}>
          Reveal answer
        </button>
      )}
    </li>
  );
}

function lessonCount(v: CourseVersion): number {
  return v.tree.modules.reduce((n, m) => n + m.lessons.length, 0);
}

export function LearningDrillsPanel() {
  const [modules, setModules] = useState<LearningModule[] | null>(null);
  const [courses, setCourses] = useState<CourseVersion[] | null>(null);
  const [completed, setCompleted] = useState<Set<string>>(new Set());
  const [due, setDue] = useState<DrillCard[] | null>(null);
  const [notice, setNotice] = useState<{ kind: "ok" | "error"; text: string } | null>(null);

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const [mods, dueCards, published] = await Promise.all([
        api.learningModules(signal),
        api.dueDrillCards(signal),
        api.listPublishedCourses(signal),
      ]);
      setModules(mods);
      setDue(dueCards);
      // Mandatory-first course leads the Academy strip.
      setCourses(
        [...published].sort((a, b) =>
          a.tree.mandatory_first !== b.tree.mandatory_first
            ? a.tree.mandatory_first
              ? -1
              : 1
            : a.tree.title.localeCompare(b.tree.title),
        ),
      );
    } catch (err) {
      if (err instanceof ApiError && err.status === 0 && err.aborted) return;
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
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.6rem", marginBottom: "0.6rem" }}>
          <h3 style={{ fontSize: "1rem", margin: 0 }}>Bruntsfield Academy</h3>
          <Link href="/workbench/academy" style={{ fontSize: "0.78rem" }}>All courses →</Link>
        </div>
        {courses === null ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>Loading…</p>
        ) : courses.length === 0 ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>No courses published yet.</p>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {courses.map((v) => (
              <li key={v.slug}>
                <Link
                  href={`/workbench/academy/${v.slug}`}
                  style={{ display: "flex", justifyContent: "space-between", gap: "0.8rem", alignItems: "center", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", padding: "0.7rem 0.9rem", textDecoration: "none", color: "inherit" }}
                >
                  <div>
                    <strong style={{ fontSize: "0.88rem" }}>{v.tree.title}</strong>
                    {v.tree.mandatory_first ? (
                      <span className="mono" style={{ marginLeft: "0.5rem", fontSize: "0.6rem", fontWeight: 600, color: "var(--color-accent)", border: "1px solid var(--color-accent)", borderRadius: "999px", padding: "0.05rem 0.35rem" }}>Start here</span>
                    ) : null}
                    <div style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
                      {lessonCount(v)} lessons{v.tree.certification_credit === "coursework" ? " · counts toward certification" : ""}
                    </div>
                  </div>
                  <span aria-hidden style={{ color: "var(--color-ink-muted)" }}>→</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h3 style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>Power drills due</h3>
        {due === null ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>Loading…</p>
        ) : due.length === 0 ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>Nothing due — nice work.</p>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {due.map((card) => (
              <DrillItem key={card.id} card={card} onGrade={(g) => void answer(card, g)} />
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
