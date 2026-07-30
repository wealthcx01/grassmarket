/**
 * The section test (GRS-0226) — the gate a learner passes before the next section opens.
 *
 * Marking is server-side: this component collects choices and POSTs them, and the pass/fail it
 * shows is the server's answer, never its own arithmetic. The explanation for every question is
 * revealed after submitting, right or wrong, because this gate exists to teach rather than to
 * filter — a test that only says "wrong" teaches nothing.
 */

"use client";

import { useState } from "react";

import { ApiError, api } from "@/lib/api";
import type { SectionTest, SectionTestAttempt } from "@/lib/types";

export function SectionTestCard({
  slug,
  moduleId,
  test,
  sectionTitle,
  passed,
  bestScore,
  attempts,
  onPassed,
}: {
  slug: string;
  moduleId: string;
  test: SectionTest;
  sectionTitle: string;
  passed: boolean;
  bestScore?: number | null;
  attempts: number;
  onPassed: () => void;
}) {
  const [choices, setChoices] = useState<Record<number, number>>({});
  const [result, setResult] = useState<SectionTestAttempt | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const answered = test.questions.every((_, i) => choices[i] !== undefined);
  const passMarkPct = Math.round(test.pass_mark * 100);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const answers = test.questions.map((_, i) => choices[i]!);
      const attempt = await api.attemptSectionTest(slug, moduleId, answers);
      setResult(attempt);
      if (attempt.passed) onPassed();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not submit your answers.");
    } finally {
      setBusy(false);
    }
  }

  function retake() {
    setChoices({});
    setResult(null);
    setError(null);
  }

  return (
    <section
      aria-label={`${sectionTitle} section test`}
      style={{
        marginTop: "0.4rem",
        border: `1px solid ${passed ? "var(--color-accent)" : "var(--color-border)"}`,
        borderRadius: "var(--radius)",
        background: "var(--color-paper-raised)",
        padding: "0.9rem 1.1rem",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.6rem", flexWrap: "wrap" }}>
        <h3 style={{ margin: 0, fontSize: "1rem" }}>Section test</h3>
        <span className="mono" style={{ fontSize: "0.65rem", color: "var(--color-ink-faint)" }}>
          {passMarkPct}% to pass
          {attempts > 0 ? ` · ${attempts} attempt${attempts === 1 ? "" : "s"}` : null}
          {bestScore !== null && bestScore !== undefined
            ? ` · best ${Math.round(bestScore * 100)}%`
            : null}
        </span>
      </div>

      {passed ? (
        <p style={{ margin: "0.5rem 0 0", fontSize: "0.85rem", color: "var(--color-accent)", fontWeight: 600 }}>
          ✓ Passed — the next section is open.
        </p>
      ) : (
        <p style={{ margin: "0.5rem 0 0", fontSize: "0.82rem", color: "var(--color-ink-muted)" }}>
          Pass this to open the next section.
        </p>
      )}

      <ol style={{ margin: "0.8rem 0 0", paddingLeft: "1.1rem", display: "flex", flexDirection: "column", gap: "0.9rem" }}>
        {test.questions.map((q, qi) => {
          const chosen = choices[qi];
          const correct = result ? chosen === q.answer_index : null;
          return (
            <li key={q.prompt}>
              <p style={{ margin: 0, fontSize: "0.86rem", fontWeight: 600 }}>{q.prompt}</p>
              <div role="radiogroup" aria-label={q.prompt} style={{ marginTop: "0.4rem", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                {q.options.map((option, oi) => (
                  <label
                    key={option}
                    style={{ display: "flex", gap: "0.45rem", alignItems: "flex-start", fontSize: "0.83rem", cursor: result ? "default" : "pointer" }}
                  >
                    <input
                      type="radio"
                      name={`${moduleId}-q${qi}`}
                      checked={chosen === oi}
                      disabled={result !== null || busy}
                      onChange={() => setChoices((prev) => ({ ...prev, [qi]: oi }))}
                    />
                    <span>{option}</span>
                  </label>
                ))}
              </div>
              {result ? (
                <p
                  style={{
                    margin: "0.4rem 0 0",
                    fontSize: "0.8rem",
                    color: "var(--color-ink-muted)",
                    borderLeft: `2px solid ${correct ? "var(--color-accent)" : "var(--color-error)"}`,
                    paddingLeft: "0.6rem",
                  }}
                >
                  <strong style={{ color: correct ? "var(--color-accent)" : "var(--color-error)" }}>
                    {correct ? "Correct. " : "Not quite. "}
                  </strong>
                  {q.explanation}
                </p>
              ) : null}
            </li>
          );
        })}
      </ol>

      {error ? (
        <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.82rem", margin: "0.7rem 0 0" }}>
          {error}
        </p>
      ) : null}

      <div style={{ marginTop: "0.9rem", display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
        {result === null ? (
          <button
            type="button"
            className="btn btn-primary"
            disabled={!answered || busy}
            onClick={submit}
            style={{ fontSize: "0.78rem" }}
            title={answered ? undefined : "Answer every question first"}
          >
            {busy ? "Marking…" : "Submit answers"}
          </button>
        ) : (
          <>
            <span
              role="status"
              style={{ fontSize: "0.85rem", fontWeight: 600, color: result.passed ? "var(--color-accent)" : "var(--color-error)" }}
            >
              {result.passed ? "Passed" : "Not passed"} — {Math.round(result.score * 100)}%
            </span>
            {result.passed ? null : (
              <button type="button" className="btn" onClick={retake} style={{ fontSize: "0.78rem" }}>
                Try again
              </button>
            )}
          </>
        )}
      </div>
    </section>
  );
}
