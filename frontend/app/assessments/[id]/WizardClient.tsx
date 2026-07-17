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

import { BandDisplay } from "@/components/BandDisplay";
import { ConsumingEngagements } from "@/components/ConsumingEngagements";
import { WIZARD_STEPS, type StepProps } from "@/components/steps";
import { ApiError, api, clearToken, getToken } from "@/lib/api";
import type {
  Assessment,
  AssessmentDocument,
  LiveScore,
  Registry,
  RegistryProfile,
} from "@/lib/types";

type SaveState = "idle" | "saving" | "saved" | "error";

export function WizardClient({ id }: { id: string }) {
  const router = useRouter();
  const [registry, setRegistry] = useState<Registry | null>(null);
  const [profiles, setProfiles] = useState<RegistryProfile[]>([]);
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
  const mounted = useRef(true);
  // In-flight live-score request; a new refresh aborts the previous one so a slow earlier response
  // can never resolve last and overwrite a newer score (the autosave out-of-order race).
  const liveCtrl = useRef<AbortController | null>(null);
  const saveCtrl = useRef<AbortController | null>(null);
  const readOnly = assessment?.state === "finalised";

  // A signed-out / expired session on ANY request (not just the initial load) returns to sign in
  // rather than leaving the panel stuck on a permanent error banner.
  const handleAuth = useCallback(
    (err: unknown): boolean => {
      if (err instanceof ApiError && err.status === 401) {
        clearToken();
        router.replace("/login");
        return true;
      }
      return false;
    },
    [router],
  );

  // Cleanup on unmount: stop the pending autosave and abort any in-flight requests so nothing
  // calls setState after the component is gone.
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      if (saveTimer.current) clearTimeout(saveTimer.current);
      liveCtrl.current?.abort();
      saveCtrl.current?.abort();
    };
  }, []);

  // --- Load (resume) ---
  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    // The registry is fetched by the profile effect below (it depends on the document's profile);
    // here we load the assessment + the selectable profiles.
    Promise.all([api.getAssessment(id, ctrl.signal), api.registryProfiles(ctrl.signal)])
      .then(([a, profs]) => {
        if (!mounted.current) return;
        setAssessment(a);
        setDocument(a.document);
        setProfiles(profs);
        // A finalised assessment is opened to be READ, not filled in — land on the scored Summary
        // (the result the advisor came for), not the blank Overview form.
        if (a.state === "finalised") {
          const summary = WIZARD_STEPS.findIndex((s) => s.title.startsWith("Summary"));
          if (summary >= 0) setStep(summary);
        }
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0) return;
        if (handleAuth(err)) return;
        if (err instanceof ApiError && err.status === 404) return router.replace("/assessments");
        setLoadError(err instanceof ApiError ? err.message : "Could not load the assessment.");
      });
    return () => ctrl.abort();
  }, [id, router, handleAuth]);

  // Fetch the registry for the document's operating-model profile (GRS-0079). Re-runs only when the
  // profile KEY changes (a primitive dep) — not on every keystroke — so choosing "Exchange" reshapes
  // the module set the wizard renders. Retail (default) is the full superset.
  const profileKey = document?.profile?.operating_model || "retail";
  useEffect(() => {
    if (!getToken()) return;
    const ctrl = new AbortController();
    api
      .registry(profileKey === "retail" ? undefined : profileKey, ctrl.signal)
      .then((reg) => {
        if (mounted.current) setRegistry(reg);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0) return;
        if (handleAuth(err)) return;
        setLoadError(err instanceof ApiError ? err.message : "Could not load the registry.");
      });
    return () => ctrl.abort();
  }, [profileKey, handleAuth]);

  const refreshLive = useCallback(() => {
    liveCtrl.current?.abort();
    const ctrl = new AbortController();
    liveCtrl.current = ctrl;
    setLiveLoading(true);
    setLiveError(null);
    api
      .liveScore(id, ctrl.signal)
      .then((s) => {
        if (ctrl.signal.aborted || !mounted.current) return;
        setLive(s);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0) return; // aborted / superseded
        if (handleAuth(err)) return;
        setLiveError(err instanceof ApiError ? err.message : "Live score failed.");
      })
      .finally(() => {
        if (mounted.current && liveCtrl.current === ctrl) setLiveLoading(false);
      });
  }, [id, handleAuth]);

  const persist = useCallback(
    (next: AssessmentDocument) => {
      saveCtrl.current?.abort();
      const ctrl = new AbortController();
      saveCtrl.current = ctrl;
      setSave("saving");
      api
        .saveAssessment(id, next, ctrl.signal)
        .then((a) => {
          if (ctrl.signal.aborted || !mounted.current) return;
          setAssessment(a);
          setSave("saved");
          refreshLive();
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0) return; // aborted / superseded
          if (handleAuth(err)) return;
          if (err instanceof ApiError && err.status === 409) {
            // Finalised elsewhere — reload to reflect the lock.
            api.getAssessment(id).then((a) => {
              if (!mounted.current) return;
              setAssessment(a);
              setDocument(a.document);
            });
          }
          if (mounted.current) setSave("error");
        });
    },
    [id, refreshLive, handleAuth],
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
      if (!mounted.current) return;
      setAssessment(a);
      setDocument(a.document);
      refreshLive();
    } catch (err: unknown) {
      if (handleAuth(err)) return;
      setLiveError(err instanceof ApiError ? err.message : "Finalisation failed.");
    } finally {
      if (mounted.current) setFinalising(false);
    }
  }

  if (loadError) return <p style={{ color: "var(--color-error)" }}>{loadError}</p>;
  if (!registry || !assessment || !document) return <p>Loading…</p>;

  const Current = WIZARD_STEPS[step]!.component;
  const stepProps: StepProps = {
    registry,
    profiles,
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
          <ConsumingEngagements assessmentId={id} />
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

/** A compact always-visible live summary in the side rail (the full panel lives on the Summary step).
 * Exported for test: it must render V through BandDisplay so an unmodelled band stays an honest
 * point, never a false range (§7 / ADR-0008). */
export function LiveSummary({ live }: { live: LiveScore | null }) {
  return (
    <div>
      {live?.scoreable && live.v ? (
        <div className="card" style={{ padding: "0.9rem 1rem", position: "sticky", top: "1rem" }}>
          {/* Delegate to BandDisplay so an UNMODELLED band (modelled=false) shows an honest labelled
              point, never a falsely confident p10–p90 range (§7 / ADR-0008). */}
          <BandDisplay label="V — PLATFORM VALUE" band={live.v} />
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
