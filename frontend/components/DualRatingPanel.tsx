/**
 * Dual rating & consensus (Methodology §9, GRS-0062). Every assessed subcomponent needs two
 * independent raters and a resolved consensus before an assessment can finalise. This is the LEAD's
 * surface, per module that still needs it: assign a co-rater (by email), submit your own blind
 * rating, then resolve consensus once both are in. The co-rater does their part from the Workbench
 * "Rating requests" tab. Solo ratings are drafts, never deliverables.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, api } from "@/lib/api";
import { getSession } from "@/lib/session";
import type { Assessment, ModuleRatingDraft, SubcomponentRating } from "@/lib/types";

/** A module's assessed (level-set) subcomponents from the document — the ratings under review. */
function assessedForModule(doc: Assessment["document"], moduleKey: string): SubcomponentRating[] {
  return doc.subcomponents.filter((s) => s.module_key === moduleKey && s.level != null);
}
function moduleResolved(subs: SubcomponentRating[]): boolean {
  return subs.length > 0 && subs.every((s) => s.consensus === true && (s.rater_ids?.length ?? 0) >= 2);
}

export function DualRatingPanel({
  assessmentId,
  moduleLabels,
  onChanged,
}: {
  assessmentId: string;
  moduleLabels: Record<string, string>;
  onChanged: () => void;
}) {
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const mounted = useRef(true);

  const reload = useCallback(
    (signal?: AbortSignal) =>
      api
        .getAssessment(assessmentId, signal)
        .then((a) => {
          if (mounted.current) setAssessment(a);
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0 && err.aborted) return;
          setLoadError(err instanceof ApiError ? err.message : "Could not load the assessment.");
        }),
    [assessmentId],
  );

  useEffect(() => {
    mounted.current = true;
    const ctrl = new AbortController();
    void reload(ctrl.signal);
    return () => {
      mounted.current = false;
      ctrl.abort();
    };
  }, [reload]);

  if (loadError) return <p role="alert" style={{ fontSize: "0.82rem", color: "var(--color-error)" }}>{loadError}</p>;
  if (!assessment) return null;

  const modules = Array.from(new Set(assessment.document.subcomponents.filter((s) => s.level != null).map((s) => s.module_key)));
  const pending = modules
    .map((m) => ({ moduleKey: m, subs: assessedForModule(assessment.document, m) }))
    .filter((m) => !moduleResolved(m.subs));

  const total = modules.length;
  const done = total - pending.length;

  return (
    <section
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        padding: "0.9rem 1rem",
        background: "var(--color-paper-raised)",
        display: "flex",
        flexDirection: "column",
        gap: "0.7rem",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.5rem" }}>
        <h3 style={{ margin: 0, fontSize: "1rem" }}>Dual rating &amp; consensus</h3>
        <span className="mono" style={{ fontSize: "0.68rem", color: pending.length ? "var(--color-warn)" : "var(--color-accent)" }}>
          {pending.length ? `${done}/${total} modules agreed` : "all modules agreed"}
        </span>
      </div>
      <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        Every rated subcomponent needs a second independent rater and a resolved consensus (§9) before
        finalising. Assign a co-rater per module, submit your own rating, then resolve.
      </p>
      {pending.length === 0 ? (
        <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--color-accent)" }}>
          Every module with a rating has reached consensus.
        </p>
      ) : (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {pending.map((m) => (
            <ModuleConsensusRow
              key={m.moduleKey}
              assessmentId={assessmentId}
              moduleKey={m.moduleKey}
              moduleName={moduleLabels[m.moduleKey] ?? m.moduleKey}
              leadRatings={m.subs}
              onChanged={() => {
                void reload();
                onChanged();
              }}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

type Phase = "unassigned" | "need-my-submit" | "waiting-co" | "ready-to-resolve";

function ModuleConsensusRow({
  assessmentId,
  moduleKey,
  moduleName,
  leadRatings,
  onChanged,
}: {
  assessmentId: string;
  moduleKey: string;
  moduleName: string;
  leadRatings: SubcomponentRating[];
  onChanged: () => void;
}) {
  const [drafts, setDrafts] = useState<ModuleRatingDraft[] | null>(null);
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dissent, setDissent] = useState("");
  const mounted = useRef(true);

  const myId = getSession()?.consultantId;

  const loadDrafts = useCallback(
    (signal?: AbortSignal) =>
      api
        .listModuleRatings(assessmentId, moduleKey, signal)
        .then((d) => {
          if (mounted.current) setDrafts(d);
        })
        .catch(() => {
          if (mounted.current) setDrafts([]);
        }),
    [assessmentId, moduleKey],
  );

  useEffect(() => {
    mounted.current = true;
    const ctrl = new AbortController();
    void loadDrafts(ctrl.signal);
    return () => {
      mounted.current = false;
      ctrl.abort();
    };
  }, [loadDrafts]);

  const mine = drafts?.find((d) => d.owner_consultant_id === myId);
  const others = (drafts ?? []).filter((d) => d.owner_consultant_id !== myId);
  const phase: Phase =
    !drafts || drafts.length === 0
      ? "unassigned"
      : !mine?.submitted
        ? "need-my-submit"
        : others.length === 0 || !others.every((d) => d.submitted)
          ? "waiting-co"
          : "ready-to-resolve";

  async function run(fn: () => Promise<unknown>, after?: () => void) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      await loadDrafts();
      after?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  async function assignCoRater() {
    if (!email.trim()) {
      setError("Enter the co-rater's email.");
      return;
    }
    await run(async () => {
      const candidate = await api.lookupConsultantByEmail(email.trim());
      // Assign the lead (self) as the first rater, then the colleague — §9 needs two.
      if (myId) await api.assignRater(assessmentId, moduleKey, myId).catch((e) => {
        // ignore "already assigned" — the lead may already be a rater
        if (!(e instanceof ApiError && e.status === 409)) throw e;
      });
      await api.assignRater(assessmentId, moduleKey, candidate.id);
      setEmail("");
    });
  }

  async function submitMine() {
    await run(async () => {
      await api.updateMyModuleRating(assessmentId, moduleKey, leadRatings);
      await api.submitMyModuleRating(assessmentId, moduleKey);
    });
  }

  async function resolve() {
    // Resolve to the lead's ratings. If the raters differed, the backend asks for a dissent note;
    // we then re-send carrying it on the resolved ratings.
    const withDissent = dissent.trim()
      ? leadRatings.map((s) => ({ ...s, dissent_note: dissent.trim() }))
      : leadRatings;
    await run(
      () => api.resolveModuleConsensus(assessmentId, moduleKey, withDissent),
      onChanged,
    );
  }

  return (
    <li style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius)", padding: "0.6rem 0.75rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
        <strong style={{ fontSize: "0.9rem" }}>{moduleName}</strong>
        <span className="mono" style={{ fontSize: "0.66rem", color: "var(--color-ink-muted)" }}>
          {leadRatings.length} rated · {phaseLabel(phase)}
        </span>
      </div>

      {drafts === null ? null : phase === "unassigned" ? (
        <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center" }}>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Co-rater's email"
            aria-label={`Co-rater email for ${moduleName}`}
            style={inputStyle}
          />
          <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => void assignCoRater()} style={{ fontSize: "0.8rem" }}>
            {busy ? "Assigning…" : "Assign co-rater"}
          </button>
        </div>
      ) : phase === "need-my-submit" ? (
        <div style={{ marginTop: "0.5rem" }}>
          <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => void submitMine()} style={{ fontSize: "0.8rem" }}>
            {busy ? "Submitting…" : "Submit my rating"}
          </button>
          <span style={{ marginLeft: "0.5rem", fontSize: "0.76rem", color: "var(--color-ink-muted)" }}>
            (your {leadRatings.length} rating{leadRatings.length === 1 ? "" : "s"} for this module)
          </span>
        </div>
      ) : phase === "waiting-co" ? (
        <p style={{ margin: "0.45rem 0 0", fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
          Your rating is in. Waiting for the co-rater to submit theirs (blind).
        </p>
      ) : (
        <div style={{ marginTop: "0.5rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
          <input
            type="text"
            value={dissent}
            onChange={(e) => setDissent(e.target.value)}
            placeholder="Dissent note (only needed if the raters differed)"
            style={inputStyle}
          />
          <button type="button" className="btn btn-primary" disabled={busy} onClick={() => void resolve()} style={{ fontSize: "0.8rem", alignSelf: "flex-start" }}>
            {busy ? "Resolving…" : "Resolve consensus"}
          </button>
        </div>
      )}
      {error ? <p role="alert" style={{ margin: "0.4rem 0 0", fontSize: "0.78rem", color: "var(--color-error)" }}>{error}</p> : null}
    </li>
  );
}

function phaseLabel(p: Phase): string {
  return p === "unassigned"
    ? "no co-rater yet"
    : p === "need-my-submit"
      ? "submit your rating"
      : p === "waiting-co"
        ? "awaiting co-rater"
        : "ready to resolve";
}

const inputStyle: React.CSSProperties = {
  fontFamily: "inherit",
  fontSize: "0.82rem",
  padding: "0.35rem 0.5rem",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius)",
  background: "var(--color-paper)",
  color: "var(--color-ink)",
  minWidth: "14rem",
};
