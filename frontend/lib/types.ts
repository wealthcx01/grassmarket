/**
 * TypeScript mirrors of the `bcap_contracts` API resources the wizard uses (GRS-0009/0010).
 * These follow the Pydantic contracts field-for-field; the backend JSON Schemas are the source of
 * truth (schema-parity CI). Kept hand-written and minimal — only what Path A needs.
 */

export type MaturityLevel = "Basic" | "Developing" | "Advanced" | "Frontier";
export type NonScoreState =
  | "Not Applicable"
  | "Not Assessed"
  // C-index Level-1 widget-observation states (ADR-0023) — present-yet-not-a-clean-pass.
  | "Present (Paywalled)"
  | "Present (Defective)";
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
  /** Optional evidence/rationale for the figure (GRS-0107). Additive; not a scoring input. */
  notes?: string | null;
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

/** Business context (GRS-0068). Mostly descriptive; `operating_model` (GRS-0079) is the profile key
 * that selects the registry view + coefficient set the assessment scores against (ADR-0025). */
export interface BusinessProfile {
  country?: string | null;
  segment?: string | null;
  operating_model?: string | null; // profile key: 'retail' (default) | 'exchange' | …
  asset_classes: string[];
  regions: string[];
  licensing?: string | null;
}

/** One selectable operating-model profile (GRS-0079) from GET /registry/profiles. `client_usable`
 *  (GRS-0156) is whether the profile scores on a client-usable coefficient set — the wizard shows the
 *  "indicative, not client-usable" caveat only for a non-retail profile that is NOT client-usable. */
export interface RegistryProfile {
  key: string;
  name: string;
  client_usable: boolean;
}

/** One Level-1 widget observation for the C-index grid (ADR-0023 / GRS-0083). A widget is either
 *  present (scored 1–5 on ease/usability/depth) or not — a non-present widget may carry
 *  `Present (Paywalled)` / `Present (Defective)`. Rarity is read from the registry, never stored. */
export interface WidgetObservation {
  widget_key: string;
  present: boolean;
  state?: NonScoreState | null; // only PRESENT_PAYWALLED / PRESENT_DEFECTIVE, only when !present
  ease?: number | null; // 1–5, only when present
  usability?: number | null;
  depth?: number | null;
  notes?: string | null;
}

export interface AssessmentDocument {
  subject: string;
  profile?: BusinessProfile | null;
  subcomponents: SubcomponentRating[];
  metrics: MetricEntry[];
  powers: PowerEntry[];
  // C-index capture (ADR-0023 / GRS-0083); default-empty so older documents load unchanged.
  c_subcomponents: SubcomponentRating[];
  widgets: WidgetObservation[];
  notes?: string | null;
}

/** Record provenance (ADR-0029): production (full gate) vs demo/sandbox (self-approvable, watermarked). */
export type RecordProvenance = "production" | "demo" | "sandbox";

/** A canonical company an assessment subject can resolve to (GRS-0100, ADR-0033). */
export interface CompanyEntity {
  entity_id: string;
  name: string;
  aliases: string[];
  domain?: string | null;
  segment?: string | null;
}

/**
 * An institution in the shared GTM registry (GRS-0193, ADR-0045). Network-shared reference data:
 * every consultant reads the same imported universe, unlike a prospect's own contacts.
 */
export interface RegistryTarget {
  target_id: string;
  name: string;
  aliases: string[];
  domain?: string | null;
  segment?: string | null;
  country?: string | null;
  ric?: string | null;
  ctb_id?: number | null;
  source: string;
  imported_on: string;
}

/**
 * A named person at a RegistryTarget (GRS-0193). `verified` means a human confirmed the person and
 * their role against a named source; an inferred or unaudited row stays false and renders flagged.
 */
export interface RegistryContact {
  contact_id: string;
  target_id: string;
  full_name: string;
  email?: string | null;
  phone?: string | null;
  job_role?: string | null;
  linkedin?: string | null;
  verified: boolean;
  source: string;
  imported_on: string;
}

export interface Assessment {
  id: string;
  owner_consultant_id: string;
  subject: string;
  entity_id?: string | null;
  state: AssessmentState;
  provenance: RecordProvenance;
  /** When the advisor last asked the founder to review this (GRS-0188). Null until submitted. */
  review_requested_at?: string | null;
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
// --- AI-assisted wizard input (GRS-0101, ADR-0032) ---
/** GUIDANCE points at a field to reconsider (no value); PREFILL proposes a starting value to accept/edit. */
export type WizardSuggestionKind = "guidance" | "prefill";

export interface WizardSuggestion {
  id: string;
  kind: WizardSuggestionKind;
  step: string;
  title: string;
  rationale: string;
  module_key?: string | null;
  subcomponent_key?: string | null;
  power_key?: string | null;
  proposed_level?: MaturityLevel | null;
}

export interface WizardSuggestions {
  assessment_id: string;
  suggester_version: string;
  suggestions: WizardSuggestion[];
}

export interface BrokeragePortfolioEntry {
  assessment_id: string;
  subject: string;
  segment?: string | null;
  state: AssessmentState;
  provenance: RecordProvenance;
  v_index?: number | null;
  // The finalised run's stored P10/P90 band (GRS-0166) — so every surface quoting the locked score
  // (portfolio, deliverable, finalised wizard rail) shows the SAME v_index + band, never a fresh
  // Monte-Carlo recompute. Null until finalised, like v_index.
  v_p10?: number | null;
  v_p90?: number | null;
  // Customer-Proposition index (ADR-0023 Stage 1) — reported alongside V, not folded in. Deterministic
  // and document-derived, so it can be present even for a draft; null when C is not yet scoreable.
  c_index?: number | null;
  uncertainty_rating?: UncertaintyRating | null;
  // Assessed / applicable subcomponents (GRS-0116) — the live-panel coverage notion; null when none.
  coverage?: number | null;
  finalised_at?: string | null;
  updated_at: string;
  // The prospect this assessment's engagement belongs to (GRS-0186) — set only when linked, so the
  // portfolio row can deep-link to the client record; null (never guessed) when unlinked.
  linked_prospect_id?: string | null;
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
  // The one-number rule (ADR-0040): the DETERMINISTIC engine points — THE quoted score on every
  // surface. The bands supply the modelled range only; their p50 is never headlined.
  v_point?: number | null;
  b_point?: number | null;
  p_point?: number | null;
  l_point?: number | null;
  blocking: string[];
  v?: IndexBand | null;
  b?: IndexBand | null;
  p?: IndexBand | null;
  l_index?: IndexBand | null;
  // C-index (ADR-0023 Stage 1): a deterministic value reported alongside V, not a band; null until
  // C is scoreable. Never summed into V (that is v1.4 / GRS-0086).
  c?: number | null;
  module_qm: Record<string, IndexBand>;
  // The DETERMINISTIC q_m per module (ADR-0040): the quoted module scores, with `module_qm` the
  // modelled range around them. Only modules that actually scored appear — a Not Assessed module
  // is absent rather than zero-filled (D9). Source for the dispersion figure (GRS-0227).
  // Optional because a payload cached before GRS-0227 shipped genuinely will not carry it, and the
  // honest render for "we don't know the spread" is to show nothing rather than to infer one.
  module_qm_point?: Record<string, number>;
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
  /** Plain-English "what it is and why it matters", operating-model aware (GRS-0103). */
  description: string;
  unit: string;
  direction: string;
  group?: string | null;
  /** Input-domain bounds (GRS-0144): a raw outside [min_raw, max_raw] is nonsensical. Used for
   *  inline field validation so an impossible value is caught at entry, not only at score time. */
  min_raw?: number | null;
  max_raw?: number | null;
}

export interface RegistryPower {
  key: string;
  name: string;
  lifecycle_stage: string;
  description: string;
}

export type WidgetRarity = "Common" | "Uncommon" | "Rare";

/** A Customer-Proposition (C) subcomponent (ADR-0023) — same shape as an L subcomponent. */
export interface RegistryCSubcomponent {
  key: string;
  name: string;
  module_key: string;
  description?: string | null;
  critical: boolean;
}

/** One of the 10 Phase-E Customer-Proposition modules (ADR-0023). */
export interface RegistryCModule {
  key: string;
  name: string;
  description: string;
  subcomponents: RegistryCSubcomponent[];
}

/** One Level-1 customer-proposition widget (ADR-0023 / GRS-0080), differentiated by rarity. */
export interface RegistryWidget {
  key: string;
  name: string;
  category: string;
  rarity: WidgetRarity;
  module_key: string;
}

export interface Registry {
  powers: RegistryPower[];
  modules: RegistryModule[];
  metrics: RegistryMetric[];
  subcomponent_status: string;
  metric_status: string;
  // Customer-Proposition (C) section (ADR-0023) — a parallel dimension to B/P/L.
  c_modules: RegistryCModule[];
  c_widgets: RegistryWidget[];
  c_status: string;
  c_widget_profile: string;
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
  website?: string | null;
  primary_contact_name?: string | null;
  primary_contact_email?: string | null;
  notes?: string | null;
  /** The one thing that has to happen next (GRS-0249). A deal without one is drifting. */
  next_action?: string | null;
  /** Independently nullable: an action with no date yet is a real state, not a missing value. */
  next_action_on?: string | null;
  created_at: string;
  updated_at: string;
}

// A first-class contact on a prospect (GRS-0111) — many per prospect, one may be primary.
export interface Contact {
  id: string;
  owner_consultant_id: string;
  prospect_id: string;
  name: string;
  email?: string | null;
  phone?: string | null;
  title?: string | null;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface WinProbability {
  score: number; // 0–100 percentage (a probability, never currency)
  label: string; // config-banded headline word (Cold / Warming / Likely / Strong)
  reasons: string[];
  missing_info: string[];
}

export interface PipelineBoardEntry {
  prospect: Prospect;
  days_in_stage: number;
  stale_after_days: number;
  stale: boolean;
  win_probability: WinProbability;
}

export interface PipelineBoard {
  generated_at: string;
  entries: PipelineBoardEntry[];
}

export interface StageHistoryEntry {
  prospect_id: string;
  from_stage: PipelineStage | null;
  to_stage: PipelineStage;
  occurred_at: string;
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

// Earnings over time + the two v7 stream totals (GRS-0133) — the incentive chart's data.
export interface EarningsTimelinePoint {
  period: string; // "YYYY-MM"
  earned: Money;
  cumulative: Money;
}

export interface EarningsTimeline {
  owner_consultant_id: string;
  currency: Currency;
  points: EarningsTimelinePoint[];
  stream_product: Money;
  stream_consultancy: Money;
}

// The live commission "carrot" for a Stream-A product (GRS-0123), from the Earnings v7 schedule.
export interface ProductCommissionCarrot {
  product_id: string;
  name: string;
  yr1_bps: number;
  yr2_bps: number;
  window_months: number;
  example_deal: Money;
  yr1_commission: Money;
  yr2_commission: Money;
  schedule_version: string;
}

/**
 * One cell of the Stream-B consultancy matrix (GRS-0187). Rates are read live from the Earnings v7
 * schedule, never typed into the UI, and the labels travel with them so wording and number cannot
 * drift apart.
 */
export interface ConsultancyCommissionCarrot {
  delivery_type: string;
  sourcing: string;
  delivery_label: string;
  sourcing_label: string;
  yr1_bps: number;
  thereafter_bps: number;
  example_deal: Money;
  yr1_commission: Money;
  thereafter_commission: Money;
  schedule_version: string;
}

// --- Sell-from-report (GRS-0162, ADR-0039) — mirrors bcap_contracts.product_fit ---

export type GapKind = "module" | "c_module" | "power";

// One assessed-and-weak target a product addresses. Module gaps carry q_m + the report's gate
// band; power gaps carry the benefit/barrier strengths. Not Assessed never appears here (D9).
export interface OpportunityGap {
  kind: GapKind;
  key: string;
  name: string;
  q_m?: number | null;
  gate_band?: MaturityLevel | null;
  benefit?: StrengthRating | null;
  barrier?: StrengthRating | null;
}

// One recommended product: the gaps it addresses in THIS assessment (evidence first) with the
// live carrot displayed alongside — the carrot never enters the ordering (ADR-0002).
export interface SellOpportunity {
  product_id: string;
  name: string;
  pitch: string;
  gaps: OpportunityGap[];
  not_yet_assessed: string[];
  carrot: ProductCommissionCarrot;
}

// Advisor-facing only — never rendered into a client deliverable (ADR-0039).
export interface SellOpportunities {
  assessment_id: string;
  subject: string;
  opportunities: SellOpportunity[];
  // Set when the catalogue has no product applicable to this operating model (GRS-0169) — the
  // honest "segment not covered yet" explanation for an empty list.
  note?: string | null;
  fit_version: string;
  coefficient_version: string;
  schedule_version: string;
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

// The advisor's own deliverables index row (GRS-0186) — a read projection enriched with the
// engagement and client so the list links straight to the record. Mirrors DeliverableIndexRow.
export interface DeliverableIndexRow {
  id: string;
  type: DeliverableType;
  title: string;
  mode: DeliverableMode;
  generated_at: string | null;
  engagement_id: string;
  engagement_title: string;
  prospect_id: string;
  prospect_company_name: string;
}

// --- AI first-draft narratives (GRS-0017 backend `AINarrative` contract) ---
export type NarrativeSection = "interpretation" | "commentary" | "recommendation";
export type NarrativeStatus = "proposed" | "approved" | "rejected";
export type ConsultantTier = "venture_associate" | "advisor" | "consultant";

/** A consultant as the API returns them — no password material (GRS-0208 act-as picker). */
export interface Consultant {
  id: string;
  email: string;
  full_name: string;
  role: "consultant" | "committee_member" | "admin";
  tier: ConsultantTier;
  is_active: boolean;
}

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
  /** ADR-0029, extended to engagements by GRS-0241. Derived from the linked assessments. */
  provenance: RecordProvenance;
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

export type BenchItemKind =
  | "rating_request"
  | "committee"
  | "certification"
  | "academy"
  | "drill"
  | "arena"
  | "research";

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
  cert_subject?: string | null;
  assessment_id?: string | null;
  occurred_at: string;
}

// Course / product certifications (GRS-0127) — alongside the assessor ladder.
export type CourseCertificationStatus = "not_started" | "in_progress" | "certified";

export interface CourseCertification {
  owner_consultant_id: string;
  subject: string;
  title: string;
  status: CourseCertificationStatus;
  course_complete: boolean;
  signed_off_by_consultant_id?: string | null;
  certified_at?: string | null;
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

// --- Bruntsfield Academy courses (GRS-0121) ---
export type LessonAuthor = "human" | "ai";

/** What a lesson reference points at (GRS-0190), used to label its link card. */
export type SourceRefKind = "docs" | "video" | "blog" | "repo";

/** A cited public source on a lesson (GRS-0190). `url` is https-only, enforced at the contract. */
export interface SourceRef {
  title: string;
  url: string;
  kind: SourceRefKind;
}

/**
 * An interpretive diagram on a lesson (GRS-0190). Inline SVG rather than a file, so a published
 * CourseVersion snapshot stays genuinely immutable. `alt` is required, never derived.
 */
export interface LessonAsset {
  caption: string;
  alt: string;
  svg: string;
}

/**
 * What a slide is for (GRS-0215). The reader styles by this and the depth tests count by it: a
 * lesson that is 30 slides of prose and no doing is not the lesson the founder asked for.
 */
export type SlideKind = "concept" | "walkthrough" | "example" | "checkpoint";

/**
 * One slide of a lesson (GRS-0215). Deliberately small — one idea, one step, or one worked
 * example. `body` is markdown; `asset` is an inline SVG for the same immutability reason
 * `LessonAsset` is. Only a CHECKPOINT slide carries a `checkpoint_prompt`.
 */
export interface Slide {
  order: number;
  kind: SlideKind;
  title: string;
  body: string;
  asset?: LessonAsset | null;
  references: SourceRef[];
  checkpoint_prompt?: string | null;
}

/** One multiple-choice question on a section test (GRS-0215). Exactly one right answer. */
export interface TestQuestion {
  prompt: string;
  options: string[];
  answer_index: number;
  /** Shown after the learner answers, right or wrong — this gate teaches rather than filters. */
  explanation: string;
}

/** The test a learner passes before the next section opens. `pass_mark` is a fraction. */
export interface SectionTest {
  questions: TestQuestion[];
  pass_mark: number;
}

/** One recorded attempt at a section test (GRS-0226). Append-only: a retake is a new row. */
export interface SectionTestAttempt {
  id: string;
  owner_consultant_id: string;
  course_id: string;
  module_id: string;
  score: number;
  passed: boolean;
  attempted_at: string;
}

/**
 * The advisor's standing on one section (GRS-0226). `unlocked` is computed server-side so the
 * rule "section N+1 opens when N is passed" is stated once, not re-derived in the reader.
 */
export interface SectionProgress {
  module_id: string;
  order: number;
  has_test: boolean;
  unlocked: boolean;
  passed: boolean;
  best_score?: number | null;
  attempts: number;
}

export interface Lesson {
  id: string;
  title: string;
  body: string;
  order: number;
  author: LessonAuthor;
  video_ref?: string | null;
  references: SourceRef[];
  assets: LessonAsset[];
  /** The lesson's slides, in order (GRS-0215). Empty on a legacy course, which still renders. */
  slides: Slide[];
  drill_topics: string[];
  measurement?: string | null;
  check_question?: string | null;
  check_answer?: string | null;
  approved: boolean;
  approved_by_consultant_id?: string | null;
  approved_at?: string | null;
}

export interface CourseModule {
  id: string;
  title: string;
  order: number;
  lessons: Lesson[];
  /** The gate a learner passes before the next section opens. Null on a legacy section. */
  section_test?: SectionTest | null;
}

export interface CourseTree {
  title: string;
  summary: string;
  certification_credit: CertificationCredit;
  mandatory_first: boolean;
  modules: CourseModule[];
}

export interface Course {
  id: string;
  slug: string;
  draft: CourseTree;
  latest_version: number;
  created_at: string;
  updated_at: string;
}

export interface CourseVersion {
  course_id: string;
  slug: string;
  version: number;
  tree: CourseTree;
  published_by_consultant_id: string;
  published_at: string;
}

export interface LessonCompletion {
  id: string;
  course_id: string;
  lesson_id: string;
  completed_at: string;
}

export interface DrillCard {
  id: string;
  topic: string;
  prompt: string;
  answer: string;
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

// --- Founder review gate (GRS-0188, ADR-0041) --------------------------------------------
// An approval names the sha256 of the document version it cleared. The gate compares that to the
// document's CURRENT hash, so editing re-opens review by arithmetic rather than by a status field.

export interface FounderApproval {
  id: string;
  owner_consultant_id: string;
  assessment_id: string;
  document_hash: string;
  approved_by_consultant_id: string;
  approved_at: string;
  created_at: string;
  updated_at: string;
}

export interface FounderReviewQueueEntry {
  id: string;
  owner_consultant_id: string;
  assessment_id: string;
  subject: string;
  advisor_name: string;
  advisor_email: string;
  requested_at: string;
  document_hash: string;
  /** True when this was signed off and then edited: the founder is re-reading, not reading. */
  previously_approved: boolean;
  /** Set when this row is a CLIENT REPORT awaiting sign-off rather than an assessment (GRS-0245). */
  deliverable_id?: string | null;
  /** On a re-review of a client report: which of the six sections differ from the approved version. */
  changed_sections?: string[];
  created_at: string;
  updated_at: string;
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

// --- The client report (GRS-0211/0219/0220) ---------------------------------------------------

/** One section of the advisor's report prose, as stored and edited. */
/** One figure the run declares, which a section is allowed to state (GRS-0230). */
export type DeclaredFigure = {
  key: string;
  label: string;
  rendered: string;
  source: string;
};

export type ReportProseSection = {
  heading: string;
  body: string[];
  tier: "free" | "engaged";
};

/** A shareable link to one deliverable's client report. Never carries the plaintext token. */
export type ClientReportLink = {
  id: string;
  deliverable_id: string;
  engagement_id: string;
  token_hash: string;
  recipient_label: string;
  expires_at: string;
  revoked_at: string | null;
  last_viewed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type SectionReadSummary = {
  section: string;
  views: number;
  total_dwell_ms: number;
  first_viewed_at: string | null;
  last_viewed_at: string | null;
};

export type ReportReadReport = {
  link_id: string;
  recipient_label: string;
  state: "active" | "expired" | "revoked";
  sections: SectionReadSummary[];
};

/** GRS-0238 — one row of the Prospecting list. Mirrors `bcap_contracts.prospecting`. */
export type ProspectingTarget = {
  target_id: string;
  name: string;
  domain: string | null;
  country: string | null;
  segment: string | null;
  segment_label: string;
  segment_kind: "firm_type" | "content_type" | "unknown";
  source: string;
  imported_on: string;
  contact_count: number;
  already_in_my_pipeline: boolean;
  /** The name is a domain stem from the import, not a verified company name. */
  name_unverified: boolean;
};

export type ProspectingPage = {
  targets: ProspectingTarget[];
  total: number;
  offset: number;
  limit: number;
};

export type SegmentFacet = {
  value: string;
  count: number;
  label: string;
  kind: "firm_type" | "content_type" | "unknown";
};

export type RegistryFacets = {
  segments: SegmentFacet[];
  countries: { value: string; count: number }[];
};

/* ---------------------------------------------------------------- Voice notes (GRS-0249) */

/**
 * Who was in the room. This decides whether the consent gate applies, so it is stated by the
 * advisor rather than inferred: an advisor dictating alone in a car park has nobody to ask for
 * consent, and a session with a client in the room has somebody who must be asked.
 * Mirrors `bcap_contracts.meetings.RecordingKind`.
 */
export type RecordingKind = "voice_note" | "recorded_session" | "not_recorded";

export type MediaKind = "transcript_text" | "audio" | "video";

/** Mirrors `bcap_contracts.meetings.MeetingTranscript`. */
export type MeetingTranscript = {
  id: string;
  owner_consultant_id: string;
  prospect_id: string | null;
  workshop_id: string | null;
  engagement_id: string | null;
  source_kind: MediaKind;
  source_filename: string;
  text: string;
  transcriber_ref: string;
  recording_kind: RecordingKind;
  /** Set only on a recorded session. Null on a voice note — nobody was there to agree. */
  consent_confirmed_at: string | null;
  /** The exact wording agreed to, stored in full rather than referenced. */
  consent_wording: string | null;
  /** The kept audio this transcript came from, so a disputed correction can be re-checked. */
  recording_document_id: string | null;
  retention_until: string | null;
  created_at: string;
  updated_at: string;
};

/**
 * The founder-approved consent line, fetched rather than hardcoded so there is exactly one copy
 * of the wording in the system. Showing different text and uploading anyway is refused by the API.
 */
export type ConsentLine = { wording: string };

/**
 * The upload body for `POST /transcripts/media`.
 *
 * Consent is either complete or absent — there is no half state. `recording_kind:
 * "recorded_session"` requires both consent fields and the wording must be the one the API served;
 * `"voice_note"` requires both to be absent, because the advisor was alone. The API refuses either
 * mistake and stores nothing.
 */
export type UploadRecordingRequest = {
  media_base64: string;
  source_filename: string;
  content_type: string;
  source_kind: "audio" | "video";
  prospect_id?: string | null;
  workshop_id?: string | null;
  engagement_id?: string | null;
  recording_kind: RecordingKind;
  consent_confirmed_at?: string | null;
  consent_wording?: string | null;
  /** Keep the audio beside the transcript. Needs one of the parent ids to file it under. */
  keep_recording?: boolean;
};

/* ------------------------------------------- Voice note → pipeline proposal (GRS-0249 scope 4) */

/**
 * The fields a voice note may propose. A closed set, mirroring
 * `bcap_contracts.voice_notes.PipelineField`: an extractor cannot invent a field name, and every
 * one of these maps to a write path that already exists.
 */
export type PipelineField = "stage" | "next_action" | "next_action_on" | "comms_note";

export type ExtractionConfidence = "high" | "medium" | "low";

export type ProposalStatus = "proposed" | "confirmed" | "discarded";

/** One field a voice note proposed, and what the advisor did with it. */
export type ProposedField = {
  id: string;
  owner_consultant_id: string;
  proposal_id: string;
  transcript_id: string;
  field: PipelineField;
  /** What the machine suggested. Kept even after a correction. */
  proposed_value: string | null;
  confidence: ExtractionConfidence;
  span_start: number;
  span_end: number;
  /** True once this field specifically was applied — not merely that the proposal was answered. */
  accepted: boolean;
  /** What the advisor actually agreed to. Null where they left the field out. */
  confirmed_value: string | null;
};

/**
 * A gated pipeline proposal drawn from one voice note. Nothing here has touched the prospect:
 * the values are applied only by confirming, and only the ones the advisor confirms.
 */
export type VoiceNoteProposal = {
  id: string;
  owner_consultant_id: string;
  prospect_id: string;
  transcript_id: string;
  status: ProposalStatus;
  extractor_version: string;
  /** Fields the extractor looked for and did not find — stated, so silence is never ambiguous. */
  gaps: string[];
  fields: ProposedField[];
  confirmed_at: string | null;
  discarded_at: string | null;
  created_at: string;
  updated_at: string;
};

/** Human labels for the proposed fields. British English, sentence case, no jargon. */
export const PIPELINE_FIELD_LABEL: Record<PipelineField, string> = {
  stage: "Move to stage",
  next_action: "Next action",
  next_action_on: "Due",
  comms_note: "Communication log note",
};
