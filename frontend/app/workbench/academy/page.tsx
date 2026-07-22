/**
 * Bruntsfield Academy — the LEARNER catalog (GRS-0135). Every published course, org-wide, the
 * mandatory-first one surfaced first with a "Start here" badge. This is the advisor-facing reading
 * surface; authoring lives at /workbench/courses (admin-only). Reads are org-wide — no role gate.
 */

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { ApiError, api, clearToken, getToken } from "@/lib/api";
import type { CourseVersion } from "@/lib/types";

function creditLabel(credit: string): string | null {
  return credit === "coursework" ? "Counts toward certification" : null;
}

function lessonCount(v: CourseVersion): number {
  return v.tree.modules.reduce((n, m) => n + m.lessons.length, 0);
}

export default function AcademyCatalogPage() {
  const router = useRouter();
  const [courses, setCourses] = useState<CourseVersion[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(
    (signal?: AbortSignal) =>
      api
        .listPublishedCourses(signal)
        .then(setCourses)
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0 && err.aborted) return;
          if (err instanceof ApiError && err.status === 401) {
            clearToken();
            router.replace("/login");
            return;
          }
          setError(err instanceof ApiError ? err.message : "Could not load the Academy.");
        }),
    [router],
  );

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    reload(ctrl.signal);
    return () => ctrl.abort();
  }, [router, reload]);

  // Mandatory-first course leads; then by title. The backend already sorts mandatory-first to the
  // front, but we make the ordering explicit and stable here too.
  const ordered = useMemo(() => {
    if (!courses) return null;
    return [...courses].sort((a, b) => {
      if (a.tree.mandatory_first !== b.tree.mandatory_first) return a.tree.mandatory_first ? -1 : 1;
      return a.tree.title.localeCompare(b.tree.title);
    });
  }, [courses]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.1rem" }}>
      <section>
        <p className="mono" style={{ margin: 0, fontSize: "0.72rem", letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--color-ink-muted)" }}>
          Bruntsfield Academy · your learning path
        </p>
        <h1 style={{ fontSize: "2rem", margin: "0.3rem 0 0" }}>Academy</h1>
        <p style={{ margin: "0.4rem 0 0", color: "var(--color-ink-muted)", maxWidth: "46rem" }}>
          The courses that turn the method into practice — the sales doctrine, the operational motion,
          and a deep course for every product you represent. Work through them to certify.
        </p>
      </section>

      {error ? (
        <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.9rem" }}>
          {error}
        </p>
      ) : null}

      {ordered === null && !error ? (
        <p>Loading…</p>
      ) : ordered && ordered.length === 0 ? (
        <p style={{ color: "var(--color-ink-muted)" }}>No courses published yet.</p>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(19rem, 1fr))", gap: "0.8rem" }}>
          {(ordered ?? []).map((v) => {
            const credit = creditLabel(v.tree.certification_credit);
            return (
              <Link
                key={v.slug}
                href={`/workbench/academy/${v.slug}`}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem",
                  padding: "0.9rem 1rem",
                  background: "var(--color-paper-raised)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius)",
                  textDecoration: "none",
                  color: "inherit",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem" }}>
                  <h2 style={{ margin: 0, fontSize: "1.05rem", fontFamily: "var(--font-serif)" }}>{v.tree.title}</h2>
                  {v.tree.mandatory_first ? (
                    <span className="mono" style={{ flex: "0 0 auto", fontSize: "0.6rem", fontWeight: 600, color: "var(--color-accent)", border: "1px solid var(--color-accent)", borderRadius: "999px", padding: "0.05rem 0.4rem" }}>
                      Start here
                    </span>
                  ) : null}
                </div>
                <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--color-ink-muted)", lineHeight: 1.45 }}>{v.tree.summary}</p>
                <div style={{ marginTop: "auto", paddingTop: "0.35rem", display: "flex", gap: "0.6rem", alignItems: "center", flexWrap: "wrap", fontSize: "0.68rem", color: "var(--color-ink-faint)" }}>
                  <span className="mono">{lessonCount(v)} lessons</span>
                  {credit ? <span className="tag" style={{ fontSize: "0.6rem" }}>{credit}</span> : null}
                  <span className="mono">v{v.version}</span>
                </div>
              </Link>
            );
          })}
        </div>
      )}

      <footer style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        <Link href="/workbench">← Workbench</Link>
      </footer>
    </div>
  );
}
