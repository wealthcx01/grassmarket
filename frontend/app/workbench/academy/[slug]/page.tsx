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

import { LessonBody, LessonObjective } from "@/components/workbench/LessonBody";
import { LessonReferences } from "@/components/workbench/LessonReferences";
import { SectionTestCard } from "@/components/workbench/SectionTestCard";
import { SlideDeck } from "@/components/workbench/SlideDeck";
import { ApiError, api, clearToken, getToken } from "@/lib/api";
import type { CourseVersion, Lesson, SectionProgress } from "@/lib/types";

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
  // Active-recall gate (GRS-0139): you complete a lesson by trying to recall its point, then
  // revealing the model answer — retrieval practice, not a click-through.
  const [attempt, setAttempt] = useState("");
  const [revealed, setRevealed] = useState(false);
  const question =
    lesson.check_question ??
    (lesson.measurement
      ? "Before you complete this — in your own words, how will you know you’ve applied it?"
      : "Recall the key idea of this lesson in your own words.");
  const modelAnswer = lesson.check_answer ?? lesson.measurement ?? "";
  // A rebuilt lesson teaches through its deck; a legacy one has only `body`. The layout difference
  // between them is the whole of GRS-0239 scope 1.
  const hasSlides = (lesson.slides ?? []).length > 0;
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
        {/* GRS-0239 scope 1. The DECK LEADS. Until now the objective paragraph and the lesson's
            reference cards rendered above it, so the first screen of every rebuilt lesson was
            "what you should learn" plus a list of links, with slide 1 below the fold. That is the
            founder's complaint almost verbatim, and it was a layout problem rather than a content
            one — the teaching was always there, just second.

            A legacy lesson has no slides: `SlideDeck` renders nothing, `LessonObjective` carries
            the whole lesson, and it reads exactly as it did before. */}
        {hasSlides ? (
          <>
            <SlideDeck slides={lesson.slides ?? []} label={lesson.title} />
            <LessonObjective
              body={lesson.body}
              videoRef={lesson.video_ref}
              assets={lesson.assets}
            />
            {/* Sources at the END, where a reader who has finished is looking for what to read
                next — not at the start, where they read as the content. */}
            <LessonReferences references={lesson.references} />
          </>
        ) : (
          <LessonBody
            body={lesson.body}
            videoRef={lesson.video_ref}
            references={lesson.references}
            assets={lesson.assets}
          />
        )}
      </div>
      {lesson.measurement ? (
        <p style={{ margin: "0.6rem 0 0", fontSize: "0.78rem", color: "var(--color-ink-muted)", borderLeft: "2px solid var(--color-border)", paddingLeft: "0.6rem" }}>
          <strong style={{ color: "var(--color-ink)" }}>How you know you applied it:</strong> {lesson.measurement}
        </p>
      ) : null}
      {lesson.drill_topics.length ? (
        <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.3rem", flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: "0.68rem", color: "var(--color-ink-faint)" }}>Practice topics:</span>
          {lesson.drill_topics.map((t) => (
            <span key={t} className="tag" style={{ fontSize: "0.6rem" }}>{t}</span>
          ))}
        </div>
      ) : null}
      {done ? (
        <div style={{ marginTop: "0.7rem" }}>
          <button type="button" className="btn" disabled style={{ fontSize: "0.78rem" }}>
            Completed
          </button>
        </div>
      ) : (
        <div
          style={{
            marginTop: "0.8rem",
            paddingTop: "0.7rem",
            borderTop: "1px dashed var(--color-border)",
            display: "flex",
            flexDirection: "column",
            gap: "0.5rem",
          }}
        >
          <p style={{ margin: 0, fontSize: "0.8rem", fontWeight: 600 }}>
            <span className="mono" style={{ fontSize: "0.6rem", color: "var(--color-accent)", marginRight: "0.4rem" }}>CHECK YOURSELF</span>
            {question}
          </p>
          <textarea
            value={attempt}
            onChange={(e) => setAttempt(e.target.value)}
            placeholder="Answer from memory before revealing — that’s what makes it stick."
            aria-label={`Recall answer for ${lesson.title}`}
            rows={2}
            disabled={revealed}
            style={{
              width: "100%",
              padding: "0.45rem 0.55rem",
              fontFamily: "inherit",
              fontSize: "0.82rem",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius)",
              background: "var(--color-paper)",
              resize: "vertical",
            }}
          />
          {revealed && modelAnswer ? (
            <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--color-ink-muted)", borderLeft: "2px solid var(--color-accent)", paddingLeft: "0.6rem" }}>
              <strong style={{ color: "var(--color-ink)" }}>Model answer:</strong> {modelAnswer}
            </p>
          ) : null}
          <div>
            {revealed ? (
              <button type="button" className="btn btn-primary" disabled={busy} onClick={onComplete} style={{ fontSize: "0.78rem" }}>
                {busy ? "Saving…" : "Mark complete →"}
              </button>
            ) : (
              <button
                type="button"
                className="btn"
                disabled={attempt.trim().length < 3}
                onClick={() => setRevealed(true)}
                style={{ fontSize: "0.78rem" }}
                title={attempt.trim().length < 3 ? "Write your recall attempt first" : undefined}
              >
                Reveal model answer
              </button>
            )}
          </div>
        </div>
      )}
    </article>
  );
}

export default function AcademyReaderPage() {
  const router = useRouter();
  const slug = useParams<{ slug: string }>().slug;
  const [course, setCourse] = useState<CourseVersion | null>(null);
  const [progress, setProgress] = useState<SectionProgress[]>([]);
  const [completed, setCompleted] = useState<Set<string>>(new Set());
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  const load = useCallback(
    (signal?: AbortSignal) =>
      Promise.all([
        api.getPublishedCourse(slug, signal),
        api.listLessonCompletions(slug, signal),
        api.sectionProgress(slug, signal),
      ])
        .then(([v, comps, prog]) => {
          setCourse(v);
          setCompleted(new Set(comps.map((c) => c.lesson_id)));
          setProgress(prog);
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0 && err.aborted) return;
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

  // A course is "gated" when it actually has section tests. A legacy course has none, and
  // reporting "0 / 0 sections passed" on one would be worse than the lesson count it replaces.
  const gatedSections = progress.filter((p) => p.has_test).length;
  const sectionsPassed = progress.filter((p) => p.has_test && p.passed).length;
  const gated = gatedSections > 0;
  const headlinePct = gated ? Math.round((sectionsPassed / gatedSections) * 100) : pct;

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

          {/* Progress. On a gated course the headline number is sections PASSED, not lessons
              scrolled past (GRS-0215 §6) — reading is not the same as having learned it. Lessons
              read stay visible underneath, because they are still what tells you where you are. */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.72rem", color: "var(--color-ink-muted)", marginBottom: "0.25rem" }}>
              <span className="mono">
                {gated
                  ? `${sectionsPassed} / ${gatedSections} sections passed`
                  : `${doneCount} / ${total} lessons`}
              </span>
              <span className="mono">{headlinePct}%</span>
            </div>
            <div style={{ height: "0.4rem", background: "var(--color-border)", borderRadius: "999px", overflow: "hidden" }}>
              <div style={{ width: `${headlinePct}%`, height: "100%", background: "var(--color-accent)", transition: "width 0.2s" }} />
            </div>
            {gated ? (
              <p style={{ margin: "0.3rem 0 0", fontSize: "0.68rem", color: "var(--color-ink-faint)" }}>
                {doneCount} of {total} lessons read.
              </p>
            ) : null}
          </div>

          {error ? (
            <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.85rem", margin: 0 }}>{error}</p>
          ) : null}

          {course.tree.modules.map((module) => {
            // Global lesson index so numbering runs across the whole course, not per-module.
            const startIdx = lessons.findIndex((l) => l.id === module.lessons[0]?.id);
            const standing = progress.find((p) => p.module_id === module.id);
            // Absent progress (a legacy course the endpoint knows nothing about) reads as open.
            // Locking a section because a fetch returned nothing would hide content over a bug.
            const unlocked = standing?.unlocked ?? true;
            return (
              <section key={module.id} style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                <h2 style={{ margin: "0.4rem 0 0", fontSize: "1.15rem", fontFamily: "var(--font-serif)" }}>
                  {module.title}
                  {standing?.passed ? (
                    <span className="mono" style={{ marginLeft: "0.5rem", fontSize: "0.62rem", fontWeight: 600, color: "var(--color-accent)" }}>
                      ✓ PASSED
                    </span>
                  ) : null}
                </h2>
                {unlocked ? (
                  module.lessons.map((lesson, i) => (
                    <LessonCard
                      key={lesson.id}
                      lesson={lesson}
                      index={startIdx + i}
                      done={completed.has(lesson.id)}
                      busy={busyId === lesson.id}
                      onComplete={() => complete(lesson.id)}
                    />
                  ))
                ) : (
                  <p
                    style={{
                      margin: 0,
                      padding: "0.8rem 1rem",
                      border: "1px dashed var(--color-border)",
                      borderRadius: "var(--radius)",
                      fontSize: "0.85rem",
                      color: "var(--color-ink-muted)",
                    }}
                  >
                    Locked. Pass the test at the end of the previous section to open this one.
                  </p>
                )}
                {unlocked && module.section_test ? (
                  <SectionTestCard
                    slug={slug}
                    moduleId={module.id}
                    test={module.section_test}
                    sectionTitle={module.title}
                    passed={standing?.passed ?? false}
                    bestScore={standing?.best_score}
                    attempts={standing?.attempts ?? 0}
                    onPassed={() => {
                      // Re-read rather than assume: the server owns the unlock rule, and a
                      // failure here has to say so or the next section silently stays shut.
                      api
                        .sectionProgress(slug)
                        .then(setProgress)
                        .catch(() =>
                          setError("Passed, but the section list did not refresh. Reload the page."),
                        );
                    }}
                  />
                ) : null}
              </section>
            );
          })}

          {/* On a gated course, "finished" means every section test passed — not every lesson
              scrolled. Reporting completion for reading alone is the claim GRS-0215 removed. */}
          {(gated ? sectionsPassed === gatedSections : doneCount === total && total > 0) ? (
            <section
              role="status"
              style={{
                border: "1px solid var(--color-accent)",
                borderRadius: "var(--radius)",
                padding: "0.9rem 1rem",
                background: "var(--color-paper-raised)",
                display: "flex",
                flexDirection: "column",
                gap: "0.4rem",
              }}
            >
              <p style={{ margin: 0, color: "var(--color-accent)", fontWeight: 600, fontSize: "0.9rem" }}>
                {gated
                  ? "✓ You’ve passed every section of this course."
                  : "✓ You’ve read every lesson in this course."}
              </p>
              <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--color-ink-muted)" }}>
                Reading is step one — the skill sticks when you use it. Next:
              </p>
              <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "0.85rem", display: "flex", flexDirection: "column", gap: "0.2rem" }}>
                <li>
                  <Link href="/workbench">Rehearse it live in the Practice Arena →</Link>
                </li>
                <li>
                  <Link href="/workbench/academy">Pick your next course →</Link>
                </li>
              </ul>
              {course.tree.certification_credit === "coursework" ? (
                <p style={{ margin: 0, fontSize: "0.72rem", color: "var(--color-ink-faint)" }}>
                  This course’s coursework credit is recorded toward your certification.
                </p>
              ) : null}
            </section>
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
