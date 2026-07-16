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
  // Dual-rating governance (§9), set by consensus resolution (read-only on the client).
  rater_ids?: string[];
  consensus?: boolean;
  dissent_note?: string | null;
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

/** Descriptive context for the business (GRS-0068). Never a scoring input — frames the assessment. */
export interface BusinessProfile {
  country?: string | null;
  segment?: string | null;
  asset_classes: string[];
  regions: string[];
  licensing?: string | null;
}

export interface AssessmentDocument {
  subject: string;
  profile?: BusinessProfile | null;
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

/** One row of the "Your Brokerages" portfolio (GRS-0071). v_index is the last finalised V (P50). */
export interface BrokeragePortfolioEntry {
  assessment_id: string;
  subject: string;
  segment?: string | null;
  state: AssessmentState;
  v_index?: number | null;
  uncertainty_rating?: UncertaintyRating | null;
  finalised_at?: string | null;
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
  // Weights the score was built from (GRS-0070 diagnostics); present only when scoreable.
  theta_b?: number | null;
  theta_p?: number | null;
  theta_l?: number | null;
  module_weights: Record<string, number>;
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

// --- Pipeline / CRM (GRS-0011..0014) ----------------------------------------------------

export type PipelineStage =
  | "prospect"
  | "workshop_scheduled"
  | "workshop_delivered"
  | "qualified"
  | "scoped"
  | "contracted"
  | "active"
  | "delivered"
  | "closed"
  | "nurture";

/** The ten stages in canonical order, with display labels — the kanban columns. */
export const PIPELINE_STAGES: { stage: PipelineStage; label: string }[] = [
  { stage: "prospect", label: "Prospect" },
  { stage: "workshop_scheduled", label: "Workshop Scheduled" },
  { stage: "workshop_delivered", label: "Workshop Delivered" },
  { stage: "qualified", label: "Qualified" },
  { stage: "scoped", label: "Scoped" },
  { stage: "contracted", label: "Contracted" },
  { stage: "active", label: "Active" },
  { stage: "delivered", label: "Delivered" },
  { stage: "closed", label: "Closed" },
  { stage: "nurture", label: "Nurture" },
];

export const STAGE_LABEL: Record<PipelineStage, string> = Object.fromEntries(
  PIPELINE_STAGES.map((s) => [s.stage, s.label]),
) as Record<PipelineStage, string>;

export interface Prospect {
  id: string;
  owner_consultant_id: string;
  company_name: string;
  stage: PipelineStage;
  stage_entered_at: string;
  sector?: string | null;
  primary_contact_name?: string | null;
  primary_contact_email?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PipelineBoardEntry {
  prospect: Prospect;
  days_in_stage: number;
  stale_after_days: number;
  stale: boolean;
}

export interface PipelineBoard {
  generated_at: string;
  entries: PipelineBoardEntry[];
}

export interface StageForecast {
  stage: PipelineStage;
  count: number;
  close_probability: number;
  weighted_deals: number;
}

export interface PipelineForecast {
  generated_at: string;
  total_prospects: number;
  open_prospects: number;
  stages: StageForecast[];
  weighted_expected_deals: number;
}

/** Currency amount straight from the API. `amount_minor` is integer minor units (never a float);
 * the UI FORMATS it for display but never does arithmetic on it (ADR-0002 at the view layer). */
export type Currency = "GBP" | "USD" | "EUR";
export interface Money {
  amount_minor: number;
  currency: Currency;
  assumption_register_ref: string;
}

export type WorkshopState = "scheduled" | "delivered";

export interface Workshop {
  id: string;
  owner_consultant_id: string;
  prospect_id: string;
  state: WorkshopState;
  scheduled_for?: string | null;
  delivered_on?: string | null;
  pre_workshop_brief?: string | null;
  workshop_output?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RecoveryFeeAttribution {
  id: string;
  owner_consultant_id: string;
  workshop_id: string;
  prospect_id: string;
  delivered_on: string;
  contracted_on: string;
  window_days: number;
  rate_ref: string;
  fee: Money;
  content_hash: string;
  created_at: string;
  updated_at: string;
}

// --- Earnings / commissions (Commission Schedule v7, ADR-0026; `CommissionLine` contract) ---
export type CommissionKind = "engagement" | "workshop_recovery_fee" | "retainer";
// v7 axes are self / firm; bruntsfield_sourced / co_sourced are legacy (pre-v7) values.
export type SourcingAttribution =
  | "self_sourced"
  | "firm_sourced"
  | "bruntsfield_sourced"
  | "co_sourced";
export type DeliveryType = "bruntsfield_led" | "consultant_led";
export type CommissionStream = "product" | "consultancy";
export type PaymentStatus = "pending" | "invoiced" | "paid";

export interface CommissionLine {
  id: string;
  owner_consultant_id: string;
  engagement_id?: string | null;
  kind: CommissionKind;
  amount: Money;
  payment_status: PaymentStatus;
  earned_on?: string | null;
  tier?: ConsultantTier | null;
  attribution?: SourcingAttribution | null;
  rate_ref?: string | null;
  base_value?: Money | null;
  source_attribution_id?: string | null;
  // v7 two-stream provenance (null on legacy / recovery lines).
  stream?: CommissionStream | null;
  product_id?: string | null;
  delivery_type?: DeliveryType | null;
  contract_year?: number | null;
  window_end?: string | null;
  client_paid_on?: string | null;
  content_hash: string;
  created_at: string;
  updated_at: string;
}

export interface EarningsSummary {
  owner_consultant_id: string;
  currency: Currency;
  ytd_earned: Money;
  pending: Money;
  invoiced: Money;
  paid: Money;
  projected_unpaid: Money;
  line_count: number;
}

export type EngagementStatus = "scoped" | "contracted" | "active" | "delivered" | "closed";
export type DeliverableStatus = "not_started" | "in_progress" | "drafted" | "delivered";
export type CommsChannel = "note" | "email" | "call" | "meeting";

export const COMMS_CHANNELS: CommsChannel[] = ["note", "email", "call", "meeting"];

export interface DeliverableSlot {
  key: string;
  label?: string | null;
  status: DeliverableStatus;
}

// --- Generated deliverables (GRS-0015/0018 backend `Deliverable` contract) ---
export type DeliverableType =
  | "executive_summary"
  | "platform_power_report"
  | "infrastructure_heatmap"
  | "modernisation_roadmap"
  | "technical_appendix"
  | "workshop_output"
  | "score_evolution";

export type DeliverableMode = "client" | "draft_internal";

export type ApprovalStatus = "draft" | "pending_approval" | "approved" | "rejected";

export interface Deliverable {
  id: string;
  owner_consultant_id: string;
  engagement_id: string;
  type: DeliverableType;
  title: string;
  ai_generated: boolean;
  approval_status: ApprovalStatus;
  approved_by_consultant_id: string | null;
  mode: DeliverableMode;
  scoring_run_id: string | null;
  coefficient_version: string | null;
  content_hash: string | null;
  generated_at: string | null;
  created_at: string;
  updated_at: string;
}

// --- AI first-draft narratives (GRS-0017 backend `AINarrative` contract) ---
export type NarrativeSection = "interpretation" | "commentary" | "recommendation";
export type NarrativeStatus = "proposed" | "approved" | "rejected";
export type ConsultantTier = "venture_associate" | "advisor" | "consultant";

export interface AINarrative {
  id: string;
  owner_consultant_id: string;
  deliverable_id: string;
  scoring_run_id: string;
  section: NarrativeSection;
  status: NarrativeStatus;
  proposed_text: string;
  drafter_version: string;
  prompt_template_version: string;
  author_tier: ConsultantTier;
  final_text: string | null;
  approved_by_consultant_id: string | null;
  approved_at: string | null;
  edit_summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface CommsLogEntry {
  id: string;
  at: string;
  channel: CommsChannel;
  author_consultant_id: string;
  body: string;
}

export interface Engagement {
  id: string;
  owner_consultant_id: string;
  prospect_id: string;
  title: string;
  status: EngagementStatus;
  started_on?: string | null;
  assessment_ids: string[];
  deliverables: DeliverableSlot[];
  comms_log: CommsLogEntry[];
  created_at: string;
  updated_at: string;
}

/* --- Workbench (GRS-0027; Loop 5 APIs) ------------------------------------------------- */

export type AssessorLevelValue = "trained" | "shadow" | "observed_lead" | "certified_lead";

export type BenchItemKind = "certification" | "drill" | "arena" | "research";

export interface BenchQueueItem {
  kind: BenchItemKind;
  priority: number;
  title: string;
  detail: string;
  action_hint: string;
  ref_id?: string | null;
}

export interface BenchQueue {
  owner_consultant_id: string;
  generated_at: string;
  items: BenchQueueItem[];
}

export interface ArenaTrendPoint {
  scored_at: string;
  completeness: number;
}

export interface PerformanceSummary {
  owner_consultant_id: string;
  level: AssessorLevelValue;
  engagements_active: number;
  engagements_completed: number;
  prospects_total: number;
  pipeline_conversion_rate: number;
  coursework_complete: boolean;
  exam_passed: boolean;
  drills_due: number;
  drill_best_streak: number;
  arena_sessions_scored: number;
  arena_best_completeness?: number | null;
  arena_trend: ArenaTrendPoint[];
}

export interface CertificationRecord {
  id: string;
  owner_consultant_id: string;
  level: AssessorLevelValue;
  coursework_complete: boolean;
  exam_score?: number | null;
  shadow_count: number;
  observed_lead_logged: boolean;
  observed_lead_signoff_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CertificationEvent {
  id: string;
  owner_consultant_id: string;
  kind: string;
  detail?: string | null;
  from_level?: AssessorLevelValue | null;
  to_level?: AssessorLevelValue | null;
  reason?: string | null;
  occurred_at: string;
}

export type LearningKind = "playbook" | "sales_journey" | "technical_primer" | "exam_quiz";
export type CertificationCredit = "none" | "coursework";

export interface LearningModule {
  id: string;
  kind: LearningKind;
  title: string;
  methodology_ref: string;
  certification_credit: CertificationCredit;
}

export interface ContentCompletion {
  id: string;
  module_id: string;
  score?: number | null;
  completed_at: string;
}

export interface DrillCard {
  id: string;
  topic: string;
  repetitions: number;
  easiness: number;
  interval_days: number;
  due_at: string;
  streak: number;
  last_reviewed_at?: string | null;
}

export type ArenaSpeaker = "advisor" | "client";

export interface ArenaTurn {
  speaker: ArenaSpeaker;
  text: string;
}

export interface PowerProbeResult {
  power_key: string;
  benefit_probed: boolean;
  barrier_probed: boolean;
}

export interface ArenaScore {
  powers: PowerProbeResult[];
  modules_evidenced: string[];
  evidence_questions: number;
  completeness: number;
}

export type ArenaStatus = "in_progress" | "scored";

export interface ArenaScenario {
  id: string;
  owner_consultant_id: string;
  title: string;
  brief: string;
  client_persona: string;
  created_at: string;
  updated_at: string;
}

export interface ArenaSession {
  id: string;
  owner_consultant_id: string;
  scenario_id: string;
  status: ArenaStatus;
  transcript: ArenaTurn[];
  score?: ArenaScore | null;
  feedback?: string | null;
  feedback_is_ai_drafted: boolean;
  drafter_version?: string | null;
  scored_at?: string | null;
}

export type CalibrationStatus = "open" | "closed";

export interface VignetteAnchor {
  subcomponent_key: string;
  reference_level: MaturityLevel;
}

export interface CalibrationVignette {
  title: string;
  excerpt: string;
  anchors: VignetteAnchor[];
}

export interface CalibrationSession {
  id: string;
  owner_consultant_id: string;
  title: string;
  status: CalibrationStatus;
  vignettes: CalibrationVignette[];
  opened_at: string;
  closed_at?: string | null;
}

export interface RatingEntry {
  vignette_index: number;
  subcomponent_key: string;
  level: MaturityLevel;
}

export interface CalibrationRating {
  id: string;
  owner_consultant_id: string;
  session_id: string;
  entries: RatingEntry[];
  submitted: boolean;
  submitted_at?: string | null;
}

export interface AnchorAgreement {
  subcomponent_key: string;
  n_raters: number;
  n_vignettes: number;
  kappa_w: number;
  ac1: number;
  flagged: boolean;
}

export interface CalibrationResult {
  session_id: string;
  computed_at: string;
  n_raters: number;
  anchors: AnchorAgreement[];
}

// --- Rating Committee sign-off (Methodology §8, GRS-0061) ---------------------------------
export type CommitteeItemType = "power" | "triad" | "module";
export type CommitteeDecisionStatus = "approved" | "rejected";

export interface CommitteeItem {
  item_type: CommitteeItemType;
  item_key: string;
  rating: string;
  label: string;
  reason: string;
}

export interface CommitteeDecision {
  id: string;
  owner_consultant_id: string;
  created_at: string;
  updated_at: string;
  assessment_id: string;
  item_type: CommitteeItemType;
  item_key: string;
  rating: string;
  status: CommitteeDecisionStatus;
  rationale: string;
  dissent_note?: string | null;
  decided_by_consultant_id: string;
  decided_at: string;
}

export interface CommitteeQueueEntry {
  item: CommitteeItem;
  decision?: CommitteeDecision | null;
}

export interface CommitteeDecisionRequest {
  item_type: CommitteeItemType;
  item_key: string;
  rating: string;
  status: CommitteeDecisionStatus;
  rationale: string;
  dissent_note?: string | null;
}

export interface CommitteeReviewSummary {
  assessment_id: string;
  subject: string;
  pending_count: number;
}

// --- Dual rating (Methodology §9, GRS-0062) ----------------------------------------------
export interface ModuleRatingDraft {
  id: string;
  owner_consultant_id: string;
  created_at: string;
  updated_at: string;
  assessment_id: string;
  module_key: string;
  ratings: SubcomponentRating[];
  submitted: boolean;
  submitted_at?: string | null;
}

export interface RaterCandidate {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
}

export interface RatingRequestSummary {
  assessment_id: string;
  subject: string;
  module_key: string;
  module_name: string;
  submitted: boolean;
}
