/**
 * The seven Wizard Path A steps (PRD §3). Each is a controlled component over the shared
 * `AssessmentDocument`; edits go through the immutable helpers in `@/lib/doc`. Not Assessed / Not
 * Applicable are first-class choices — a subcomponent can be left unrated (unrated ≠ zero).
 */

"use client";

import { useState } from "react";

import { CommitteeReviewPanel } from "@/components/CommitteeReviewPanel";
import { DiagnosticsPanel } from "@/components/Diagnostics";
import { DualRatingPanel } from "@/components/DualRatingPanel";
import { GuidancePanel } from "@/components/GuidancePanel";
import { LiveScorePanel } from "@/components/LiveScorePanel";
import * as doc from "@/lib/doc";
import { POWER_GUIDANCE } from "@/lib/powerGuidance";
import type {
  AssessmentDocument,
  EvidenceGrade,
  LiveScore,
  MaturityLevel,
  MetricConfidence,
  NonScoreState,
  Registry,
  RegistryProfile,
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
  profiles: RegistryProfile[];
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

// Controls inherit the global form styling (border, radius, focus ring, select chevron);
// we only nudge the size down for the dense wizard.
const selectStyle: React.CSSProperties = {
  fontSize: "0.85rem",
};
// A compact secondary button for inline wizard controls (Guidance, scenario add/remove).
const smallBtn = "btn btn-secondary";
const smallBtnStyle: React.CSSProperties = { padding: "0.4rem 0.7rem", fontSize: "0.82rem" };

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "0.85rem 1rem",
        background: "var(--color-paper-raised)",
      }}
    >
      {children}
    </div>
  );
}

// --- 1. Overview ------------------------------------------------------------------------

// Suggested segments — a datalist (not an enum): the operating-model profile selector is deferred.
const SEGMENT_SUGGESTIONS = [
  "Retail broker",
  "Neobroker",
  "Multi-asset broker",
  "Wealth / advisory platform",
  "Exchange",
  "Infrastructure vendor",
];

export function OverviewStep({ document: d, update, readOnly, profiles }: StepProps) {
  const profile = d.profile ?? null;
  const operatingModel = profile?.operating_model || "retail";
  const labelStyle: React.CSSProperties = { fontSize: "0.85rem" };
  const fieldStyle: React.CSSProperties = { ...selectStyle, display: "block", width: "100%", marginTop: "0.3rem" };
  return (
    <div style={{ maxWidth: "40rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
      <p style={{ color: "var(--color-ink-muted)" }}>
        Manual assessment (Path A). Enter what you know — a partial assessment is valid and autosaves.
        Leave anything you have not assessed unrated; unrated is never treated as zero.
      </p>
      <label style={labelStyle}>
        Subject (the business being assessed)
        <input
          type="text"
          value={d.subject}
          disabled={readOnly}
          onChange={(e) => update((x) => ({ ...x, subject: e.target.value }))}
          style={fieldStyle}
        />
      </label>

      {/* Operating-model profile (GRS-0079) — SCORING-relevant: it reshapes the module set and the
          weights the assessment scores against. Retail is the default; choosing another reshapes
          the wizard. */}
      <label style={labelStyle}>
        Operating model
        <select
          value={operatingModel}
          disabled={readOnly}
          onChange={(e) =>
            update((x) => doc.setProfile(x, { operating_model: e.target.value }))
          }
          style={fieldStyle}
          title="Which operating model this business runs — reshapes the modules assessed and the weights."
        >
          {(profiles.length ? profiles : [{ key: "retail", name: "Retail" }]).map((p) => (
            <option key={p.key} value={p.key}>
              {p.name}
            </option>
          ))}
        </select>
        {operatingModel !== "retail" ? (
          <span style={{ display: "block", marginTop: "0.35rem", fontSize: "0.75rem", color: "var(--color-warn)" }}>
            Non-retail profiles are <strong>draft</strong> (weights &amp; criticals pending
            elicitation) — scores are indicative, not client-usable.
          </span>
        ) : null}
      </label>

      {/* Structured business profile (GRS-0068) — descriptive context, never a scoring input. */}
      <fieldset style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius-lg)", padding: "0.85rem 1rem", margin: 0 }}>
        <legend style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)", padding: "0 0.4rem" }}>
          Business profile <span style={{ color: "var(--color-ink-faint)" }}>· context only, not scored</span>
        </legend>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
          <label style={labelStyle}>
            Country / domicile
            <input
              type="text"
              placeholder="e.g. United Kingdom"
              value={profile?.country ?? ""}
              disabled={readOnly}
              onChange={(e) => update((x) => doc.setProfile(x, { country: e.target.value || null }))}
              style={fieldStyle}
            />
          </label>
          <label style={labelStyle}>
            Segment
            <input
              type="text"
              list="segment-suggestions"
              placeholder="e.g. Retail broker"
              value={profile?.segment ?? ""}
              disabled={readOnly}
              onChange={(e) => update((x) => doc.setProfile(x, { segment: e.target.value || null }))}
              style={fieldStyle}
            />
            <datalist id="segment-suggestions">
              {SEGMENT_SUGGESTIONS.map((s) => (
                <option key={s} value={s} />
              ))}
            </datalist>
          </label>
          <label style={labelStyle}>
            Asset classes <span style={{ color: "var(--color-ink-faint)" }}>(comma-separated)</span>
            <input
              type="text"
              placeholder="equities, funds, FX, crypto"
              defaultValue={(profile?.asset_classes ?? []).join(", ")}
              disabled={readOnly}
              onBlur={(e) => update((x) => doc.setProfile(x, { asset_classes: doc.parseList(e.target.value) }))}
              style={fieldStyle}
            />
          </label>
          <label style={labelStyle}>
            Regions served <span style={{ color: "var(--color-ink-faint)" }}>(comma-separated)</span>
            <input
              type="text"
              placeholder="UK, EU, US"
              defaultValue={(profile?.regions ?? []).join(", ")}
              disabled={readOnly}
              onBlur={(e) => update((x) => doc.setProfile(x, { regions: doc.parseList(e.target.value) }))}
              style={fieldStyle}
            />
          </label>
        </div>
        <label style={{ ...labelStyle, display: "block", marginTop: "0.75rem" }}>
          Licensing / regulatory status
          <input
            type="text"
            placeholder="e.g. FCA-authorised; MiFID II passported"
            value={profile?.licensing ?? ""}
            disabled={readOnly}
            onChange={(e) => update((x) => doc.setProfile(x, { licensing: e.target.value || null }))}
            style={fieldStyle}
          />
        </label>
      </fieldset>

      <label style={labelStyle}>
        Notes
        <textarea
          value={d.notes ?? ""}
          disabled={readOnly}
          rows={4}
          onChange={(e) => update((x) => ({ ...x, notes: e.target.value || null }))}
          style={fieldStyle}
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
            <div style={{ display: "flex", flexDirection: "column", gap: "0.55rem" }}>
              <div>
                <strong style={{ fontSize: "0.9rem" }}>{m.name}</strong>{" "}
                <span className="mono" style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
                  {m.unit} · {m.group ?? "—"}
                </span>
                <p style={{ margin: "0.25rem 0 0", fontSize: "0.8rem", color: "var(--color-ink-muted)", lineHeight: 1.45 }}>
                  {m.description}
                </p>
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

// --- 3. Powers (Helmer) ----------------------------------------------------------------

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

// Friendly labels for the Helmer lifecycle stage a power tends to arise in.
const LIFECYCLE_LABEL: Record<string, string> = {
  origination: "Origination",
  takeoff: "Take-off",
  stability: "Stability",
};

export function StrategicPowersStep({ registry, document: d, update, readOnly }: StepProps) {
  const [openExample, setOpenExample] = useState<string | null>(null);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
      <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>
        Each power carries a Benefit (the upside the leader enjoys) and a Barrier (why a rival can&rsquo;t
        copy it); the engine takes the <strong>weaker</strong> side (Helmer). Grade the evidence to model
        uncertainty — ungraded powers score as a point (labelled honestly).
      </p>
      {registry.powers.map((p) => {
        const e = doc.findPower(d, p.key);
        const g = POWER_GUIDANCE[p.key];
        const set = (
          benefit: StrengthRating,
          barrier: StrengthRating,
          bg: EvidenceGrade | null,
          rg: EvidenceGrade | null,
          be: string | null = e?.benefit_evidence ?? null,
          ba: string | null = e?.barrier_evidence ?? null,
        ) => update((x) => doc.setPower(x, doc.powerEntry(p.key, benefit, barrier, bg, rg, be, ba)));
        const showExample = openExample === p.key;
        return (
          <Card key={p.key}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.5rem", flexWrap: "wrap" }}>
              <strong style={{ fontSize: "0.9rem" }}>{p.name}</strong>
              {p.lifecycle_stage ? (
                <span className="tag" title="The lifecycle stage this power typically arises in (Helmer)">
                  {LIFECYCLE_LABEL[p.lifecycle_stage] ?? p.lifecycle_stage}
                </span>
              ) : null}
            </div>
            {/* Plain-English definition — surfaced from the registry (was previously unused). */}
            {p.description ? (
              <p style={{ margin: "0.3rem 0 0", fontSize: "0.78rem", color: "var(--color-ink-muted)", lineHeight: 1.5 }}>
                {p.description}
              </p>
            ) : null}
            <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: "0.4rem 0.6rem", marginTop: "0.55rem", alignItems: "center", maxWidth: "34rem" }}>
              <span style={{ fontSize: "0.8rem" }} title={g?.benefitHint}>Benefit</span>
              <StrengthSelect value={e?.benefit} disabled={readOnly} title={g?.benefitHint ?? "Benefit strength"} onChange={(v) => set(v, e?.barrier ?? "None", e?.benefit_grade ?? null, e?.barrier_grade ?? null)} />
              <GradeSelect value={e?.benefit_grade} disabled={readOnly} onChange={(gr) => set(e?.benefit ?? "None", e?.barrier ?? "None", gr, e?.barrier_grade ?? null)} />
              <span style={{ fontSize: "0.8rem" }} title={g?.barrierHint}>Barrier</span>
              <StrengthSelect value={e?.barrier} disabled={readOnly} title={g?.barrierHint ?? "Barrier strength"} onChange={(v) => set(e?.benefit ?? "None", v, e?.benefit_grade ?? null, e?.barrier_grade ?? null)} />
              <GradeSelect value={e?.barrier_grade} disabled={readOnly} onChange={(gr) => set(e?.benefit ?? "None", e?.barrier ?? "None", e?.benefit_grade ?? null, gr)} />
            </div>
            {/* Optional rationale per side — records WHY, using the contract's evidence fields. */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginTop: "0.5rem", maxWidth: "34rem" }}>
              <label style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
                Why this benefit?
                <input
                  type="text"
                  disabled={readOnly}
                  value={e?.benefit_evidence ?? ""}
                  placeholder="evidence / rationale"
                  onChange={(ev) => set(e?.benefit ?? "None", e?.barrier ?? "None", e?.benefit_grade ?? null, e?.barrier_grade ?? null, ev.target.value || null, e?.barrier_evidence ?? null)}
                  style={{ ...selectStyle, display: "block", width: "100%", marginTop: "0.2rem" }}
                />
              </label>
              <label style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
                Why this barrier?
                <input
                  type="text"
                  disabled={readOnly}
                  value={e?.barrier_evidence ?? ""}
                  placeholder="evidence / rationale"
                  onChange={(ev) => set(e?.benefit ?? "None", e?.barrier ?? "None", e?.benefit_grade ?? null, e?.barrier_grade ?? null, e?.benefit_evidence ?? null, ev.target.value || null)}
                  style={{ ...selectStyle, display: "block", width: "100%", marginTop: "0.2rem" }}
                />
              </label>
            </div>
            {g ? (
              <div style={{ marginTop: "0.5rem" }}>
                <button type="button" className={smallBtn} style={smallBtnStyle} onClick={() => setOpenExample(showExample ? null : p.key)}>
                  {showExample ? "Hide example" : "See an example"}
                </button>
                {showExample ? (
                  <div className="callout callout-info" style={{ marginTop: "0.5rem", fontSize: "0.8rem", lineHeight: 1.5 }}>
                    {g.example}
                  </div>
                ) : null}
              </div>
            ) : null}
          </Card>
        );
      })}
    </div>
  );
}

// --- 4. Infrastructure Deep Dive (Module Overview folded in, GRS-0106) ------------------

type SubChoice = "" | MaturityLevel | "Not Applicable" | "Not Assessed";

export function InfrastructureDeepDiveStep({ registry, document: d, update, readOnly }: StepProps) {
  const [openGuidance, setOpenGuidance] = useState<string | null>(null);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem", margin: 0 }}>
        Work each of the nine modules, front end to liquidity. A ★ marks a critical subcomponent — it
        gates the module rating (a module can&rsquo;t outrun its critical bottleneck). Each row&rsquo;s
        Guidance opens the §4 rubric anchor inline. The count by each module is your progress so far.
      </p>
      {registry.modules.map((m) => {
        const rated = m.subcomponents.filter((s) => doc.findSub(d, s.key)?.level != null).length;
        return (
        <div key={m.key}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.75rem", margin: "0 0 0.4rem" }}>
            <h3 style={{ fontSize: "1rem", margin: 0 }}>{m.name}</h3>
            <span className="mono" style={{ fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
              {rated}/{m.subcomponents.length} rated
            </span>
          </div>
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
                      <button type="button" className={smallBtn} style={smallBtnStyle} onClick={() => setOpenGuidance(openGuidance === s.key ? null : s.key)}>
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
        );
      })}
    </div>
  );
}

// --- 5b. Customer Proposition (C) — ADR-0023 --------------------------------------------

// A widget's headline presence choice. "" = untouched. Paywalled/Defective are non-present states.
type WidgetChoice = "" | "Yes" | "No" | "Paywalled" | "Defective";
const WIDGET_SCORE_FIELDS: { key: "ease" | "usability" | "depth"; label: string }[] = [
  { key: "ease", label: "Ease" },
  { key: "usability", label: "Usability" },
  { key: "depth", label: "Depth" },
];
const RARITY_TITLE: Record<string, string> = {
  Common: "Common — table stakes; a gap here is a bottleneck",
  Uncommon: "Uncommon — above baseline",
  Rare: "Rare — a differentiator when done well",
};

function widgetChoiceOf(w: { present: boolean; state?: NonScoreState | null } | undefined): WidgetChoice {
  if (!w) return "";
  if (w.present) return "Yes";
  if (w.state === "Present (Paywalled)") return "Paywalled";
  if (w.state === "Present (Defective)") return "Defective";
  return "No";
}

/** A 1–5 score select (ease / usability / depth) for a present widget. */
function ScoreSelect({
  value,
  label,
  disabled,
  onChange,
}: {
  value: number | null | undefined;
  label: string;
  disabled: boolean;
  onChange: (v: number | null) => void;
}) {
  return (
    <select
      disabled={disabled}
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
      style={selectStyle}
      title={label}
      aria-label={label}
    >
      <option value="">{label}…</option>
      {[1, 2, 3, 4, 5].map((n) => (
        <option key={n} value={n}>
          {label[0]}
          {n}
        </option>
      ))}
    </select>
  );
}

export function CustomerPropositionStep({ registry, document: d, update, readOnly }: StepProps) {
  const [openGuidance, setOpenGuidance] = useState<string | null>(null);
  const profileKey = d.profile?.operating_model ?? "retail";
  const showGrid = registry.c_widgets.length > 0 && profileKey === registry.c_widget_profile;
  const categories = Array.from(new Set(registry.c_widgets.map((w) => w.category)));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem", margin: 0 }}>
        The Customer Proposition (C) index (ADR-0023) — the ten Phase-E modules, plus the Level-1
        widget checklist. C is reported <em>alongside</em> V; it does not change V yet.
      </p>

      {registry.c_modules.map((m) => (
        <div key={m.key}>
          <h3 style={{ fontSize: "1rem", margin: "0 0 0.4rem" }}>{m.name}</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {m.subcomponents.map((s) => {
              const r = doc.findCSub(d, s.key);
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
                            if (v === "") return doc.setCSub(x, s.key, null);
                            if (v === "Not Applicable" || v === "Not Assessed")
                              return doc.setCSub(x, s.key, doc.subState(m.key, s.key, v));
                            return doc.setCSub(x, s.key, doc.subAssessed(m.key, s.key, v, r?.evidence_grade ?? "E2"));
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
                          onChange={(g) => update((x) => doc.setCSub(x, s.key, doc.subAssessed(m.key, s.key, r.level as MaturityLevel, g ?? "E1")))}
                        />
                      ) : null}
                      <button type="button" className={smallBtn} style={smallBtnStyle} onClick={() => setOpenGuidance(openGuidance === s.key ? null : s.key)}>
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

      <div>
        <h3 style={{ fontSize: "1rem", margin: "0 0 0.4rem" }}>Level-1 widget checklist</h3>
        {!showGrid ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.82rem", margin: 0 }}>
            The widget checklist is scoped to the <strong>{registry.c_widget_profile}</strong>{" "}
            operating model; it is not shown for the <strong>{profileKey}</strong> profile.
          </p>
        ) : (
          categories.map((category) => (
            <div key={category} style={{ marginBottom: "0.75rem" }}>
              <h4 style={{ fontSize: "0.82rem", margin: "0.5rem 0 0.3rem", color: "var(--color-ink-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                {category}
              </h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                {registry.c_widgets
                  .filter((w) => w.category === category)
                  .map((w) => {
                    const obs = doc.findWidget(d, w.key);
                    const choice = widgetChoiceOf(obs);
                    return (
                      <Card key={w.key}>
                        <div style={{ display: "flex", justifyContent: "space-between", gap: "0.75rem", flexWrap: "wrap", alignItems: "center" }}>
                          <div style={{ display: "flex", gap: "0.5rem", alignItems: "baseline" }}>
                            <strong style={{ fontSize: "0.82rem" }}>{w.name}</strong>
                            <span className="mono" title={RARITY_TITLE[w.rarity]} style={{ fontSize: "0.68rem", color: "var(--color-ink-muted)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-sm)", padding: "0 0.3rem" }}>
                              {w.rarity}
                            </span>
                          </div>
                          <div style={{ display: "flex", gap: "0.4rem", alignItems: "center", flexWrap: "wrap" }}>
                            <select
                              disabled={readOnly}
                              value={choice}
                              aria-label={`${w.name} presence`}
                              onChange={(e) => {
                                const v = e.target.value as WidgetChoice;
                                update((x) => {
                                  if (v === "") return doc.setWidget(x, w.key, null);
                                  if (v === "Yes")
                                    return doc.setWidget(x, w.key, doc.widgetPresent(w.key, obs ?? undefined));
                                  if (v === "No") return doc.setWidget(x, w.key, doc.widgetAbsent(w.key, null));
                                  const state: NonScoreState = v === "Paywalled" ? "Present (Paywalled)" : "Present (Defective)";
                                  return doc.setWidget(x, w.key, doc.widgetAbsent(w.key, state));
                                });
                              }}
                              style={selectStyle}
                            >
                              <option value="">— untouched —</option>
                              <option value="Yes">Present</option>
                              <option value="No">Absent</option>
                              <option value="Paywalled">Paywalled</option>
                              <option value="Defective">Defective</option>
                            </select>
                            {choice === "Yes"
                              ? WIDGET_SCORE_FIELDS.map((f) => (
                                  <ScoreSelect
                                    key={f.key}
                                    label={f.label}
                                    value={obs?.[f.key]}
                                    disabled={readOnly}
                                    onChange={(n) =>
                                      update((x) => {
                                        const cur = doc.findWidget(x, w.key);
                                        return doc.setWidget(x, w.key, doc.widgetPresent(w.key, { ...cur, [f.key]: n }));
                                      })
                                    }
                                  />
                                ))
                              : null}
                          </div>
                        </div>
                      </Card>
                    );
                  })}
              </div>
            </div>
          ))
        )}
      </div>
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
      {live?.c != null ? (
        <Card>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "1rem" }}>
            <div>
              <strong style={{ fontSize: "0.9rem" }}>Customer Proposition (C)</strong>
              <p style={{ margin: "0.2rem 0 0", fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
                Reported alongside V (ADR-0023) — a point estimate, not yet part of the composite.
              </p>
            </div>
            <span className="mono" style={{ fontSize: "1.15rem" }} title="C-index × 100">
              {(live.c * 100).toFixed(1)}
            </span>
          </div>
        </Card>
      ) : null}
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

      {/* Diagnostic visuals (GRS-0070): radar, value waterfall, weighted module table. */}
      <DiagnosticsPanel live={live} moduleLabels={moduleLabels} />

      {/* Governance (resolves the finalise blockers in-product): §9 dual rating + §8 committee. */}
      {readOnly ? null : (
        <DualRatingPanel
          assessmentId={props.assessmentId}
          moduleLabels={moduleLabels}
          onChanged={props.refreshLive}
        />
      )}
      {live?.scoreable ? <CommitteeReviewPanel assessmentId={props.assessmentId} /> : null}
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
            <button type="button" className={smallBtn} style={smallBtnStyle} onClick={() => setRows((xs) => xs.filter((_, j) => j !== i))}>
              Remove
            </button>
          </div>
        </Card>
      ))}
      <div style={{ display: "flex", gap: "0.5rem" }}>
        <button
          type="button"
          className={smallBtn}
          style={smallBtnStyle}
          onClick={() => setRows((xs) => [...xs, { key: allSubs[0]!.key, level: "Advanced" }])}
        >
          + Add scenario
        </button>
        <button type="button" className="btn btn-primary" style={smallBtnStyle} onClick={run} disabled={busy || rows.length === 0}>
          {busy ? "Evaluating…" : "Rank by ΔV"}
        </button>
      </div>
      {error ? <p style={{ color: "var(--color-error)" }}>{error}</p> : null}
      {result && !result.scoreable ? (
        <p style={{ color: "var(--color-warn)" }}>Baseline not scoreable: {result.blocking.join(" ")}</p>
      ) : null}
      {result?.scoreable ? (
        <Card>
          <h3 style={{ margin: "0 0 0.1rem", fontSize: "1rem" }}>Upgrade Priority Index</h3>
          <p style={{ margin: "0 0 0.6rem", fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
            Ranked by ΔV (score points ×100). Longest bar = the highest-leverage single upgrade.
          </p>
          {(() => {
            const maxDelta = Math.max(...result.priority_index.map((u) => Math.abs(u.delta_v)), 1e-9);
            return (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                {result.priority_index.map((u) => {
                  const pts = u.delta_v * 100;
                  const widthPct = Math.max((Math.abs(u.delta_v) / maxDelta) * 100, 1.5);
                  return (
                    <div key={u.name} style={{ display: "grid", gridTemplateColumns: "1.4rem 1fr auto", gap: "0.5rem", alignItems: "center" }}>
                      <span className="mono" style={{ fontSize: "0.72rem", color: "var(--color-ink-faint)" }}>#{u.rank}</span>
                      <div title={u.name}>
                        <div style={{ fontSize: "0.78rem", marginBottom: "0.15rem", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{u.name}</div>
                        <div style={{ height: "0.55rem", background: "var(--color-paper-sunken)", borderRadius: "var(--radius-pill)", overflow: "hidden" }}>
                          <div style={{ width: `${widthPct}%`, height: "100%", background: "var(--color-accent)", borderRadius: "var(--radius-pill)" }} />
                        </div>
                      </div>
                      <strong className="mono" style={{ fontSize: "0.8rem" }}>ΔV {pts.toFixed(2)}</strong>
                    </div>
                  );
                })}
              </div>
            );
          })()}
        </Card>
      ) : null}
    </div>
  );
}

export const WIZARD_STEPS: { title: string; component: (p: StepProps) => React.ReactElement }[] = [
  { title: "Overview", component: OverviewStep },
  { title: "Business Metrics", component: BusinessMetricsStep },
  { title: "Powers", component: StrategicPowersStep },
  { title: "Infrastructure Deep Dive", component: InfrastructureDeepDiveStep },
  { title: "Customer Proposition", component: CustomerPropositionStep },
  { title: "Summary & Interpretation", component: SummaryStep },
  { title: "Scenarios", component: ScenariosStep },
];
