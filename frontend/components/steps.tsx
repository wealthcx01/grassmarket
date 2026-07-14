/**
 * The seven Wizard Path A steps (PRD §3). Each is a controlled component over the shared
 * `AssessmentDocument`; edits go through the immutable helpers in `@/lib/doc`. Not Assessed / Not
 * Applicable are first-class choices — a subcomponent can be left unrated (unrated ≠ zero).
 */

"use client";

import { useState } from "react";

import { GuidancePanel } from "@/components/GuidancePanel";
import { LiveScorePanel } from "@/components/LiveScorePanel";
import * as doc from "@/lib/doc";
import type {
  AssessmentDocument,
  EvidenceGrade,
  LiveScore,
  MaturityLevel,
  MetricConfidence,
  Registry,
  ScenarioComparison,
  StrengthRating,
} from "@/lib/types";
import {
  EVIDENCE_GRADES,
  MATURITY_LEVELS,
  METRIC_CONFIDENCES,
  STRENGTHS,
} from "@/lib/types";
import { api, ApiError } from "@/lib/api";

export interface StepProps {
  registry: Registry;
  document: AssessmentDocument;
  update: (fn: (d: AssessmentDocument) => AssessmentDocument) => void;
  readOnly: boolean;
  assessmentId: string;
  live: LiveScore | null;
  liveLoading: boolean;
  liveError: string | null;
  refreshLive: () => void;
  onFinalise: () => void;
  finalising: boolean;
}

const selectStyle: React.CSSProperties = {
  padding: "0.35rem 0.4rem",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius)",
  background: "var(--color-paper-raised)",
  fontFamily: "inherit",
  fontSize: "0.85rem",
};

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        padding: "0.75rem 0.9rem",
        background: "var(--color-paper-raised)",
      }}
    >
      {children}
    </div>
  );
}

// --- 1. Overview ------------------------------------------------------------------------

export function OverviewStep({ document: d, update, readOnly }: StepProps) {
  return (
    <div style={{ maxWidth: "40rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
      <p style={{ color: "var(--color-ink-muted)" }}>
        Manual assessment (Path A). Enter what you know — a partial assessment is valid and autosaves.
        Leave anything you have not assessed unrated; unrated is never treated as zero.
      </p>
      <label style={{ fontSize: "0.85rem" }}>
        Subject (the business being assessed)
        <input
          type="text"
          value={d.subject}
          disabled={readOnly}
          onChange={(e) => update((x) => ({ ...x, subject: e.target.value }))}
          style={{ ...selectStyle, display: "block", width: "100%", marginTop: "0.3rem" }}
        />
      </label>
      <label style={{ fontSize: "0.85rem" }}>
        Notes
        <textarea
          value={d.notes ?? ""}
          disabled={readOnly}
          rows={4}
          onChange={(e) => update((x) => ({ ...x, notes: e.target.value || null }))}
          style={{ ...selectStyle, display: "block", width: "100%", marginTop: "0.3rem" }}
        />
      </label>
    </div>
  );
}

// --- 2. Business Metrics ----------------------------------------------------------------

export function BusinessMetricsStep({ registry, document: d, update, readOnly }: StepProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
      {registry.metrics.map((m) => {
        const entry = doc.findMetric(d, m.key);
        const notAssessed = entry?.state === "Not Assessed";
        return (
          <Card key={m.key}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
              <div>
                <strong style={{ fontSize: "0.9rem" }}>{m.name}</strong>{" "}
                <span className="mono" style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
                  {m.unit} · {m.group ?? "—"}
                </span>
              </div>
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                <input
                  type="number"
                  placeholder="value"
                  disabled={readOnly || notAssessed}
                  value={entry && entry.raw != null ? entry.raw : ""}
                  onChange={(e) =>
                    update((x) =>
                      e.target.value === ""
                        ? doc.setMetric(x, m.key, null)
                        : doc.setMetric(
                            x,
                            m.key,
                            doc.metricObserved(m.key, Number(e.target.value), entry?.confidence ?? null),
                          ),
                    )
                  }
                  style={{ ...selectStyle, width: "9rem" }}
                />
                <select
                  disabled={readOnly || notAssessed || !entry || entry.raw == null}
                  value={entry?.confidence ?? ""}
                  onChange={(e) =>
                    update((x) =>
                      doc.setMetric(
                        x,
                        m.key,
                        doc.metricObserved(m.key, entry?.raw ?? 0, (e.target.value || null) as MetricConfidence | null),
                      ),
                    )
                  }
                  style={selectStyle}
                  title="Source/recency confidence (drives §7 uncertainty)"
                >
                  <option value="">confidence…</option>
                  {METRIC_CONFIDENCES.map((c) => (
                    <option key={c} value={c}>
                      {c.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
                <label style={{ fontSize: "0.78rem", display: "flex", alignItems: "center", gap: "0.25rem" }}>
                  <input
                    type="checkbox"
                    disabled={readOnly}
                    checked={notAssessed}
                    onChange={(e) =>
                      update((x) =>
                        e.target.checked ? doc.setMetric(x, m.key, doc.metricState(m.key, "Not Assessed")) : doc.setMetric(x, m.key, null),
                      )
                    }
                  />
                  Not assessed
                </label>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}

// --- 3. Strategic Powers ----------------------------------------------------------------

function StrengthSelect({
  value,
  disabled,
  onChange,
  title,
}: {
  value: StrengthRating | undefined;
  disabled: boolean;
  onChange: (v: StrengthRating) => void;
  title: string;
}) {
  return (
    <select
      disabled={disabled}
      value={value ?? "None"}
      onChange={(e) => onChange(e.target.value as StrengthRating)}
      style={selectStyle}
      title={title}
    >
      {STRENGTHS.map((s) => (
        <option key={s} value={s}>
          {s}
        </option>
      ))}
    </select>
  );
}

function GradeSelect({
  value,
  disabled,
  onChange,
}: {
  value: EvidenceGrade | null | undefined;
  disabled: boolean;
  onChange: (v: EvidenceGrade | null) => void;
}) {
  return (
    <select
      disabled={disabled}
      value={value ?? ""}
      onChange={(e) => onChange((e.target.value || null) as EvidenceGrade | null)}
      style={selectStyle}
      title="Evidence grade (drives §7 uncertainty)"
    >
      <option value="">grade…</option>
      {EVIDENCE_GRADES.map((g) => (
        <option key={g} value={g}>
          {g}
        </option>
      ))}
    </select>
  );
}

export function StrategicPowersStep({ registry, document: d, update, readOnly }: StepProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
      <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>
        Each power carries a Benefit and a Barrier; the engine takes the weaker side (Helmer). Grade
        the evidence to model uncertainty — ungraded powers score as a point (labelled honestly).
      </p>
      {registry.powers.map((p) => {
        const e = doc.findPower(d, p.key);
        const set = (
          benefit: StrengthRating,
          barrier: StrengthRating,
          bg: EvidenceGrade | null,
          rg: EvidenceGrade | null,
        ) => update((x) => doc.setPower(x, doc.powerEntry(p.key, benefit, barrier, bg, rg)));
        return (
          <Card key={p.key}>
            <strong style={{ fontSize: "0.9rem" }}>{p.name}</strong>
            <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: "0.4rem 0.6rem", marginTop: "0.4rem", alignItems: "center", maxWidth: "34rem" }}>
              <span style={{ fontSize: "0.8rem" }}>Benefit</span>
              <StrengthSelect value={e?.benefit} disabled={readOnly} title="Benefit strength" onChange={(v) => set(v, e?.barrier ?? "None", e?.benefit_grade ?? null, e?.barrier_grade ?? null)} />
              <GradeSelect value={e?.benefit_grade} disabled={readOnly} onChange={(g) => set(e?.benefit ?? "None", e?.barrier ?? "None", g, e?.barrier_grade ?? null)} />
              <span style={{ fontSize: "0.8rem" }}>Barrier</span>
              <StrengthSelect value={e?.barrier} disabled={readOnly} title="Barrier strength" onChange={(v) => set(e?.benefit ?? "None", v, e?.benefit_grade ?? null, e?.barrier_grade ?? null)} />
              <GradeSelect value={e?.barrier_grade} disabled={readOnly} onChange={(g) => set(e?.benefit ?? "None", e?.barrier ?? "None", e?.benefit_grade ?? null, g)} />
            </div>
          </Card>
        );
      })}
    </div>
  );
}

// --- 4. Module Overview (quick pass) ----------------------------------------------------

export function ModuleOverviewStep({ registry, document: d }: StepProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>
        A quick pass over the nine modules before the deep dive. Coverage counts assessed
        subcomponents; a ★ marks a critical subcomponent (it gates the module rating).
      </p>
      {registry.modules.map((m) => {
        const rated = m.subcomponents.filter((s) => {
          const r = doc.findSub(d, s.key);
          return r?.level != null;
        }).length;
        return (
          <Card key={m.key}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <strong style={{ fontSize: "0.9rem" }}>{m.name}</strong>
              <span className="mono" style={{ fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>
                {rated}/{m.subcomponents.length} rated
              </span>
            </div>
            <p style={{ margin: "0.3rem 0 0", fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>
              {m.subcomponents.map((s) => (s.critical ? `★ ${s.name}` : s.name)).join(" · ")}
            </p>
          </Card>
        );
      })}
    </div>
  );
}

// --- 5. Infrastructure Deep Dive --------------------------------------------------------

type SubChoice = "" | MaturityLevel | "Not Applicable" | "Not Assessed";

export function InfrastructureDeepDiveStep({ registry, document: d, update, readOnly }: StepProps) {
  const [openGuidance, setOpenGuidance] = useState<string | null>(null);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {registry.modules.map((m) => (
        <div key={m.key}>
          <h3 style={{ fontSize: "1rem", margin: "0 0 0.4rem" }}>{m.name}</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {m.subcomponents.map((s) => {
              const r = doc.findSub(d, s.key);
              const choice: SubChoice = r?.level ?? (r?.state as SubChoice) ?? "";
              return (
                <Card key={s.key}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap", alignItems: "center" }}>
                    <div>
                      <strong style={{ fontSize: "0.85rem" }}>
                        {s.critical ? "★ " : ""}
                        {s.name}
                      </strong>
                      {s.description ? (
                        <p style={{ margin: "0.1rem 0 0", fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>{s.description}</p>
                      ) : null}
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                      <select
                        disabled={readOnly}
                        value={choice}
                        onChange={(e) => {
                          const v = e.target.value as SubChoice;
                          update((x) => {
                            if (v === "") return doc.setSub(x, s.key, null);
                            if (v === "Not Applicable" || v === "Not Assessed")
                              return doc.setSub(x, s.key, doc.subState(m.key, s.key, v));
                            return doc.setSub(x, s.key, doc.subAssessed(m.key, s.key, v, r?.evidence_grade ?? "E2"));
                          });
                        }}
                        style={selectStyle}
                      >
                        <option value="">— unrated —</option>
                        {MATURITY_LEVELS.map((l) => (
                          <option key={l} value={l}>
                            {l}
                          </option>
                        ))}
                        <option value="Not Applicable">Not Applicable</option>
                        <option value="Not Assessed">Not Assessed</option>
                      </select>
                      {r?.level != null ? (
                        <GradeSelect
                          value={r.evidence_grade}
                          disabled={readOnly}
                          onChange={(g) => update((x) => doc.setSub(x, s.key, doc.subAssessed(m.key, s.key, r.level as MaturityLevel, g ?? "E1")))}
                        />
                      ) : null}
                      <button type="button" onClick={() => setOpenGuidance(openGuidance === s.key ? null : s.key)} style={{ ...selectStyle, cursor: "pointer" }}>
                        {openGuidance === s.key ? "Hide guidance" : "Guidance"}
                      </button>
                    </div>
                  </div>
                  {openGuidance === s.key ? (
                    <div style={{ marginTop: "0.6rem" }}>
                      <GuidancePanel subcomponentKey={s.key} />
                    </div>
                  ) : null}
                </Card>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

// --- 6. Summary & Interpretation --------------------------------------------------------

export function SummaryStep(props: StepProps) {
  const { live, readOnly, onFinalise, finalising } = props;
  const moduleLabels = Object.fromEntries(props.registry.modules.map((m) => [m.key, m.name]));
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem", maxWidth: "42rem" }}>
      <LiveScorePanel
        score={live}
        loading={props.liveLoading}
        error={props.liveError}
        onRefresh={props.refreshLive}
        moduleLabels={moduleLabels}
      />
      {live?.scoreable ? (
        <Card>
          <h3 style={{ margin: "0 0 0.4rem", fontSize: "1rem" }}>Platform Power triad (ordinal)</h3>
          <div style={{ display: "flex", gap: "1.5rem", fontSize: "0.85rem" }}>
            <span>Economic: <strong>{live.triad_economic}</strong></span>
            <span>Perceived: <strong>{live.triad_perceived}</strong></span>
            <span>Defence: <strong>{live.triad_defence}</strong></span>
          </div>
        </Card>
      ) : null}
      {readOnly ? (
        <p style={{ color: "var(--color-accent)", fontWeight: 600 }}>
          This assessment is finalised — its inputs are locked.
        </p>
      ) : (
        <div>
          <button
            type="button"
            className="btn btn-primary"
            onClick={onFinalise}
            disabled={finalising || !live?.scoreable}
          >
            {finalising ? "Finalising…" : "Finalise & lock inputs"}
          </button>
          {!live?.scoreable ? (
            <p style={{ margin: "0.4rem 0 0", fontSize: "0.8rem", color: "var(--color-warn)" }}>
              Complete the blocking items above before finalising.
            </p>
          ) : null}
        </div>
      )}
    </div>
  );
}

// --- 7. Scenarios -----------------------------------------------------------------------

export function ScenariosStep({ registry, document: d, assessmentId }: StepProps) {
  const [rows, setRows] = useState<{ key: string; level: MaturityLevel }[]>([]);
  const [result, setResult] = useState<ScenarioComparison | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const allSubs = registry.modules.flatMap((m) => m.subcomponents.map((s) => ({ ...s, module_key: m.key })));

  async function run() {
    setBusy(true);
    setError(null);
    try {
      const scenarios = rows.map((r) => {
        const sub = allSubs.find((s) => s.key === r.key)!;
        const scenarioDoc = doc.setSub(d, r.key, doc.subAssessed(sub.module_key, r.key, r.level, "E3"));
        return { name: `Raise ${sub.name} → ${r.level}`, document: scenarioDoc };
      });
      setResult(await api.evaluateScenarios(assessmentId, scenarios));
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Scenario evaluation failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxWidth: "42rem" }}>
      <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>
        Build candidate upgrades and rank them by ΔV — the Upgrade Priority Index (score domain only;
        no currency). Each scenario raises one subcomponent to a target level against the current baseline.
      </p>
      {rows.map((r, i) => (
        <Card key={i}>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
            <select value={r.key} onChange={(e) => setRows((xs) => xs.map((x, j) => (j === i ? { ...x, key: e.target.value } : x)))} style={selectStyle}>
              {allSubs.map((s) => (
                <option key={s.key} value={s.key}>
                  {s.name}
                </option>
              ))}
            </select>
            <select value={r.level} onChange={(e) => setRows((xs) => xs.map((x, j) => (j === i ? { ...x, level: e.target.value as MaturityLevel } : x)))} style={selectStyle}>
              {MATURITY_LEVELS.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
            <button type="button" onClick={() => setRows((xs) => xs.filter((_, j) => j !== i))} style={{ ...selectStyle, cursor: "pointer" }}>
              Remove
            </button>
          </div>
        </Card>
      ))}
      <div style={{ display: "flex", gap: "0.5rem" }}>
        <button
          type="button"
          onClick={() => setRows((xs) => [...xs, { key: allSubs[0]!.key, level: "Advanced" }])}
          style={{ ...selectStyle, cursor: "pointer" }}
        >
          + Add scenario
        </button>
        <button type="button" onClick={run} disabled={busy || rows.length === 0} style={{ ...selectStyle, cursor: "pointer" }}>
          {busy ? "Evaluating…" : "Rank by ΔV"}
        </button>
      </div>
      {error ? <p style={{ color: "var(--color-error)" }}>{error}</p> : null}
      {result && !result.scoreable ? (
        <p style={{ color: "var(--color-warn)" }}>Baseline not scoreable: {result.blocking.join(" ")}</p>
      ) : null}
      {result?.scoreable ? (
        <Card>
          <h3 style={{ margin: "0 0 0.4rem", fontSize: "1rem" }}>Upgrade Priority Index</h3>
          <ol style={{ margin: 0, paddingLeft: "1.2rem" }}>
            {result.priority_index.map((u) => (
              <li key={u.name} style={{ fontSize: "0.85rem", marginBottom: "0.2rem" }}>
                {u.name} — <strong className="mono">ΔV {(u.delta_v * 100).toFixed(2)}</strong>
              </li>
            ))}
          </ol>
        </Card>
      ) : null}
    </div>
  );
}

export const WIZARD_STEPS: { title: string; component: (p: StepProps) => React.ReactElement }[] = [
  { title: "Overview", component: OverviewStep },
  { title: "Business Metrics", component: BusinessMetricsStep },
  { title: "Strategic Powers", component: StrategicPowersStep },
  { title: "Module Overview", component: ModuleOverviewStep },
  { title: "Infrastructure Deep Dive", component: InfrastructureDeepDiveStep },
  { title: "Summary & Interpretation", component: SummaryStep },
  { title: "Scenarios", component: ScenariosStep },
];
