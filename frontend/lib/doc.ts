/**
 * Immutable helpers for editing an `AssessmentDocument`. Not Assessed / Not Applicable are
 * first-class: leaving a subcomponent unrated (absent) is different from Not Assessed, which is
 * different from a level. Unrated ≠ zero — the engine treats an absent subcomponent as Not Assessed.
 */

import type {
  AssessmentDocument,
  BusinessProfile,
  EvidenceGrade,
  MaturityLevel,
  MetricConfidence,
  MetricEntry,
  NonScoreState,
  PowerEntry,
  StrengthRating,
  SubcomponentRating,
  WidgetObservation,
} from "@/lib/types";

const EMPTY_PROFILE: BusinessProfile = {
  country: null,
  segment: null,
  asset_classes: [],
  regions: [],
  licensing: null,
};

/** Merge a partial business-profile update into the document (GRS-0068), creating it if absent. */
export function setProfile(
  doc: AssessmentDocument,
  patch: Partial<BusinessProfile>,
): AssessmentDocument {
  return { ...doc, profile: { ...EMPTY_PROFILE, ...doc.profile, ...patch } };
}

/** Parse a comma-separated field into a trimmed, non-empty list (for asset classes / regions). */
export function parseList(raw: string): string[] {
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export function emptyDoc(subject = ""): AssessmentDocument {
  return {
    subject,
    subcomponents: [],
    metrics: [],
    powers: [],
    c_subcomponents: [],
    widgets: [],
    notes: null,
  };
}

export function findSub(doc: AssessmentDocument, key: string): SubcomponentRating | undefined {
  return doc.subcomponents.find((s) => s.subcomponent_key === key);
}

/** Replace (or remove, when `rating` is null) a subcomponent rating by key. */
export function setSub(
  doc: AssessmentDocument,
  key: string,
  rating: SubcomponentRating | null,
): AssessmentDocument {
  const rest = doc.subcomponents.filter((s) => s.subcomponent_key !== key);
  return { ...doc, subcomponents: rating ? [...rest, rating] : rest };
}

export function subAssessed(
  moduleKey: string,
  key: string,
  level: MaturityLevel,
  evidence: EvidenceGrade,
  notes?: string | null,
): SubcomponentRating {
  return {
    module_key: moduleKey,
    subcomponent_key: key,
    level,
    state: null,
    evidence_grade: evidence,
    notes: notes ?? null,
  };
}

export function subState(
  moduleKey: string,
  key: string,
  state: NonScoreState,
): SubcomponentRating {
  return { module_key: moduleKey, subcomponent_key: key, level: null, state, evidence_grade: null };
}

export function findMetric(doc: AssessmentDocument, key: string): MetricEntry | undefined {
  return doc.metrics.find((m) => m.metric_key === key);
}

export function setMetric(
  doc: AssessmentDocument,
  key: string,
  entry: MetricEntry | null,
): AssessmentDocument {
  const rest = doc.metrics.filter((m) => m.metric_key !== key);
  return { ...doc, metrics: entry ? [...rest, entry] : rest };
}

export function metricObserved(
  key: string,
  raw: number,
  confidence: MetricConfidence | null,
  notes: string | null = null,
): MetricEntry {
  return { metric_key: key, raw, state: null, confidence, notes };
}

export function metricState(key: string, state: NonScoreState): MetricEntry {
  return { metric_key: key, raw: null, state, confidence: null };
}

export function findPower(doc: AssessmentDocument, key: string): PowerEntry | undefined {
  return doc.powers.find((p) => p.power_key === key);
}

export function setPower(doc: AssessmentDocument, entry: PowerEntry): AssessmentDocument {
  const rest = doc.powers.filter((p) => p.power_key !== entry.power_key);
  return { ...doc, powers: [...rest, entry] };
}

/** Un-rate a power (GRS-0170): back to first-class UNRATED (the entry is removed), which the
 *  engine treats as "not assessed" — never coerced into the StrengthRating "None" moat floor. */
export function removePower(doc: AssessmentDocument, key: string): AssessmentDocument {
  return { ...doc, powers: doc.powers.filter((p) => p.power_key !== key) };
}

export function powerEntry(
  key: string,
  benefit: StrengthRating,
  barrier: StrengthRating,
  benefitGrade: EvidenceGrade | null,
  barrierGrade: EvidenceGrade | null,
  benefitEvidence?: string | null,
  barrierEvidence?: string | null,
): PowerEntry {
  return {
    power_key: key,
    benefit,
    barrier,
    benefit_grade: benefitGrade,
    barrier_grade: barrierGrade,
    // Only carry evidence keys when present, so existing callers serialise identically (an empty
    // string collapses to null — the engine treats absent and blank evidence the same).
    benefit_evidence: benefitEvidence ? benefitEvidence : null,
    barrier_evidence: barrierEvidence ? barrierEvidence : null,
  };
}

// --- C-index capture (ADR-0023 / GRS-0083) ---------------------------------------------
// C subcomponent ratings reuse the SubcomponentRating shape and the subAssessed/subState builders
// above — only the collection differs (c_subcomponents, not subcomponents).

export function findCSub(doc: AssessmentDocument, key: string): SubcomponentRating | undefined {
  return doc.c_subcomponents.find((s) => s.subcomponent_key === key);
}

/** Replace (or remove, when `rating` is null) a C subcomponent rating by key. */
export function setCSub(
  doc: AssessmentDocument,
  key: string,
  rating: SubcomponentRating | null,
): AssessmentDocument {
  const rest = doc.c_subcomponents.filter((s) => s.subcomponent_key !== key);
  return { ...doc, c_subcomponents: rating ? [...rest, rating] : rest };
}

export function findWidget(doc: AssessmentDocument, key: string): WidgetObservation | undefined {
  return doc.widgets.find((w) => w.widget_key === key);
}

/** Upsert (or remove, when `obs` is null) one widget observation by key. */
export function setWidget(
  doc: AssessmentDocument,
  key: string,
  obs: WidgetObservation | null,
): AssessmentDocument {
  const rest = doc.widgets.filter((w) => w.widget_key !== key);
  return { ...doc, widgets: obs ? [...rest, obs] : rest };
}

/** A present widget with optional 1–5 ease/usability/depth scores. */
export function widgetPresent(
  key: string,
  scores?: { ease?: number | null; usability?: number | null; depth?: number | null },
): WidgetObservation {
  return {
    widget_key: key,
    present: true,
    state: null,
    ease: scores?.ease ?? null,
    usability: scores?.usability ?? null,
    depth: scores?.depth ?? null,
  };
}

/** A non-present widget, optionally flagged Present (Paywalled) / Present (Defective). */
export function widgetAbsent(key: string, state: NonScoreState | null = null): WidgetObservation {
  return { widget_key: key, present: false, state, ease: null, usability: null, depth: null };
}
