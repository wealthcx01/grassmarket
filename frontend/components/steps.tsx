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
import { RatingControl } from "@/components/RatingControl";
import { StrengthControl } from "@/components/StrengthControl";
import * as doc from "@/lib/doc";
import { POWER_GUIDANCE } from "@/lib/powerGuidance";
import type {
  AssessmentDocument,
  BrokeragePortfolioEntry,
  EvidenceGrade,
  LiveScore,
  MaturityLevel,
  MetricConfidence,
  NonScoreState,
  PowerEntry,
  RecordProvenance,
  Registry,
  RegistryProfile,
  ScenarioComparison,
  StrengthRating,
} from "@/lib/types";
import {
  EVIDENCE_GRADES,
  MATURITY_LEVELS,
  METRIC_CONFIDENCES,
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
  // Solo-path escape hatch (GRS-0148): a production record needs a co-rater + committee to finalise;
  // a working-solo advisor can clone it to a self-approvable sandbox to see the real deliverable.
  provenance: RecordProvenance;
  onPreviewInSandbox: () => void;
  previewingSandbox: boolean;
  // Whether the assessment's operating-model profile scores on a client-usable set (GRS-0156) —
  // gates the "indicative, not client-usable" caveat on the score views.
  clientUsable: boolean;
  // The finalised portfolio row (GRS-0166): the immutable run's v_index + stored band, so the
  // Summary panel headlines the SAME locked score the portfolio and deliverable quote. Null while
  // draft/in-progress (the live view applies).
  finalEntry?: BrokeragePortfolioEntry | null;
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
        {operatingModel !== "retail" &&
        !(profiles.find((p) => p.key === operatingModel)?.client_usable ?? false) ? (
          <span style={{ display: "block", marginTop: "0.35rem", fontSize: "0.75rem", color: "var(--color-warn)" }}>
            This profile is <strong>draft</strong> (weights &amp; criticals pending elicitation) —
            scores are indicative, not client-usable.
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
        // Inline input-domain check (GRS-0154), mirroring the backend `domain_violation` so an
        // impossible value (e.g. a negative ADV) is caught at ENTRY, not only as a score-time
        // blocker — the mock-advisor (Elena) entered −500 and it saved silently. Same copy shape.
        const raw = entry?.raw;
        let domainError: string | null = null;
        if (raw != null) {
          if (m.min_raw != null && raw < m.min_raw)
            domainError = `${m.name} can't be below ${m.min_raw} ${m.unit} (got ${raw}).`;
          else if (m.max_raw != null && raw > m.max_raw)
            domainError = `${m.name} can't be above ${m.max_raw} ${m.unit} (got ${raw}).`;
        }
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
                  min={m.min_raw ?? undefined}
                  max={m.max_raw ?? undefined}
                  aria-invalid={domainError != null}
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
                  style={{
                    ...selectStyle,
                    width: "9rem",
                    ...(domainError ? { borderColor: "var(--color-error)" } : {}),
                  }}
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
              {/* Evidence/rationale for the figure (GRS-0107) — where it came from, as-of when. */}
              {entry && entry.raw != null ? (
                <input
                  type="text"
                  disabled={readOnly}
                  value={entry.notes ?? ""}
                  placeholder="Source / as-of date (e.g. Q2 board pack, audited)"
                  onChange={(ev) =>
                    update((x) =>
                      doc.setMetric(
                        x,
                        m.key,
                        doc.metricObserved(m.key, entry.raw ?? 0, entry.confidence ?? null, ev.target.value || null),
                      ),
                    )
                  }
                  style={{ ...selectStyle, width: "100%", fontSize: "0.78rem" }}
                />
              ) : null}
              {domainError ? (
                <p role="alert" style={{ margin: 0, fontSize: "0.76rem", color: "var(--color-error)" }}>
                  {domainError}
                </p>
              ) : null}
            </div>
          </Card>
        );
      })}
    </div>
  );
}

// --- 3. Powers (Helmer) ----------------------------------------------------------------

/** One power's Benefit/Barrier rating grid (GRS-0170). An unrated side shows NO active segment —
 *  "None" is an explicit zero-power rating, never the face of an untouched control (D9). A power
 *  is only PERSISTED once both sides are rated (the contract requires the pair); a half-rating
 *  lives in local pending state with a visible hint, and clearing a side un-rates honestly
 *  (removes the entry) instead of silently writing "None". */
function PowerStrengthGrid({
  powerKey,
  powerName,
  entry,
  readOnly,
  benefitHint,
  barrierHint,
  update,
}: {
  powerKey: string;
  powerName: string;
  entry: PowerEntry | undefined;
  readOnly: boolean;
  benefitHint?: string;
  barrierHint?: string;
  update: StepProps["update"];
}) {
  const [pending, setPending] = useState<{
    benefit?: StrengthRating;
    barrier?: StrengthRating;
  }>({});
  const benefit = entry?.benefit ?? pending.benefit ?? null;
  const barrier = entry?.barrier ?? pending.barrier ?? null;

  const pick = (side: "benefit" | "barrier", v: StrengthRating | null) => {
    const nextBenefit = side === "benefit" ? v : benefit;
    const nextBarrier = side === "barrier" ? v : barrier;
    if (nextBenefit != null && nextBarrier != null) {
      // Both sides rated → persist (grades/evidence survive an in-place strength change).
      update((x) =>
        doc.setPower(
          x,
          doc.powerEntry(
            powerKey,
            nextBenefit,
            nextBarrier,
            entry?.benefit_grade ?? null,
            entry?.barrier_grade ?? null,
            entry?.benefit_evidence ?? null,
            entry?.barrier_evidence ?? null,
          ),
        ),
      );
      setPending({});
    } else {
      // A half-rating (or a cleared side): the power goes back to UNRATED in the document —
      // never a silent "None" on the side that wasn't chosen.
      if (entry) update((x) => doc.removePower(x, powerKey));
      setPending({
        benefit: nextBenefit ?? undefined,
        barrier: nextBarrier ?? undefined,
      });
    }
  };

  const half = !entry && (pending.benefit != null || pending.barrier != null);
  return (
    <>
      <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: "0.4rem 0.6rem", marginTop: "0.55rem", alignItems: "center", maxWidth: "40rem" }}>
        <span style={{ fontSize: "0.8rem" }} title={benefitHint}>Benefit</span>
        <StrengthControl
          value={benefit}
          disabled={readOnly}
          ariaLabel={`${powerName} benefit strength`}
          onChange={(v) => pick("benefit", v)}
        />
        {entry ? (
          <GradeSelect
            value={entry.benefit_grade}
            disabled={readOnly}
            onChange={(gr) =>
              update((x) =>
                doc.setPower(
                  x,
                  doc.powerEntry(powerKey, entry.benefit, entry.barrier, gr, entry.barrier_grade ?? null, entry.benefit_evidence ?? null, entry.barrier_evidence ?? null),
                ),
              )
            }
          />
        ) : (
          <span />
        )}
        <span style={{ fontSize: "0.8rem" }} title={barrierHint}>Barrier</span>
        <StrengthControl
          value={barrier}
          disabled={readOnly}
          ariaLabel={`${powerName} barrier strength`}
          onChange={(v) => pick("barrier", v)}
        />
        {entry ? (
          <GradeSelect
            value={entry.barrier_grade}
            disabled={readOnly}
            onChange={(gr) =>
              update((x) =>
                doc.setPower(
                  x,
                  doc.powerEntry(powerKey, entry.benefit, entry.barrier, entry.benefit_grade ?? null, gr, entry.benefit_evidence ?? null, entry.barrier_evidence ?? null),
                ),
              )
            }
          />
        ) : (
          <span />
        )}
      </div>
      {half ? (
        <p style={{ margin: "0.35rem 0 0", fontSize: "0.72rem", color: "var(--color-warn)" }}>
          Rate the {pending.benefit != null ? "Barrier" : "Benefit"} too — a power records only
          with both sides (the engine takes the weaker one).
        </p>
      ) : null}
    </>
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
      <div style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem", lineHeight: 1.55 }}>
        <p style={{ margin: 0 }}>
          Each of Helmer&rsquo;s seven powers carries a <strong>Benefit</strong> (the upside the leader
          enjoys) and a <strong>Barrier</strong> (why a rival can&rsquo;t copy it); the engine takes the{" "}
          <strong>weaker</strong> side — a great benefit with no barrier is just a head start. Open
          &ldquo;How to assess this power&rdquo; on any card for the Helmer framing and what evidence to
          look for, so the rating is grounded rather than guessed.
        </p>
        <p style={{ margin: "0.5rem 0 0" }}>
          Grade the evidence behind each side (this drives §7 uncertainty, not the score):{" "}
          <strong>E1</strong> client-said · <strong>E2</strong> interview · <strong>E3</strong> artifact
          you saw · <strong>E4</strong> observed yourself — weakest to strongest. Ungraded powers score
          as a labelled point, never a false-tight range.
        </p>
      </div>
      {registry.powers.map((p) => {
        const e = doc.findPower(d, p.key);
        const g = POWER_GUIDANCE[p.key];
        const setEvidence = (be: string | null, ba: string | null) => {
          if (!e) return; // rationale attaches to a recorded rating; both sides come first
          update((x) =>
            doc.setPower(
              x,
              doc.powerEntry(p.key, e.benefit, e.barrier, e.benefit_grade ?? null, e.barrier_grade ?? null, be, ba),
            ),
          );
        };
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
            <PowerStrengthGrid
              powerKey={p.key}
              powerName={p.name}
              entry={e}
              readOnly={readOnly}
              benefitHint={g?.benefitHint}
              barrierHint={g?.barrierHint}
              update={update}
            />
            {/* Optional rationale per side — records WHY. Attaches to a recorded rating. */}
            {e ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginTop: "0.5rem", maxWidth: "34rem" }}>
              <label style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
                Why this benefit?
                <input
                  type="text"
                  disabled={readOnly}
                  value={e.benefit_evidence ?? ""}
                  placeholder="evidence / rationale"
                  onChange={(ev) => setEvidence(ev.target.value || null, e.barrier_evidence ?? null)}
                  style={{ ...selectStyle, display: "block", width: "100%", marginTop: "0.2rem" }}
                />
              </label>
              <label style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
                Why this barrier?
                <input
                  type="text"
                  disabled={readOnly}
                  value={e.barrier_evidence ?? ""}
                  placeholder="evidence / rationale"
                  onChange={(ev) => setEvidence(e.benefit_evidence ?? null, ev.target.value || null)}
                  style={{ ...selectStyle, display: "block", width: "100%", marginTop: "0.2rem" }}
                />
              </label>
            </div>
            ) : null}
            {g ? (
              <div style={{ marginTop: "0.5rem" }}>
                <button type="button" className={smallBtn} style={smallBtnStyle} onClick={() => setOpenExample(showExample ? null : p.key)}>
                  {showExample ? "Hide guidance" : "How to assess this power"}
                </button>
                {showExample ? (
                  <div className="callout callout-info" style={{ marginTop: "0.5rem", fontSize: "0.8rem", lineHeight: 1.5, display: "grid", gap: "0.5rem" }}>
                    <div>
                      <strong style={{ color: "var(--color-accent)" }}>Benefit</strong> — {g.benefitHint}
                    </div>
                    <div>
                      <strong style={{ color: "var(--color-accent)" }}>Barrier</strong> — {g.barrierHint}{" "}
                      The engine takes the <strong>weaker</strong> of the two.
                    </div>
                    <div>
                      <strong>How to assess</strong> — {g.assessment}
                    </div>
                    <div style={{ color: "var(--color-ink-soft)", fontStyle: "italic" }}>
                      Example — {g.example}
                    </div>
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
  // Collapse each module so the 51-subcomponent page is navigable, not one endless scroll (GRS-0160).
  // Modules that are already fully rated start collapsed; the rest open. Controlled by state so a
  // manual toggle is never overridden on the next render.
  const isRated = (key: string) => doc.findSub(d, key)?.level != null;
  const [collapsed, setCollapsed] = useState<Set<string>>(
    () =>
      new Set(
        registry.modules
          .filter((m) => m.subcomponents.length > 0 && m.subcomponents.every((s) => isRated(s.key)))
          .map((m) => m.key),
      ),
  );
  const toggle = (key: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "1rem", flexWrap: "wrap" }}>
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem", margin: 0, maxWidth: "46rem" }}>
          Work each of the {registry.modules.length} modules, front end to liquidity. A ★ marks a critical
          subcomponent — it gates the module rating (a module can&rsquo;t outrun its critical bottleneck).
          Each row&rsquo;s Guidance opens the §4 rubric anchor inline. Click a module to collapse it.
        </p>
        <button
          type="button"
          className={smallBtn}
          style={smallBtnStyle}
          onClick={() =>
            setCollapsed((prev) =>
              prev.size === registry.modules.length ? new Set() : new Set(registry.modules.map((m) => m.key)),
            )
          }
        >
          {collapsed.size === registry.modules.length ? "Expand all" : "Collapse all"}
        </button>
      </div>
      {registry.modules.map((m) => {
        const rated = m.subcomponents.filter((s) => doc.findSub(d, s.key)?.level != null).length;
        const isOpen = !collapsed.has(m.key);
        return (
        <div key={m.key} className="card" style={{ padding: "0.5rem 0.85rem" }}>
          <SectionHeader
            title={m.name}
            rated={rated}
            total={m.subcomponents.length}
            noun="rated"
            isOpen={isOpen}
            onToggle={() => toggle(m.key)}
          />
          {isOpen ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", marginTop: "0.4rem" }}>
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
                      {/* One-click segmented rating (GRS-0165) — same transitions the old select made. */}
                      <RatingControl
                        choice={choice}
                        disabled={readOnly}
                        ariaLabel={s.name}
                        onChange={(v) =>
                          update((x) => {
                            if (v === "") return doc.setSub(x, s.key, null);
                            if (v === "Not Applicable" || v === "Not Assessed")
                              return doc.setSub(x, s.key, doc.subState(m.key, s.key, v));
                            return doc.setSub(x, s.key, doc.subAssessed(m.key, s.key, v, r?.evidence_grade ?? "E2"));
                          })
                        }
                      />
                      {r?.level != null ? (
                        <GradeSelect
                          value={r.evidence_grade}
                          disabled={readOnly}
                          onChange={(g) => update((x) => doc.setSub(x, s.key, doc.subAssessed(m.key, s.key, r.level as MaturityLevel, g ?? "E1", r.notes ?? null)))}
                        />
                      ) : null}
                      <button type="button" className={smallBtn} style={smallBtnStyle} onClick={() => setOpenGuidance(openGuidance === s.key ? null : s.key)}>
                        {openGuidance === s.key ? "Hide guidance" : "Guidance"}
                      </button>
                    </div>
                  </div>
                  {/* Evidence/rationale for the rating (GRS-0107) — what you saw that supports it. */}
                  {r?.level != null ? (
                    <input
                      type="text"
                      disabled={readOnly}
                      value={r.notes ?? ""}
                      placeholder="What evidence supports this rating? (e.g. saw the failover runbook + incident log)"
                      onChange={(ev) => update((x) => doc.setSub(x, s.key, doc.subAssessed(m.key, s.key, r.level as MaturityLevel, r.evidence_grade ?? "E1", ev.target.value || null)))}
                      style={{ ...selectStyle, width: "100%", fontSize: "0.78rem", marginTop: "0.5rem" }}
                    />
                  ) : null}
                  {openGuidance === s.key ? (
                    <div style={{ marginTop: "0.6rem" }}>
                      <GuidancePanel subcomponentKey={s.key} />
                    </div>
                  ) : null}
                </Card>
              );
            })}
          </div>
          ) : null}
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

/** The shared collapsible section header (GRS-0165): title + "n/m" progress + disclosure caret.
 *  The whole header is the toggle, mirroring the Infrastructure treatment (GRS-0160). */
function SectionHeader({
  title,
  rated,
  total,
  noun,
  isOpen,
  onToggle,
}: {
  title: string;
  rated: number;
  total: number;
  noun: string;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const complete = total > 0 && rated === total;
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={isOpen}
      style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.75rem", width: "100%", background: "none", border: "none", cursor: "pointer", padding: "0.3rem 0", textAlign: "left" }}
    >
      <h3 style={{ fontSize: "1rem", margin: 0, display: "flex", alignItems: "baseline", gap: "0.5rem" }}>
        <span aria-hidden="true" style={{ display: "inline-block", width: "0.75rem", color: "var(--color-ink-muted)", fontSize: "0.7rem" }}>
          {isOpen ? "▾" : "▸"}
        </span>
        {title}
      </h3>
      <span className="mono" style={{ fontSize: "0.75rem", color: complete ? "var(--color-accent)" : "var(--color-ink-muted)" }}>
        {rated}/{total} {noun}{complete ? " ✓" : ""}
      </span>
    </button>
  );
}

export function CustomerPropositionStep({ registry, document: d, update, readOnly }: StepProps) {
  const [openGuidance, setOpenGuidance] = useState<string | null>(null);
  const profileKey = d.profile?.operating_model ?? "retail";
  const showGrid = registry.c_widgets.length > 0 && profileKey === registry.c_widget_profile;
  const categories = Array.from(new Set(registry.c_widgets.map((w) => w.category)));
  // Collapse the C modules and widget categories the same way Infrastructure collapses (GRS-0165):
  // fully-complete sections start collapsed; a manual toggle is never overridden on re-render.
  const isCRated = (key: string) => doc.findCSub(d, key)?.level != null;
  const catWidgets = (category: string) => registry.c_widgets.filter((w) => w.category === category);
  const recordedIn = (category: string) =>
    catWidgets(category).filter((w) => widgetChoiceOf(doc.findWidget(d, w.key)) !== "").length;
  const [collapsed, setCollapsed] = useState<Set<string>>(() => {
    const done = registry.c_modules
      .filter((m) => m.subcomponents.length > 0 && m.subcomponents.every((s) => isCRated(s.key)))
      .map((m) => m.key);
    const doneCats = categories
      .filter((c) => catWidgets(c).length > 0 && recordedIn(c) === catWidgets(c).length)
      .map((c) => `cat:${c}`);
    return new Set([...done, ...doneCats]);
  });
  const allSectionKeys = [...registry.c_modules.map((m) => m.key), ...categories.map((c) => `cat:${c}`)];
  const toggle = (key: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  // The Customer-Proposition taxonomy is a retail-brokerage customer-experience model (GRS-0152).
  // A non-retail profile carries no C modules (profiles.yaml → c_modules: []), so instead of asking
  // a wealth/exchange firm retail neobroker questions, degrade honestly: this dimension is not yet
  // modelled for the segment. A per-segment C taxonomy is a founder-scoped content build.
  const cModelled = registry.c_modules.length > 0;

  if (!cModelled) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div className="card" style={{ padding: "1rem 1.15rem", borderLeft: "3px solid var(--color-ink-faint)" }}>
          <h3 style={{ fontSize: "1rem", margin: "0 0 0.4rem" }}>
            Customer Proposition — not yet modelled for the {profileKey} operating model
          </h3>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--color-ink-muted)", lineHeight: 1.55 }}>
            The Customer-Proposition Index (C) is a <strong>retail-brokerage</strong> customer-experience
            model — onboarding and time-to-first-trade, trading experience, product range. This{" "}
            <strong>{profileKey}</strong> operating model&rsquo;s client proposition is a different
            construct (advice relationship, planning and reporting for wealth; member/participant
            experience for an exchange), and its taxonomy has not been authored yet. Rather than score you
            on questions that don&rsquo;t fit, this step is <strong>skipped for this segment</strong> — it
            does not affect your V. B, P and L (and the infrastructure deep dive) are fully segment-native.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      <p style={{ color: "var(--color-ink-muted)", fontSize: "0.9rem", margin: 0, lineHeight: 1.55 }}>
        <strong style={{ color: "var(--color-ink)" }}>This is where you judge how good the platform
        actually is for a customer.</strong> The Customer Proposition Index (C) reads the{" "}
        {registry.c_modules.length} Phase-E modules and the <strong>Level-1 widget checklist</strong> —
        is each feature present, and how good is it on <strong>Ease · Usability · Depth</strong>? A rare
        feature done well is a differentiator; a common one missing is a gap. C is scored live (see the
        rail) and reported alongside V (ADR-0023); it does not change V yet.
      </p>

      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button
          type="button"
          className={smallBtn}
          style={smallBtnStyle}
          onClick={() =>
            setCollapsed((prev) =>
              prev.size === allSectionKeys.length ? new Set() : new Set(allSectionKeys),
            )
          }
        >
          {collapsed.size === allSectionKeys.length ? "Expand all" : "Collapse all"}
        </button>
      </div>

      {registry.c_modules.map((m) => {
        const rated = m.subcomponents.filter((s) => isCRated(s.key)).length;
        const isOpen = !collapsed.has(m.key);
        return (
        <div key={m.key} className="card" style={{ padding: "0.5rem 0.85rem" }}>
          <SectionHeader
            title={m.name}
            rated={rated}
            total={m.subcomponents.length}
            noun="rated"
            isOpen={isOpen}
            onToggle={() => toggle(m.key)}
          />
          {isOpen ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", marginTop: "0.4rem" }}>
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
                      {/* One-click segmented rating (GRS-0165) — same transitions the old select made. */}
                      <RatingControl
                        choice={choice}
                        disabled={readOnly}
                        ariaLabel={s.name}
                        onChange={(v) =>
                          update((x) => {
                            if (v === "") return doc.setCSub(x, s.key, null);
                            if (v === "Not Applicable" || v === "Not Assessed")
                              return doc.setCSub(x, s.key, doc.subState(m.key, s.key, v));
                            return doc.setCSub(x, s.key, doc.subAssessed(m.key, s.key, v, r?.evidence_grade ?? "E2"));
                          })
                        }
                      />
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
          ) : null}
        </div>
        );
      })}

      <div>
        <h3 style={{ fontSize: "1rem", margin: "0 0 0.4rem" }}>Level-1 widget checklist</h3>
        {!showGrid ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.82rem", margin: 0 }}>
            The widget checklist is scoped to the <strong>{registry.c_widget_profile}</strong>{" "}
            operating model; it is not shown for the <strong>{profileKey}</strong> profile.
          </p>
        ) : (
          categories.map((category) => {
            const catKey = `cat:${category}`;
            const isOpen = !collapsed.has(catKey);
            return (
            <div key={category} className="card" style={{ padding: "0.4rem 0.85rem", marginBottom: "0.5rem" }}>
              <SectionHeader
                title={category}
                rated={recordedIn(category)}
                total={catWidgets(category).length}
                noun="recorded"
                isOpen={isOpen}
                onToggle={() => toggle(catKey)}
              />
              {isOpen ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem", marginTop: "0.35rem" }}>
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
              ) : null}
            </div>
            );
          })
        )}
      </div>
    </div>
  );
}

// --- 6. Summary & Interpretation --------------------------------------------------------

/** The interpretation (GRS-0110): read the RANGE not the point, name the bottleneck, remind that
 *  words rate / numbers rank, and point at the value bridge — computed from the live diagnostics the
 *  engine already produces, never recomputed. */
function Interpretation({
  live,
  moduleLabels,
  final,
}: {
  live: LiveScore;
  moduleLabels: Record<string, string>;
  final?: BrokeragePortfolioEntry | null;
}) {
  if (!live.scoreable || !live.v) return null;
  const pct = (x: number) => Math.round(x * 100);
  // The one-number rule (ADR-0040): quote the deterministic point (locked value when finalised,
  // live v_point otherwise) — the prose must agree with the headline right above it.
  const vPoint = final?.v_index ?? live.v_point ?? live.v.p50;
  const vLow = final?.v_index != null && final.v_p10 != null ? Math.min(final.v_p10, final.v_index) : live.v.p10;
  const vHigh = final?.v_index != null && final.v_p90 != null ? Math.max(final.v_p90, final.v_index) : live.v.p90;
  const modules = Object.entries(live.module_qm);
  const bottleneck = modules.length
    ? modules.reduce((min, cur) => (cur[1].p50 < min[1].p50 ? cur : min))
    : null;
  // At low coverage the "weakest module" is unreliable: an unassessed module carries a modelled
  // ~neutral band and can rank weakest simply because it hasn't been looked at (GRS-0145). Below half
  // coverage we caveat the bottleneck rather than issue a confident "go fix this" that could point at
  // the one module nobody assessed.
  const lowCoverage = live.coverage != null && live.coverage < 0.5;
  return (
    <Card>
      <h3 style={{ margin: "0 0 0.6rem", fontSize: "1rem" }}>What this means</h3>
      <ul style={{ margin: 0, paddingLeft: "1.15rem", fontSize: "0.86rem", lineHeight: 1.6, color: "var(--color-ink-muted)" }}>
        <li>
          <strong>Read the range, not the point.</strong> Platform Value sits at{" "}
          <strong style={{ color: "var(--color-ink)" }}>{pct(vPoint)}</strong>, but the honest
          answer is the <strong style={{ color: "var(--color-ink)" }}>{pct(vLow)}–{pct(vHigh)}</strong>{" "}
          range (overall uncertainty {live.overall_uncertainty}). Quote the range; the point alone loses a technical audience.
        </li>
        {bottleneck ? (
          <li>
            <strong>The bottleneck.</strong>{" "}
            <strong style={{ color: "var(--color-ink)" }}>{moduleLabels[bottleneck[0]] ?? bottleneck[0]}</strong>{" "}
            is the current weakest link at <strong style={{ color: "var(--color-ink)" }}>{pct(bottleneck[1].p50)}</strong>
            {lowCoverage ? (
              <>
                {" "}— but at only{" "}
                <strong style={{ color: "var(--color-ink)" }}>{pct(live.coverage as number)}%</strong> coverage this is
                provisional: a module can rank weakest simply because it hasn&rsquo;t been assessed yet. Assess more before
                acting on it.
              </>
            ) : (
              <>
                {" "}— it caps the whole. The fastest lift comes from fixing the weakest critical part, not the
                already-strong ones.
              </>
            )}
          </li>
        ) : null}
        <li>
          <strong>Words rate; numbers rank.</strong> The module bands (Basic → Frontier) are what you
          defend in the boardroom; the continuous scores decide <em>what to fix first</em>. Use the word to communicate, the number to prioritise.
        </li>
        <li>
          <strong>The value bridge.</strong> The finalised deliverable prices the gaps in three layers
          kept apart — cost (£) to upgrade, the cash-flow levers it moves (NPV), and strategic value (words). It never divides a score gap into pounds.
        </li>
      </ul>
    </Card>
  );
}

/** Preview the finalised assessment's deliverable as a watermarked .docx without an engagement
 *  (GRS-0154) — the solo/sandbox "see the real deliverable" path. Internal-only, so it works for a
 *  draft wealth/exchange profile too. A 409 (committee gate) surfaces the backend's plain message. */
function DeliverablePreviewButton({ assessmentId }: { assessmentId: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function download() {
    setBusy(true);
    setError(null);
    try {
      const { blob, filename } = await api.previewAssessmentDeliverable(assessmentId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Couldn't generate the preview.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
        <div>
          <strong style={{ fontSize: "0.9rem" }}>Deliverable preview</strong>
          <p style={{ margin: "0.2rem 0 0", fontSize: "0.76rem", color: "var(--color-ink-muted)", lineHeight: 1.45 }}>
            The real Platform Power Report for this finalised assessment, watermarked and internal-only
            (never client-facing). Download the .docx.
          </p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={download} disabled={busy}>
          {busy ? "Generating…" : "Download preview (.docx)"}
        </button>
      </div>
      {error ? (
        <p role="alert" style={{ margin: "0.5rem 0 0", fontSize: "0.78rem", color: "var(--color-error)" }}>
          {error}
        </p>
      ) : null}
    </Card>
  );
}

export function SummaryStep(props: StepProps) {
  const { live, readOnly, onFinalise, finalising } = props;
  // Two-step finalise (GRS-0171): the irreversible lock needs an explicit confirm that names the
  // consequences and the sandbox-vs-production difference.
  const [confirmingFinalise, setConfirmingFinalise] = useState(false);
  const moduleLabels = Object.fromEntries(props.registry.modules.map((m) => [m.key, m.name]));
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem", maxWidth: "42rem" }}>
      <LiveScorePanel
        score={live}
        loading={props.liveLoading}
        error={props.liveError}
        onRefresh={props.refreshLive}
        moduleLabels={moduleLabels}
        profileKey={props.document?.profile?.operating_model ?? "retail"}
        clientUsable={props.clientUsable}
        final={props.finalEntry}
      />
      {/* A finalised assessment can preview its real deliverable here — no engagement needed
          (GRS-0154), so the solo/sandbox "see the real deliverable" promise actually pays off. */}
      {readOnly ? <DeliverablePreviewButton assessmentId={props.assessmentId} /> : null}
      {live ? <Interpretation live={live} moduleLabels={moduleLabels} final={props.finalEntry} /> : null}
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
          {/* Finalisation is irreversible — a one-click lock alarmed every persona (GRS-0171).
              The confirm states the consequences AND what the current path does/doesn't include,
              so a solo advisor knows exactly what a sandbox lock is. */}
          {!confirmingFinalise ? (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setConfirmingFinalise(true)}
              disabled={finalising || !live?.scoreable}
            >
              Finalise & lock inputs
            </button>
          ) : (
            <div
              className="callout callout-warn"
              role="alertdialog"
              aria-label="Confirm finalisation"
              style={{ fontSize: "0.85rem", lineHeight: 1.55, display: "grid", gap: "0.6rem", maxWidth: "36rem" }}
            >
              <p style={{ margin: 0 }}>
                <strong>Finalise and lock?</strong> This creates the immutable, versioned scoring
                run and locks every input — the assessment cannot be edited afterwards
                {live?.v_point != null ? (
                  <>
                    {" "}(the locked score will be{" "}
                    <strong className="mono">{(live.v_point * 100).toFixed(1)}</strong> — the same
                    number showing above).
                  </>
                ) : (
                  "."
                )}
              </p>
              <p style={{ margin: 0, color: "var(--color-ink-muted)" }}>
                {props.provenance === "production"
                  ? "Production path: this score carries dual-rating consensus and committee sign-off, and can feed client-facing work (subject to the client-usability gates)."
                  : "Sandbox/demo path: self-approved with NO second rater or committee — permanently watermarked, never client-facing. The production path adds dual rating and committee sign-off."}
              </p>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={onFinalise}
                  disabled={finalising}
                >
                  {finalising ? "Finalising…" : "Yes — finalise & lock"}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setConfirmingFinalise(false)}
                  disabled={finalising}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
          {!live?.scoreable ? (
            <p style={{ margin: "0.4rem 0 0", fontSize: "0.8rem", color: "var(--color-warn)" }}>
              Complete the blocking items above before finalising.
            </p>
          ) : null}

          {/* Solo-path escape hatch (GRS-0148): production finalise needs a second rater + committee.
              A working-solo advisor can clone this to a self-approvable sandbox and see the real,
              watermarked deliverable now — the capability existed but testers never found it. */}
          {props.provenance === "production" ? (
            <div
              style={{
                marginTop: "0.9rem",
                padding: "0.75rem 0.85rem",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius)",
                background: "var(--color-paper-raised)",
              }}
            >
              <p style={{ margin: "0 0 0.5rem", fontSize: "0.82rem", color: "var(--color-ink-muted)" }}>
                <strong style={{ color: "var(--color-ink)" }}>Working solo?</strong> A production score
                finalises with a second independent rater and committee sign-off. To see a finished,
                watermarked deliverable draft <em>now</em>, create a Sandbox preview of this assessment —
                self-approved, and never client-facing.
              </p>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={props.onPreviewInSandbox}
                disabled={props.previewingSandbox}
              >
                {props.previewingSandbox ? "Creating preview…" : "Preview in sandbox"}
              </button>
            </div>
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
          {result.baseline_v != null && result.priority_index.length > 0 ? (
            <p style={{ margin: "0 0 0.7rem", fontSize: "0.82rem" }}>
              Baseline V <strong className="mono">{(result.baseline_v * 100).toFixed(1)}</strong> → the
              top upgrade ({result.priority_index[0]!.name}) lifts it to{" "}
              <strong className="mono">
                {((result.baseline_v + result.priority_index[0]!.delta_v) * 100).toFixed(1)}
              </strong>
              . ΔV is score-domain only — it says <em>what to fix first</em>, not what it&rsquo;s worth
              (the deliverable&rsquo;s value bridge prices that).
            </p>
          ) : null}
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
