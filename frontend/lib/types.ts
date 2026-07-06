/**
 * TypeScript mirrors of the `bcap_contracts` API resources the wizard uses (GRS-0009/0010).
 * These follow the Pydantic contracts field-for-field; the backend JSON Schemas are the source of
 * truth (schema-parity CI). Kept hand-written and minimal — only what Path A needs.
 */

export type MaturityLevel = "Basic" | "Developing" | "Advanced" | "Frontier";
export type NonScoreState = "Not Applicable" | "Not Assessed";
export type EvidenceGrade = "E1" | "E2" | "E3" | "E4";
export type StrengthRating = "None" | "Emerging" | "Established" | "Wide";
export type MetricConfidence =
  | "audited"
  | "management_reported"
  | "self_reported"
  | "estimated";
export type TrendDirection = "improving" | "stable" | "eroding";
export type AssessmentState = "draft" | "in_progress" | "finalised";
export type UncertaintyRating = "Low" | "Medium" | "High" | "Very High";

export const MATURITY_LEVELS: MaturityLevel[] = [
  "Basic",
  "Developing",
  "Advanced",
  "Frontier",
];
export const EVIDENCE_GRADES: EvidenceGrade[] = ["E1", "E2", "E3", "E4"];
export const STRENGTHS: StrengthRating[] = ["None", "Emerging", "Established", "Wide"];
export const METRIC_CONFIDENCES: MetricConfidence[] = [
  "audited",
  "management_reported",
  "self_reported",
  "estimated",
];

/** Exactly one of `level` (assessed) or `state` (Not Applicable / Not Assessed). */
export interface SubcomponentRating {
  module_key: string;
  subcomponent_key: string;
  level?: MaturityLevel | null;
  state?: NonScoreState | null;
  evidence_grade?: EvidenceGrade | null;
  evidence_refs?: string[];
  notes?: string | null;
}

export interface MetricEntry {
  metric_key: string;
  raw?: number | null;
  state?: NonScoreState | null;
  confidence?: MetricConfidence | null;
}

export interface PowerEntry {
  power_key: string;
  benefit: StrengthRating;
  barrier: StrengthRating;
  benefit_grade?: EvidenceGrade | null;
  barrier_grade?: EvidenceGrade | null;
  benefit_evidence?: string | null;
  barrier_evidence?: string | null;
  trend?: TrendDirection | null;
}

export interface AssessmentDocument {
  subject: string;
  subcomponents: SubcomponentRating[];
  metrics: MetricEntry[];
  powers: PowerEntry[];
  notes?: string | null;
}

export interface Assessment {
  id: string;
  owner_consultant_id: string;
  subject: string;
  state: AssessmentState;
  document: AssessmentDocument;
  finalised_at?: string | null;
  scoring_run_id?: string | null;
  engine_version?: string | null;
  methodology_version?: string | null;
  coefficient_version?: string | null;
  uncertainty_version?: string | null;
  created_at: string;
  updated_at: string;
}

/** P10/P50/P90 band + the ADR-0008 honesty flag. modelled=false ⟹ a point estimate. */
export interface IndexBand {
  p10: number;
  p50: number;
  p90: number;
  modelled: boolean;
}

export interface LiveScore {
  scoreable: boolean;
  blocking: string[];
  v?: IndexBand | null;
  b?: IndexBand | null;
  p?: IndexBand | null;
  l_index?: IndexBand | null;
  module_qm: Record<string, IndexBand>;
  triad_economic?: StrengthRating | null;
  triad_perceived?: StrengthRating | null;
  triad_defence?: StrengthRating | null;
  overall_uncertainty?: UncertaintyRating | null;
  subcomponents_assessed: number;
  subcomponents_total: number;
  coverage?: number | null;
  engine_version: string;
  methodology_version: string;
  coefficient_version: string;
  uncertainty_version: string;
}

export type AnchorStatus = "authored" | "draft" | "todo";

export interface RubricAnchor {
  subcomponent_key: string;
  level: MaturityLevel;
  status: AnchorStatus;
  statement: string;
  required_evidence: string[];
  differentiator_questions: string[];
  misgrading_notes?: string | null;
}

export interface RegistrySubcomponent {
  key: string;
  name: string;
  module_key: string;
  description?: string | null;
  critical: boolean;
}

export interface RegistryModule {
  key: string;
  name: string;
  description: string;
  subcomponents: RegistrySubcomponent[];
}

export interface RegistryMetric {
  key: string;
  name: string;
  unit: string;
  direction: string;
  group?: string | null;
}

export interface RegistryPower {
  key: string;
  name: string;
  lifecycle_stage: string;
  description: string;
}

export interface Registry {
  powers: RegistryPower[];
  modules: RegistryModule[];
  metrics: RegistryMetric[];
  subcomponent_status: string;
  metric_status: string;
}

export interface ScenarioResult {
  name: string;
  baseline_v: number;
  scenario_v: number;
  delta_v: number;
  delta_l: number;
  delta_b: number;
  delta_p: number;
}

export interface UpgradePriority {
  name: string;
  delta_v: number;
  rank: number;
}

export interface ScenarioComparison {
  scoreable: boolean;
  blocking: string[];
  baseline_v?: number | null;
  results: ScenarioResult[];
  priority_index: UpgradePriority[];
}
