/**
 * Immutable helpers for editing an `AssessmentDocument`. Not Assessed / Not Applicable are
 * first-class: leaving a subcomponent unrated (absent) is different from Not Assessed, which is
 * different from a level. Unrated ≠ zero — the engine treats an absent subcomponent as Not Assessed.
 */

import type {
  AssessmentDocument,
  EvidenceGrade,
  MaturityLevel,
  MetricConfidence,
  MetricEntry,
  NonScoreState,
  PowerEntry,
  StrengthRating,
  SubcomponentRating,
} from "@/lib/types";

export function emptyDoc(subject = ""): AssessmentDocument {
  return { subject, subcomponents: [], metrics: [], powers: [], notes: null };
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
): MetricEntry {
  return { metric_key: key, raw, state: null, confidence };
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
