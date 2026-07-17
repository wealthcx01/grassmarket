/**
 * Bruntsfield Academy — course editor (GRS-0121). Admin-only. Edits the draft tree
 * (metadata → modules → lessons), approves AI-authored lessons (ADR-0009), publishes an immutable
 * version, and lists the retained version history. The draft is edited locally and saved explicitly;
 * publishing is a separate, gated action.
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

import { Breadcrumb } from "@/components/Breadcrumb";
import { ApiError, api, getToken } from "@/lib/api";
import type {
  CertificationCredit,
  CourseModule,
  CourseTree,
  CourseVersion,
  Lesson,
  LessonAuthor,
} from "@/lib/types";

function uid(): string {
  return crypto.randomUUID();
}

export default function CourseEditorPage() {
  const router = useRouter();
  const slug = useParams<{ slug: string }>().slug;

  const [tree, setTree] = useState<CourseTree | null>(null);
  const [versions, setVersions] = useState<CourseVersion[]>([]);
  const [latestVersion, setLatestVersion] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(
    (signal?: AbortSignal) =>
      Promise.all([api.getCourse(slug, signal), api.listCourseVersions(slug, signal)])
        .then(([course, vers]) => {
          setTree(course.draft);
          setLatestVersion(course.latest_version);
          setVersions(vers);
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0) return;
          if (err instanceof ApiError && err.status === 401) return router.replace("/login");
          if (err instanceof ApiError && err.status === 403)
            return setError("Course authoring is admin-only.");
          if (err instanceof ApiError && err.status === 404) return router.replace("/workbench/courses");
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

  function patchTree(patch: Partial<CourseTree>) {
    setTree((t) => (t ? { ...t, ...patch } : t));
  }
  function setModules(modules: CourseModule[]) {
    patchTree({ modules });
  }

  async function saveDraft() {
    if (!tree) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await api.saveCourseDraft(slug, tree);
      setNotice("Draft saved.");
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not save the draft.");
    } finally {
      setBusy(false);
    }
  }

  async function publish() {
    if (!tree) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await api.saveCourseDraft(slug, tree); // publish the current on-screen draft
      const version = await api.publishCourse(slug);
      setNotice(`Published version ${version.version}.`);
      await load();
    } catch (err: unknown) {
      // A 409 carries the AI-approval blockers verbatim (ADR-0009).
      setError(err instanceof ApiError ? err.message : "Could not publish.");
    } finally {
      setBusy(false);
    }
  }

  async function approveLesson(lessonId: string) {
    setBusy(true);
    setError(null);
    try {
      // Approve on the server against the SAVED draft, then reload so local state matches.
      await api.saveCourseDraft(slug, tree!);
      const course = await api.approveCourseLesson(slug, lessonId);
      setTree(course.draft);
      setNotice("Lesson approved.");
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not approve the lesson.");
    } finally {
      setBusy(false);
    }
  }

  if (error && !tree) return <p style={{ color: "var(--color-error)" }}>{error}</p>;
  if (!tree) return <p>Loading…</p>;

  const pendingAi = tree.modules
    .flatMap((m) => m.lessons)
    .filter((l) => l.author === "ai" && !l.approved);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem", maxWidth: "52rem" }}>
      <div>
        <Breadcrumb trail={[{ label: "Workbench", href: "/workbench" }, { label: "Courses", href: "/workbench/courses" }]} current={tree.title} />
        <h1 style={{ fontSize: "1.5rem", margin: "0.4rem 0 0.2rem" }}>{tree.title}</h1>
        <p className="mono" style={{ margin: 0, fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
          /{slug} · {latestVersion > 0 ? `v${latestVersion} published` : "never published"}
        </p>
      </div>

      {notice ? <p style={{ color: "var(--color-accent)", fontSize: "0.85rem" }}>{notice}</p> : null}
      {error ? <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.85rem" }}>{error}</p> : null}

      {/* Metadata */}
      <section style={sectionStyle}>
        <label style={labelStyle}>
          Title
          <input value={tree.title} onChange={(e) => patchTree({ title: e.target.value })} style={inputStyle} />
        </label>
        <label style={labelStyle}>
          Summary
          <input value={tree.summary} onChange={(e) => patchTree({ summary: e.target.value })} style={inputStyle} />
        </label>
        <label style={labelStyle}>
          Certification credit
          <select
            value={tree.certification_credit}
            onChange={(e) => patchTree({ certification_credit: e.target.value as CertificationCredit })}
            style={inputStyle}
          >
            <option value="none">None</option>
            <option value="coursework">Coursework</option>
          </select>
        </label>
      </section>

      {/* Modules + lessons */}
      <section style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <h2 style={{ fontSize: "1.05rem", margin: 0 }}>Modules</h2>
        {tree.modules.length === 0 ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>No modules yet.</p>
        ) : (
          tree.modules.map((mod, mi) => (
            <ModuleEditor
              key={mod.id}
              module={mod}
              onChange={(next) => setModules(tree.modules.map((m, i) => (i === mi ? next : m)))}
              onRemove={() => setModules(tree.modules.filter((_, i) => i !== mi))}
              onApprove={approveLesson}
              busy={busy}
            />
          ))
        )}
        <button
          type="button"
          className="btn"
          style={{ alignSelf: "flex-start" }}
          onClick={() =>
            setModules([
              ...tree.modules,
              { id: uid(), title: `Module ${tree.modules.length + 1}`, order: tree.modules.length, lessons: [] },
            ])
          }
        >
          + Add module
        </button>
      </section>

      {pendingAi.length > 0 ? (
        <p style={{ fontSize: "0.82rem", color: "var(--color-warn)" }}>
          {pendingAi.length} AI-authored lesson{pendingAi.length > 1 ? "s" : ""} must be approved
          before publishing (ADR-0009).
        </p>
      ) : null}

      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", borderTop: "1px solid var(--color-border)", paddingTop: "1rem" }}>
        <button type="button" className="btn" onClick={saveDraft} disabled={busy}>
          Save draft
        </button>
        <button type="button" className="btn btn-primary" onClick={publish} disabled={busy}>
          Publish version
        </button>
      </div>

      {/* Retained version history */}
      {versions.length > 0 ? (
        <section>
          <h2 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Published versions</h2>
          <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.3rem" }}>
            {versions.map((v) => (
              <li key={v.version} className="mono" style={{ fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>
                v{v.version} · {new Date(v.published_at).toLocaleString()} ·{" "}
                {v.tree.modules.reduce((n, m) => n + m.lessons.length, 0)} lessons
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <footer style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        <Link href="/workbench/courses">← All courses</Link>
      </footer>
    </div>
  );
}

function ModuleEditor({
  module,
  onChange,
  onRemove,
  onApprove,
  busy,
}: {
  module: CourseModule;
  onChange: (m: CourseModule) => void;
  onRemove: () => void;
  onApprove: (lessonId: string) => void;
  busy: boolean;
}) {
  const [lessonTitle, setLessonTitle] = useState("");
  const [lessonBody, setLessonBody] = useState("");
  const [lessonAuthor, setLessonAuthor] = useState<LessonAuthor>("human");

  function addLesson() {
    if (!lessonTitle.trim() || !lessonBody.trim()) return;
    const lesson: Lesson = {
      id: crypto.randomUUID(),
      title: lessonTitle.trim(),
      body: lessonBody.trim(),
      order: module.lessons.length,
      author: lessonAuthor,
      video_ref: null,
      drill_topics: [],
      // A human lesson is inherently approved; an AI lesson starts unapproved and is gated.
      approved: lessonAuthor === "human",
      approved_by_consultant_id: null,
      approved_at: null,
    };
    onChange({ ...module, lessons: [...module.lessons, lesson] });
    setLessonTitle("");
    setLessonBody("");
    setLessonAuthor("human");
  }

  return (
    <div style={{ ...sectionStyle, gap: "0.6rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.5rem" }}>
        <input
          value={module.title}
          onChange={(e) => onChange({ ...module, title: e.target.value })}
          style={{ ...inputStyle, flex: 1, fontWeight: 600 }}
        />
        <button type="button" className="btn" onClick={onRemove} title="Remove module">
          ×
        </button>
      </div>
      {module.lessons.length === 0 ? (
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.8rem", margin: 0 }}>No lessons.</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.35rem" }}>
          {module.lessons.map((l, li) => (
            <li key={l.id} style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem" }}>
              <span style={{ flex: 1 }}>{l.title}</span>
              {l.author === "ai" ? (
                l.approved ? (
                  <span className="mono" style={{ fontSize: "0.68rem", color: "var(--color-accent)" }}>AI · approved</span>
                ) : (
                  <>
                    <span className="mono" style={{ fontSize: "0.68rem", color: "var(--color-warn)" }}>AI · pending</span>
                    <button type="button" className="btn" disabled={busy} onClick={() => onApprove(l.id)}>
                      Approve
                    </button>
                  </>
                )
              ) : (
                <span className="mono" style={{ fontSize: "0.68rem", color: "var(--color-ink-faint)" }}>human</span>
              )}
              <button
                type="button"
                className="btn"
                title="Remove lesson"
                onClick={() => onChange({ ...module, lessons: module.lessons.filter((_, i) => i !== li) })}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", borderTop: "1px dashed var(--color-border)", paddingTop: "0.5rem" }}>
        <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
          <input value={lessonTitle} onChange={(e) => setLessonTitle(e.target.value)} placeholder="Lesson title" style={{ ...inputStyle, flex: "1 1 12rem" }} />
          <select value={lessonAuthor} onChange={(e) => setLessonAuthor(e.target.value as LessonAuthor)} style={inputStyle}>
            <option value="human">Human</option>
            <option value="ai">AI-authored</option>
          </select>
        </div>
        <textarea value={lessonBody} onChange={(e) => setLessonBody(e.target.value)} placeholder="Lesson body (markdown)" rows={2} style={{ ...inputStyle, resize: "vertical" }} />
        <button type="button" className="btn" style={{ alignSelf: "flex-start" }} onClick={addLesson} disabled={!lessonTitle.trim() || !lessonBody.trim()}>
          + Add lesson
        </button>
      </div>
    </div>
  );
}

const sectionStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "0.5rem",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius)",
  padding: "0.9rem",
  background: "var(--color-paper-raised)",
};

const labelStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "0.25rem",
  fontSize: "0.8rem",
  color: "var(--color-ink-muted)",
};

const inputStyle: React.CSSProperties = {
  padding: "0.45rem 0.6rem",
  fontFamily: "inherit",
  fontSize: "0.9rem",
  color: "var(--color-ink)",
  background: "var(--color-paper)",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius)",
};
