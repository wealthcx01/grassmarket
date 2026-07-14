/**
 * Wizard Path A orchestrator (GRS-0010). Loads the assessment (resume) + registry, holds the
 * document, DEBOUNCE-autosaves every edit (a partial document is always valid), refreshes the live
 * score, and finalises (lock). Data scoping is server-enforced; the client just carries the JWT and
 * shows only the user's own work — a 401/404 sends them back to sign in / the list.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { WIZARD_STEPS, type StepProps } from "@/components/steps";
import { ApiError, api, getToken } from "@/lib/api";
import type { Assessment, AssessmentDocument, LiveScore, Registry } from "@/lib/types";

type SaveState = "idle" | "saving" | "saved" | "error";

export function WizardClient({ id }: { id: string }) {
  const router = useRouter();
  const [registry, setRegistry] = useState<Registry | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [document, setDocument] = useState<AssessmentDocument | null>(null);
  const [step, setStep] = useState(0);
  const [save, setSave] = useState<SaveState>("idle");
  const [loadError, setLoadError] = useState<string | null>(null);

  const [live, setLive] = useState<LiveScore | null>(null);
  const [liveLoading, setLiveLoading] = useState(false);
  const [liveError, setLiveError] = useState<string | null>(null);
  const [finalising, setFinalising] = useState(false);

  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const readOnly = assessment?.state === "finalised";

  // --- Load (resume) ---
  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    Promise.all([api.registry(ctrl.signal), api.getAssessment(id, ctrl.signal)])
      .then(([reg, a]) => {
        setRegistry(reg);
        setAssessment(a);
        setDocument(a.document);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0) return;
        if (err instanceof ApiError && err.status === 401) return router.replace("/login");
        if (err instanceof ApiError && err.status === 404) return router.replace("/assessments");
        setLoadError(err instanceof ApiError ? err.message : "Could not load the assessment.");
      });
    return () => ctrl.abort();
  }, [id, router]);

  const refreshLive = useCallback(() => {
    setLiveLoading(true);
    setLiveError(null);
    api
      .liveScore(id)
      .then(setLive)
      .catch((err: unknown) => setLiveError(err instanceof ApiError ? err.message : "Live score failed."))
      .finally(() => setLiveLoading(false));
  }, [id]);

  const persist = useCallback(
    (next: AssessmentDocument) => {
      setSave("saving");
      api
        .saveAssessment(id, next)
        .then((a) => {
          setAssessment(a);
          setSave("saved");
          refreshLive();
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 409) {
            // Finalised elsewhere — reload to reflect the lock.
            api.getAssessment(id).then((a) => {
              setAssessment(a);
              setDocument(a.document);
            });
          }
          setSave("error");
        });
    },
    [id, refreshLive],
  );

  const update = useCallback(
    (fn: (d: AssessmentDocument) => AssessmentDocument) => {
      setDocument((prev) => {
        if (!prev || readOnly) return prev;
        const next = fn(prev);
        if (saveTimer.current) clearTimeout(saveTimer.current);
        saveTimer.current = setTimeout(() => persist(next), 800); // debounced autosave
        setSave("saving");
        return next;
      });
    },
    [persist, readOnly],
  );

  // Fetch a live score once loaded.
  useEffect(() => {
    if (document) refreshLive();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [document !== null]);

  async function onFinalise() {
    setFinalising(true);
    try {
      const a = await api.finaliseAssessment(id);
      setAssessment(a);
      setDocument(a.document);
      refreshLive();
    } catch (err: unknown) {
      setLiveError(err instanceof ApiError ? err.message : "Finalisation failed.");
    } finally {
      setFinalising(false);
    }
  }

  if (loadError) return <p style={{ color: "var(--color-error)" }}>{loadError}</p>;
  if (!registry || !assessment || !document) return <p>Loading…</p>;

  const Current = WIZARD_STEPS[step]!.component;
  const stepProps: StepProps = {
    registry,
    document,
    update,
    readOnly: !!readOnly,
    assessmentId: id,
    live,
    liveLoading,
    liveError,
    refreshLive,
    onFinalise,
    finalising,
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.5rem" }}>
        <div>
          <Link href="/assessments" style={{ fontSize: "0.8rem" }}>
            ← All assessments
          </Link>
          <h1 style={{ fontSize: "1.5rem", margin: "0.2rem 0 0" }}>{assessment.subject || "Untitled assessment"}</h1>
        </div>
        <SaveBadge state={save} readOnly={!!readOnly} />
      </div>

      <Stepper current={step} onSelect={setStep} />

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) 20rem", gap: "1.5rem", marginTop: "1rem" }}>
        <div>
          <h2 style={{ fontSize: "1.15rem" }}>{WIZARD_STEPS[step]!.title}</h2>
          <Current {...stepProps} />
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: "1.5rem" }}>
            <button type="button" className="btn btn-secondary" disabled={step === 0} onClick={() => setStep((s) => s - 1)}>
              ← Back
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              disabled={step === WIZARD_STEPS.length - 1}
              onClick={() => setStep((s) => s + 1)}
            >
              Next →
            </button>
          </div>
        </div>
        <LiveSummary live={live} />
      </div>
    </div>
  );
}

function Stepper({ current, onSelect }: { current: number; onSelect: (i: number) => void }) {
  return (
    <ol style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", listStyle: "none", padding: 0, margin: 0 }}>
      {WIZARD_STEPS.map((s, i) => (
        <li key={s.title}>
          <button
            type="button"
            className="pill"
            data-active={i === current}
            onClick={() => onSelect(i)}
            style={{ fontSize: "0.75rem", padding: "0.3rem 0.75rem" }}
          >
            {i + 1}. {s.title}
          </button>
        </li>
      ))}
    </ol>
  );
}

function SaveBadge({ state, readOnly }: { state: SaveState; readOnly: boolean }) {
  if (readOnly)
    return <span style={{ fontSize: "0.78rem", color: "var(--color-accent)", fontWeight: 600 }}>Finalised · locked</span>;
  const map: Record<SaveState, string> = {
    idle: "",
    saving: "Saving…",
    saved: "All changes saved",
    error: "Save failed",
  };
  return (
    <span style={{ fontSize: "0.78rem", color: state === "error" ? "var(--color-error)" : "var(--color-ink-muted)" }}>
      {map[state]}
    </span>
  );
}

/** A compact always-visible live summary in the side rail (the full panel lives on the Summary step). */
function LiveSummary({ live }: { live: LiveScore | null }) {
  return (
    <div>
      {live?.scoreable && live.v ? (
        <div className="card" style={{ padding: "0.9rem 1rem", position: "sticky", top: "1rem" }}>
          <span className="mono" style={{ fontSize: "0.66rem", letterSpacing: "0.08em", color: "var(--color-ink-muted)" }}>
            V — PLATFORM VALUE
          </span>
          <div>
            <strong className="mono" style={{ fontSize: "1.6rem" }}>
              {(live.v.p50 * 100).toFixed(1)}
            </strong>{" "}
            <span className="mono" style={{ fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>
              ({(live.v.p10 * 100).toFixed(1)}–{(live.v.p90 * 100).toFixed(1)})
            </span>
          </div>
          <p style={{ margin: "0.3rem 0 0", fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
            {live.subcomponents_assessed}/{live.subcomponents_total} rated · uncertainty {live.overall_uncertainty}
          </p>
        </div>
      ) : (
        <div style={{ border: "1px dashed var(--color-border)", borderRadius: "var(--radius)", padding: "0.75rem", fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
          Live V appears once the assessment is scoreable. Open the Summary step for details and to
          finalise.
        </div>
      )}
    </div>
  );
}
