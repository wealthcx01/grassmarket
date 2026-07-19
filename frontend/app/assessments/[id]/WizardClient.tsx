/**
 * Wizard Path A orchestrator (GRS-0010). Loads the assessment (resume) + registry, holds the
 * document, DEBOUNCE-autosaves every edit (a partial document is always valid), refreshes the live
 * score, and finalises (lock). Data scoping is server-enforced; the client just carries the JWT and
 * shows only the user's own work — a 401/404 sends them back to sign in / the list.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { BandDisplay } from "@/components/BandDisplay";
import { ConsumingEngagements } from "@/components/ConsumingEngagements";
import { ProvenanceBadge } from "@/components/ProvenanceBadge";
import { WIZARD_STEPS, type StepProps } from "@/components/steps";
import { Breadcrumb } from "@/components/Breadcrumb";
import { WizardSuggestionsPanel } from "@/components/WizardSuggestionsPanel";
import { ApiError, api, clearToken, getToken } from "@/lib/api";
import { setSub, subAssessed } from "@/lib/doc";
import type {
  Assessment,
  AssessmentDocument,
  LiveScore,
  Registry,
  RegistryProfile,
  WizardSuggestion,
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
  const [cloningSandbox, setCloningSandbox] = useState(false);

  // Wizard input assistant (GRS-0101/0136): deterministic rule-based suggestions + the ids the advisor has dismissed.
  const [suggestions, setSuggestions] = useState<WizardSuggestion[]>([]);
  const [suggesterVersion, setSuggesterVersion] = useState("");
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

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
        // 404 (no such assessment) or 422 (malformed id in the URL) → not a real record; bounce to
        // the portfolio rather than leak a raw "Request failed (422)" (GRS-0143).
        if (err instanceof ApiError && (err.status === 404 || err.status === 422))
          return router.replace("/assessments");
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

  // Suggestions over the persisted document — refreshed on load and after each autosave, so a
  // coverage nudge disappears as coverage grows. A failure is silent (assistance is non-essential).
  const refreshSuggestions = useCallback(() => {
    api
      .wizardSuggestions(id)
      .then((r) => {
        if (!mounted.current) return;
        setSuggestions(r.suggestions);
        setSuggesterVersion(r.suggester_version);
      })
      .catch(() => {});
  }, [id]);

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
          refreshSuggestions();
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
    [id, refreshLive, refreshSuggestions, handleAuth],
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

  // Accept a PREFILL: apply the proposed level as an ordinary edit (the advisor can change it after),
  // then hide the suggestion. This is the visible approve step — nothing applied without it.
  const acceptSuggestion = useCallback(
    (s: WizardSuggestion) => {
      if (s.kind === "prefill" && s.module_key && s.subcomponent_key && s.proposed_level) {
        update((d) =>
          setSub(
            d,
            s.subcomponent_key!,
            subAssessed(s.module_key!, s.subcomponent_key!, s.proposed_level!, "E1"),
          ),
        );
      }
      setDismissed((prev) => new Set(prev).add(s.id));
    },
    [update],
  );

  const dismissSuggestion = useCallback((sid: string) => {
    setDismissed((prev) => new Set(prev).add(sid));
  }, []);

  // Fetch a live score + suggestions once loaded.
  useEffect(() => {
    if (document) {
      refreshLive();
      refreshSuggestions();
    }
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

  // Solo-path escape hatch (GRS-0148): clone this production assessment into a self-approvable
  // sandbox copy (carrying the full in-progress document, incl. profile) and open it, so a working-
  // solo advisor can finalise and see the real watermarked deliverable without a co-rater/committee.
  // Composes two shipped endpoints — no new backend.
  async function previewInSandbox() {
    if (!assessment || !document) return;
    setCloningSandbox(true);
    try {
      const copy = await api.createAssessment(
        assessment.subject,
        "sandbox",
        assessment.entity_id ?? null,
      );
      await api.saveAssessment(copy.id, document);
      router.push(`/assessments/${copy.id}`);
    } catch (err: unknown) {
      if (handleAuth(err)) return;
      setLiveError(err instanceof ApiError ? err.message : "Could not create the sandbox preview.");
      if (mounted.current) setCloningSandbox(false);
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
    provenance: assessment.provenance,
    onPreviewInSandbox: previewInSandbox,
    previewingSandbox: cloningSandbox,
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.5rem" }}>
        <div>
          <Breadcrumb
            trail={[{ label: "Your Portfolio", href: "/assessments" }]}
            current={assessment.subject || "Untitled assessment"}
          />
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap", margin: "0.35rem 0 0" }}>
            <h1 style={{ fontSize: "1.5rem", margin: 0 }}>{assessment.subject || "Untitled assessment"}</h1>
            <ProvenanceBadge provenance={assessment.provenance} />
          </div>
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
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <LiveSummary live={live} />
          {!readOnly ? (
            <WizardSuggestionsPanel
              suggestions={suggestions.filter((s) => !dismissed.has(s.id))}
              version={suggesterVersion}
              onAccept={acceptSuggestion}
              onDismiss={dismissSuggestion}
            />
          ) : null}
        </div>
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
    <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem", position: "sticky", top: "1rem" }}>
      {live?.scoreable && live.v ? (
        <div className="card" style={{ padding: "0.9rem 1rem" }}>
          {/* Delegate to BandDisplay so an UNMODELLED band (modelled=false) shows an honest labelled
              point, never a falsely confident p10–p90 range (§7 / ADR-0008). */}
          <BandDisplay label="V — PLATFORM VALUE" band={live.v} />
          <p style={{ margin: "0.3rem 0 0", fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
            {live.subcomponents_assessed}/{live.subcomponents_total} rated · uncertainty {live.overall_uncertainty}
          </p>
        </div>
      ) : (
        <div className="card" style={{ padding: "0.85rem 1rem", position: "sticky", top: "1rem" }}>
          <p style={{ margin: 0, fontWeight: 600, fontSize: "0.82rem" }}>Live score</p>
          {live && live.blocking.length > 0 ? (
            <>
              <p style={{ margin: "0.3rem 0 0.4rem", fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>
                A Platform Value score appears once you&rsquo;ve done these:
              </p>
              <ul style={{ margin: 0, paddingLeft: "1.05rem", fontSize: "0.78rem", color: "var(--color-ink-muted)", lineHeight: 1.5 }}>
                {live.blocking.map((b) => (
                  <li key={b} style={{ marginBottom: "0.2rem" }}>
                    {b}
                  </li>
                ))}
              </ul>
              <p style={{ margin: "0.45rem 0 0", fontSize: "0.72rem", color: "var(--color-ink-faint)" }}>
                {live.subcomponents_assessed}/{live.subcomponents_total} subcomponents rated so far.
              </p>
            </>
          ) : (
            <p style={{ margin: "0.3rem 0 0", fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>
              Start rating the steps — the live score updates as you go.
            </p>
          )}
        </div>
      )}

      {/* Customer Proposition Index (C) — surfaced alongside V on every step (GRS-0108), so the widget-
          driven view of how good the platform actually is stays front-of-mind, not buried. Reported
          alongside V (ADR-0023), not folded into it. Shown as soon as C is scoreable. */}
      {live?.c != null ? (
        <div className="card" style={{ padding: "0.9rem 1rem" }}>
          <p style={{ margin: 0, fontSize: "0.7rem", fontWeight: 600, letterSpacing: "0.04em", color: "var(--color-ink-muted)" }}>
            C — CUSTOMER PROPOSITION
          </p>
          <div style={{ display: "flex", alignItems: "baseline", gap: "0.4rem", marginTop: "0.2rem" }}>
            <strong className="mono" style={{ fontSize: "1.35rem" }}>{(live.c * 100).toFixed(0)}</strong>
            <span style={{ fontSize: "0.72rem", color: "var(--color-ink-faint)" }}>/ 100</span>
          </div>
          <p style={{ margin: "0.25rem 0 0", fontSize: "0.7rem", color: "var(--color-ink-faint)" }}>
            From the widget checklist + Ease/Usability/Depth. Reported alongside V.
          </p>
        </div>
      ) : null}
    </div>
  );
}
