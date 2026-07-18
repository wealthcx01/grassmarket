/**
 * Bruntsfield Academy — the LEARNER course reader (GRS-0135). Renders the latest published version
 * of one course (org-wide read), tracks the advisor's OWN lesson completions, and lets them mark a
 * lesson done. Completing every lesson of a coursework-credit course grants the credit server-side
 * (existing certification path). Authoring is elsewhere (/workbench/courses, admin-only).
 */

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

import { ApiError, api, clearToken, getToken } from "@/lib/api";
import type { CourseVersion, Lesson } from "@/lib/types";

// Lesson bodies are prose (optionally blank-line separated) with inline **bold** emphasis. Render as
// paragraphs, building React elements for the bold spans — no markdown dependency, no HTML injection.
function inline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i}>{part.slice(2, -2)}</strong>
    ) : (
      part
    ),
  );
}

function Body({ text }: { text: string }) {
  const paras = text.split(/\n{2,}/).map((p) => p.trim()).filter(Boolean);
  return (
    <>
      {paras.map((p, i) => (
        <p key={i} style={{ margin: i === 0 ? 0 : "0.6rem 0 0", fontSize: "0.9rem", lineHeight: 1.6 }}>
          {inline(p)}
        </p>
      ))}
    </>
  );
}

function LessonCard({
  lesson,
  index,
  done,
  busy,
  onComplete,
}: {
  lesson: Lesson;
  index: number;
  done: boolean;
  busy: boolean;
  onComplete: () => void;
}) {
  return (
    <article
      style={{
        padding: "0.9rem 1.1rem",
        background: "var(--color-paper-raised)",
        border: `1px solid ${done ? "var(--color-accent)" : "var(--color-border)"}`,
        borderRadius: "var(--radius)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.6rem" }}>
        <h3 style={{ margin: 0, fontSize: "1rem" }}>
          <span className="mono" style={{ color: "var(--color-ink-faint)", marginRight: "0.5rem" }}>{index + 1}</span>
          {lesson.title}
        </h3>
        {done ? (
          <span className="mono" style={{ flex: "0 0 auto", fontSize: "0.62rem", fontWeight: 600, color: "var(--color-accent)" }}>✓ Completed</span>
        ) : null}
      </div>
      <div style={{ marginTop: "0.5rem", color: "var(--color-ink)" }}>
        <Body text={lesson.body} />
      </div>
      {lesson.measurement ? (
        <p style={{ margin: "0.6rem 0 0", fontSize: "0.78rem", color: "var(--color-ink-muted)", borderLeft: "2px solid var(--color-border)", paddingLeft: "0.6rem" }}>
          <strong style={{ color: "var(--color-ink)" }}>How you know you applied it:</strong> {lesson.measurement}
        </p>
      ) : null}
      {lesson.drill_topics.length ? (
        <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.3rem", flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: "0.68rem", color: "var(--color-ink-faint)" }}>Reinforced by drills:</span>
          {lesson.drill_topics.map((t) => (
            <span key={t} className="tag" style={{ fontSize: "0.6rem" }}>{t}</span>
          ))}
        </div>
      ) : null}
      <div style={{ marginTop: "0.7rem" }}>
        <button type="button" className="btn" disabled={done || busy} onClick={onComplete} style={{ fontSize: "0.78rem" }}>
          {done ? "Completed" : busy ? "Saving…" : "Mark complete"}
        </button>
      </div>
    </article>
  );
}

export default function AcademyReaderPage() {
  const router = useRouter();
  const slug = useParams<{ slug: string }>().slug;
  const [course, setCourse] = useState<CourseVersion | null>(null);
  const [completed, setCompleted] = useState<Set<string>>(new Set());
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  const load = useCallback(
    (signal?: AbortSignal) =>
      Promise.all([api.getPublishedCourse(slug, signal), api.listLessonCompletions(slug, signal)])
        .then(([v, comps]) => {
          setCourse(v);
          setCompleted(new Set(comps.map((c) => c.lesson_id)));
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0) return;
          if (err instanceof ApiError && err.status === 401) {
            clearToken();
            router.replace("/login");
            return;
          }
          if (err instanceof ApiError && err.status === 404) {
            setNotFound(true);
            return;
          }
          setError(err instanceof ApiError ? err.message : "Could not load the course.");
        }),
    [slug, router],
  );

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    load(ctrl.signal);
    return () => ctrl.abort();
  }, [router, load]);

  const lessons = useMemo(
    () => (course ? course.tree.modules.flatMap((m) => m.lessons) : []),
    [course],
  );
  const total = lessons.length;
  const doneCount = lessons.filter((l) => completed.has(l.id)).length;
  const pct = total ? Math.round((doneCount / total) * 100) : 0;

  async function complete(lessonId: string) {
    setBusyId(lessonId);
    setError(null);
    try {
      await api.completeLesson(slug, lessonId);
      setCompleted((prev) => new Set(prev).add(lessonId));
    } catch (err: unknown) {
      // A 409 means it was already done elsewhere — treat as done, not an error.
      if (err instanceof ApiError && err.status === 409) {
        setCompleted((prev) => new Set(prev).add(lessonId));
      } else {
        setError(err instanceof ApiError ? err.message : "Could not record completion.");
      }
    } finally {
      setBusyId(null);
    }
  }

  if (notFound) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
        <h1 style={{ fontSize: "1.6rem", margin: 0 }}>Course not found</h1>
        <p style={{ color: "var(--color-ink-muted)" }}>This course isn’t published, or the link is wrong.</p>
        <p style={{ fontSize: "0.85rem" }}>
          <Link href="/workbench/academy">← Back to the Academy</Link>
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.1rem", maxWidth: "48rem" }}>
      <nav style={{ fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>
        <Link href="/workbench/academy">Academy</Link> / {course?.tree.title ?? slug}
      </nav>

      {course ? (
        <>
          <header>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
              <h1 style={{ fontSize: "1.9rem", margin: 0 }}>{course.tree.title}</h1>
              {course.tree.mandatory_first ? (
                <span className="mono" style={{ fontSize: "0.62rem", fontWeight: 600, color: "var(--color-accent)", border: "1px solid var(--color-accent)", borderRadius: "999px", padding: "0.1rem 0.45rem" }}>
                  Start here
                </span>
              ) : null}
            </div>
            <p style={{ margin: "0.4rem 0 0", color: "var(--color-ink-muted)" }}>{course.tree.summary}</p>
          </header>

          {/* Progress */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.72rem", color: "var(--color-ink-muted)", marginBottom: "0.25rem" }}>
              <span className="mono">{doneCount} / {total} lessons</span>
              <span className="mono">{pct}%</span>
            </div>
            <div style={{ height: "0.4rem", background: "var(--color-border)", borderRadius: "999px", overflow: "hidden" }}>
              <div style={{ width: `${pct}%`, height: "100%", background: "var(--color-accent)", transition: "width 0.2s" }} />
            </div>
          </div>

          {error ? (
            <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.85rem", margin: 0 }}>{error}</p>
          ) : null}

          {course.tree.modules.map((module) => {
            // Global lesson index so numbering runs across the whole course, not per-module.
            const startIdx = lessons.findIndex((l) => l.id === module.lessons[0]?.id);
            return (
              <section key={module.id} style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                <h2 style={{ margin: "0.4rem 0 0", fontSize: "1.15rem", fontFamily: "var(--font-serif)" }}>{module.title}</h2>
                {module.lessons.map((lesson, i) => (
                  <LessonCard
                    key={lesson.id}
                    lesson={lesson}
                    index={startIdx + i}
                    done={completed.has(lesson.id)}
                    busy={busyId === lesson.id}
                    onComplete={() => complete(lesson.id)}
                  />
                ))}
              </section>
            );
          })}

          {doneCount === total && total > 0 ? (
            <p role="status" style={{ color: "var(--color-accent)", fontWeight: 600, fontSize: "0.9rem" }}>
              ✓ You’ve completed every lesson in this course.
              {course.tree.certification_credit === "coursework" ? " The coursework credit is recorded." : ""}
            </p>
          ) : null}
        </>
      ) : !error ? (
        <p>Loading…</p>
      ) : (
        <p role="alert" style={{ color: "var(--color-error)" }}>{error}</p>
      )}

      <footer style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        <Link href="/workbench/academy">← Academy</Link> · <Link href="/workbench">Workbench</Link>
      </footer>
    </div>
  );
}
