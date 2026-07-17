/**
 * Bruntsfield Academy — course catalog authoring (GRS-0121). Admin-only: the API refuses a
 * non-admin (403) and this page surfaces that. Lists every course draft and creates new ones; the
 * per-course editor (./[slug]) edits the tree, approves AI lessons, and publishes.
 */

"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { ApiError, api, getToken } from "@/lib/api";
import type { CertificationCredit, Course } from "@/lib/types";

export default function CoursesPage() {
  const router = useRouter();
  const [courses, setCourses] = useState<Course[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [slug, setSlug] = useState("");
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [credit, setCredit] = useState<CertificationCredit>("none");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    api
      .listCourses(ctrl.signal)
      .then(setCourses)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0) return;
        if (err instanceof ApiError && err.status === 401) return router.replace("/login");
        if (err instanceof ApiError && err.status === 403) {
          setError("Course authoring is admin-only.");
          setCourses([]);
          return;
        }
        setError(err instanceof ApiError ? err.message : "Could not load courses.");
      });
    return () => ctrl.abort();
  }, [router]);

  async function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!slug.trim() || !title.trim() || !summary.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const created = await api.createCourse({
        slug: slug.trim(),
        title: title.trim(),
        summary: summary.trim(),
        certification_credit: credit,
      });
      router.push(`/workbench/courses/${created.slug}`);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not create the course.");
      setCreating(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "48rem" }}>
      <header>
        <p className="mono" style={{ margin: 0, fontSize: "0.72rem", letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--color-ink-muted)" }}>
          Bruntsfield Academy · authoring
        </p>
        <h1 style={{ fontSize: "1.6rem", margin: "0.3rem 0 0.3rem" }}>Courses</h1>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>
          Author a course, then publish it — every published version is retained, and re-publishing
          needs no deploy. AI-authored lessons must be approved before they can be published.
        </p>
      </header>

      {error ? (
        <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.9rem" }}>
          {error}
        </p>
      ) : null}

      <form onSubmit={onCreate} style={{ display: "flex", flexDirection: "column", gap: "0.6rem", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", padding: "1rem", background: "var(--color-paper-raised)" }}>
        <strong style={{ fontSize: "0.9rem" }}>New course</strong>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <input value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="slug (e.g. sales-egoist)" style={{ ...inputStyle, flex: "1 1 12rem" }} />
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" style={{ ...inputStyle, flex: "1 1 12rem" }} />
        </div>
        <input value={summary} onChange={(e) => setSummary(e.target.value)} placeholder="One-line summary" style={inputStyle} />
        <label style={{ fontSize: "0.82rem", color: "var(--color-ink-muted)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          Certification credit
          <select value={credit} onChange={(e) => setCredit(e.target.value as CertificationCredit)} style={inputStyle}>
            <option value="none">None</option>
            <option value="coursework">Coursework</option>
          </select>
        </label>
        <button type="submit" className="btn btn-primary" disabled={creating || !slug.trim() || !title.trim() || !summary.trim()} style={{ alignSelf: "flex-start" }}>
          {creating ? "Creating…" : "Create & edit"}
        </button>
      </form>

      <section>
        <h2 style={{ fontSize: "1.05rem", marginBottom: "0.75rem" }}>Catalog</h2>
        {courses === null ? (
          <p style={{ color: "var(--color-ink-muted)" }}>Loading…</p>
        ) : courses.length === 0 ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.9rem" }}>No courses yet.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {courses.map((c) => (
              <li key={c.id}>
                <Link
                  href={`/workbench/courses/${c.slug}`}
                  style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.6rem 0.8rem", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", background: "var(--color-paper-raised)", textDecoration: "none", color: "inherit" }}
                >
                  <span>
                    <strong style={{ fontSize: "0.9rem" }}>{c.draft.title}</strong>{" "}
                    <span className="mono" style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>/{c.slug}</span>
                    {c.draft.mandatory_first ? (
                      <span className="mono" style={{ marginLeft: "0.5rem", fontSize: "0.62rem", color: "var(--color-accent)", border: "1px solid var(--color-accent)", borderRadius: "999px", padding: "0 0.35rem" }}>
                        start here
                      </span>
                    ) : null}
                  </span>
                  <span className="mono" style={{ fontSize: "0.72rem", color: c.latest_version > 0 ? "var(--color-accent)" : "var(--color-ink-faint)" }}>
                    {c.latest_version > 0 ? `v${c.latest_version} published` : "unpublished"}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <footer style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        <Link href="/workbench">← Workbench</Link>
      </footer>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  padding: "0.5rem 0.7rem",
  fontFamily: "inherit",
  fontSize: "0.9rem",
  color: "var(--color-ink)",
  background: "var(--color-paper)",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius)",
};
