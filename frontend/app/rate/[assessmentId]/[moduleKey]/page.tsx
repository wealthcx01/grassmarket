/**
 * Co-rater's blind rating of one module (Methodology §9, GRS-0062). A consultant assigned as a
 * second rater independently rates the module's subcomponents here — they never see the lead's
 * ratings (blind by construction, server-enforced). Submitting locks the draft; the lead then
 * resolves consensus. Reachable from the Workbench "Rating requests" tab.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

import { ApiError, api, getToken } from "@/lib/api";
import {
  EVIDENCE_GRADES,
  MATURITY_LEVELS,
  type EvidenceGrade,
  type MaturityLevel,
  type RegistryModule,
  type SubcomponentRating,
} from "@/lib/types";

type Row = { key: string; name: string; level: MaturityLevel | ""; grade: EvidenceGrade };

export default function CoRaterModulePage() {
  const router = useRouter();
  const params = useParams<{ assessmentId: string; moduleKey: string }>();
  const assessmentId = params.assessmentId;
  const moduleKey = params.moduleKey;

  const [module, setModule] = useState<RegistryModule | null>(null);
  const [rows, setRows] = useState<Row[]>([]);
  const [submitted, setSubmitted] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [notice, setNotice] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const mounted = useRef(true);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      try {
        const [registry, draft] = await Promise.all([
          // The full superset view; profile-aware co-rating of non-retail assessments is a follow-up.
          api.registry(undefined, signal),
          api.getMyModuleRating(assessmentId, moduleKey, signal),
        ]);
        if (!mounted.current) return;
        const mod = registry.modules.find((m) => m.key === moduleKey) ?? null;
        setModule(mod);
        setSubmitted(draft.submitted);
        const byKey = new Map(draft.ratings.map((r) => [r.subcomponent_key, r]));
        setRows(
          (mod?.subcomponents ?? []).map((s) => {
            const existing = byKey.get(s.key);
            return {
              key: s.key,
              name: s.name,
              level: (existing?.level as MaturityLevel | undefined) ?? "",
              grade: (existing?.evidence_grade as EvidenceGrade | undefined) ?? "E3",
            };
          }),
        );
      } catch (err) {
        if (err instanceof ApiError && err.status === 0 && err.aborted) return;
        if (err instanceof ApiError && err.status === 401) {
          router.replace("/login");
          return;
        }
        setLoadError(
          err instanceof ApiError ? err.message : "Could not load this rating request.",
        );
      }
    },
    [assessmentId, moduleKey, router],
  );

  useEffect(() => {
    mounted.current = true;
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    void load(ctrl.signal);
    return () => {
      mounted.current = false;
      ctrl.abort();
    };
  }, [load, router]);

  function ratings(): SubcomponentRating[] {
    return rows
      .filter((r) => r.level !== "")
      .map((r) => ({
        module_key: moduleKey,
        subcomponent_key: r.key,
        level: r.level as MaturityLevel,
        evidence_grade: r.grade,
      }));
  }

  async function saveDraft() {
    setBusy(true);
    setNotice(null);
    try {
      await api.updateMyModuleRating(assessmentId, moduleKey, ratings());
      setNotice({ kind: "ok", text: "Draft saved." });
    } catch (err) {
      setNotice({ kind: "error", text: err instanceof ApiError ? err.message : "Could not save." });
    } finally {
      setBusy(false);
    }
  }

  async function submit() {
    setBusy(true);
    setNotice(null);
    try {
      await api.updateMyModuleRating(assessmentId, moduleKey, ratings());
      await api.submitMyModuleRating(assessmentId, moduleKey);
      setSubmitted(true);
      setNotice({ kind: "ok", text: "Submitted. Thank you — the lead will resolve consensus." });
    } catch (err) {
      setNotice({ kind: "error", text: err instanceof ApiError ? err.message : "Could not submit." });
    } finally {
      setBusy(false);
    }
  }

  if (loadError) return <p style={{ color: "var(--color-error)" }}>{loadError}</p>;
  if (!module) return <p>Loading…</p>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.1rem", maxWidth: "46rem" }}>
      <div>
        <Link href="/workbench" style={{ fontSize: "0.82rem" }}>
          ← Workbench · Rating requests
        </Link>
        <p className="eyebrow" style={{ marginTop: "0.5rem" }}>
          Dual rating · your independent opinion
        </p>
        <h1 style={{ fontSize: "1.6rem", margin: "0.3rem 0 0.4rem" }}>{module.name}</h1>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "0.92rem", lineHeight: 1.55 }}>
          Rate what you independently judge, blind to the lead&rsquo;s ratings (§9). Leave anything you
          didn&rsquo;t assess unrated. Once you submit, your draft locks and the lead resolves consensus.
        </p>
      </div>

      {submitted ? (
        <p style={{ color: "var(--color-accent)", fontWeight: 600 }}>
          You have submitted this rating — it is locked pending the lead&rsquo;s consensus.
        </p>
      ) : null}

      <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {rows.map((r, i) => (
          <li
            key={r.key}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: "0.75rem",
              flexWrap: "wrap",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius)",
              padding: "0.55rem 0.75rem",
              background: "var(--color-paper-raised)",
            }}
          >
            <span style={{ fontSize: "0.88rem" }}>{r.name}</span>
            <span style={{ display: "flex", gap: "0.4rem" }}>
              <select
                aria-label={`Level for ${r.name}`}
                value={r.level}
                disabled={submitted}
                onChange={(e) => setRows((cur) => cur.map((x, j) => (j === i ? { ...x, level: e.target.value as MaturityLevel | "" } : x)))}
                style={selectStyle}
              >
                <option value="">— unrated —</option>
                {MATURITY_LEVELS.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
              <select
                aria-label={`Evidence grade for ${r.name}`}
                value={r.grade}
                disabled={submitted || r.level === ""}
                onChange={(e) => setRows((cur) => cur.map((x, j) => (j === i ? { ...x, grade: e.target.value as EvidenceGrade } : x)))}
                style={selectStyle}
              >
                {EVIDENCE_GRADES.map((g) => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </span>
          </li>
        ))}
      </ul>

      {!submitted ? (
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => void saveDraft()}>
            {busy ? "Saving…" : "Save draft"}
          </button>
          <button type="button" className="btn btn-primary" disabled={busy} onClick={() => void submit()}>
            {busy ? "Submitting…" : "Submit my rating"}
          </button>
        </div>
      ) : null}

      {notice ? (
        <p
          role={notice.kind === "error" ? "alert" : undefined}
          style={{ fontSize: "0.85rem", color: notice.kind === "error" ? "var(--color-error)" : "var(--color-accent)" }}
        >
          {notice.text}
        </p>
      ) : null}
    </div>
  );
}

const selectStyle: React.CSSProperties = {
  fontFamily: "inherit",
  fontSize: "0.82rem",
  padding: "0.3rem 0.4rem",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius)",
  background: "var(--color-paper)",
  color: "var(--color-ink)",
};
