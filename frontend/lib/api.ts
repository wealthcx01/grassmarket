/**
 * Typed fetch helper for the Grassmarket (Bruntsfield Advisor Studio) backend.
 *
 * Reads NEXT_PUBLIC_API_BASE_URL (default http://localhost:8000). Because it is a
 * NEXT_PUBLIC_ var it is inlined at build time and safe to reference on the client.
 *
 * Fail-loud in spirit: a non-2xx response throws ApiError with the parsed body when
 * available, rather than silently returning a defaulted shape. Callers decide how to
 * present the failure.
 */

import type {
  ClientReportLink,
  ConsentLine,
  MeetingTranscript,
  UploadRecordingRequest,
  Consultant,
  DeclaredFigure,
  ReportProseSection,
  ReportReadReport,
  ProspectingPage,
  RegistryFacets,
  FounderApproval,
  FounderReviewQueueEntry,
  AINarrative,
  ArenaScenario,
  ArenaSession,
  ArenaTurn,
  Assessment,
  AssessmentDocument,
  BenchQueue,
  BrokeragePortfolioEntry,
  CalibrationRating,
  CalibrationResult,
  CalibrationSession,
  CertificationEvent,
  CertificationRecord,
  CourseCertification,
  CommissionLine,
  CommitteeDecision,
  CommitteeDecisionRequest,
  CommitteeQueueEntry,
  CommitteeReviewSummary,
  CommsChannel,
  CommsLogEntry,
  ConsultancyCommissionCarrot,
  CompanyEntity,
  RegistryContact,
  Contact,
  ContentCompletion,
  Course,
  CourseTree,
  CourseVersion,
  LessonCompletion,
  SectionProgress,
  SectionTestAttempt,
  CertificationCredit,
  Deliverable,
  DeliverableIndexRow,
  DeliverableSlot,
  DeliverableType,
  DrillCard,
  EarningsSummary,
  EarningsTimeline,
  Engagement,
  LearningModule,
  ModuleRatingDraft,
  NarrativeSection,
  LiveScore,
  WizardSuggestions,
  RaterCandidate,
  RatingRequestSummary,
  SubcomponentRating,
  PerformanceSummary,
  PipelineBoard,
  PipelineForecast,
  PipelineStage,
  ProductCommissionCarrot,
  Prospect,
  RatingEntry,
  RecoveryFeeAttribution,
  Registry,
  RegistryProfile,
  RubricAnchor,
  ScenarioComparison,
  SellOpportunities,
  StageHistoryEntry,
  Workshop,
} from "@/lib/types";

export const API_BASE_URL: string =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:8000";

/**
 * User-facing copy for a transport failure (backend unreachable, CORS, DNS). Deliberately generic —
 * it never leaks the internal API host:port into the UI (GRS-0163). A caught `ApiError` with
 * `status === 0` is the signal to render a "can't reach — retry" state rather than a dead spinner.
 */
export const NETWORK_ERROR_MESSAGE = "Can't reach the studio. Check your connection and try again.";

/** Where the access + refresh tokens live (GRS-0120). The access token is short-lived; the refresh
 *  token rotates it silently so an active advisor is not signed out at the 30-min TTL. */
export const TOKEN_KEY = "bas.access_token";
export const REFRESH_TOKEN_KEY = "bas.refresh_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

/** Persist a freshly-issued pair (login, hand-off exchange, or a refresh rotation). */
export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, accessToken);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Single-flight refresh: many concurrent 401s share ONE /auth/refresh call, so a rotated (single-use)
// refresh token is not spent by a stampede. Returns true when a fresh pair was stored.
let refreshInFlight: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
          method: "POST",
          headers: { Accept: "application/json", "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refresh }),
        });
        if (!res.ok) {
          clearToken(); // a dead refresh token → genuinely signed out; fall back to full login
          return false;
        }
        const body = (await res.json()) as LoginResponse;
        setTokens(body.access_token, body.refresh_token);
        return true;
      } catch {
        return false;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

/** Backend GET /health — coded defensively; fields beyond `status` are optional. */
export interface HealthResponse {
  status: string;
  version?: string;
  service?: string;
}

/** Backend POST /auth/login request/response contract. */
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;
  /**
   * True when this status-0 error is an intentional fetch abort (navigation / a superseded request),
   * NOT a real transport failure. Callers swallow aborts but must SURFACE a genuine unreachable
   * backend — otherwise a page that renders "Loading…" while its data is null sits there forever
   * (GRS-0163). `status === 0 && !aborted` is the "can't reach the studio" signal.
   */
  readonly aborted: boolean;

  constructor(status: number, message: string, body: unknown, aborted = false) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
    this.aborted = aborted;
  }
}

/** Was this thrown cause an AbortController abort (navigation / superseded fetch)? Checked by
 *  `name`, not `instanceof` alone — DOMException does not reliably extend Error across browsers,
 *  and a false negative here would flash phantom "can't reach" errors on every navigation. */
function isAbort(cause: unknown): boolean {
  return (cause instanceof DOMException || cause instanceof Error) && cause.name === "AbortError";
}

async function parseBody(res: Response): Promise<unknown> {
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      return await res.json();
    } catch {
      return null;
    }
  }
  try {
    return await res.text();
  } catch {
    return null;
  }
}

/** Extract a human-readable message from a FastAPI-style error body when possible. */
function messageFromBody(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

async function request<T>(path: string, init?: RequestInit, retried = false): Promise<T> {
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
  let res: Response;
  try {
    res = await fetch(url, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });
  } catch (cause) {
    // Network failure (backend not running, CORS, DNS). Surface it, don't swallow.
    throw new ApiError(0, NETWORK_ERROR_MESSAGE, cause, isAbort(cause));
  }

  // Expiry-aware retry (GRS-0120): a 401 on an authed call means the access token likely lapsed —
  // transparently refresh once and retry before surfacing signed-out. `/auth/*` calls are never
  // intercepted (that would loop the login/refresh flow itself).
  if (res.status === 401 && !retried && !path.startsWith("/auth/")) {
    if (await tryRefresh()) {
      // Swap in the freshly-rotated access token (authHeaders() now reads the new one).
      const newInit: RequestInit = { ...init, headers: { ...init?.headers, ...authHeaders() } };
      return request<T>(path, newInit, true);
    }
  }

  const body = await parseBody(res);
  if (!res.ok) {
    throw new ApiError(res.status, messageFromBody(body, `Request failed (${res.status})`), body);
  }
  return body as T;
}

export const api = {
  health(signal?: AbortSignal): Promise<HealthResponse> {
    return request<HealthResponse>("/health", { method: "GET", signal });
  },

  login(payload: LoginRequest, signal?: AbortSignal): Promise<LoginResponse> {
    return request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
      signal,
    });
  },

  // Self-service password change (GRS-0148d). 204 on success; 401 if the current password is wrong
  // or the account is OAuth-only; 422 if the new password is under the 12-char floor.
  changePassword(currentPassword: string, newPassword: string, signal?: AbortSignal): Promise<void> {
    return request<void>("/auth/change-password", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      signal,
    });
  },

  // Exchange a single-use Google login hand-off code for the GM JWT (GRS-0074).
  exchangeSession(code: string, signal?: AbortSignal): Promise<LoginResponse> {
    return request<LoginResponse>("/auth/session/exchange", {
      method: "POST",
      body: JSON.stringify({ code }),
      signal,
    });
  },

  // --- Assessments (all JWT-scoped server-side; the client carries the token) ---
  // The registry the wizard renders — for an operating-model profile view (GRS-0079). Retail
  // (default/omitted) is the full superset.
  registry(profile?: string, signal?: AbortSignal): Promise<Registry> {
    const query = profile ? `?profile=${encodeURIComponent(profile)}` : "";
    return request<Registry>(`/registry${query}`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  registryProfiles(signal?: AbortSignal): Promise<RegistryProfile[]> {
    return request<RegistryProfile[]>("/registry/profiles", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  createAssessment(
    subject: string,
    provenance: "production" | "sandbox" = "production",
    entityId?: string | null,
    signal?: AbortSignal,
  ): Promise<Assessment> {
    return request<Assessment>("/assessments", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ subject, provenance, entity_id: entityId ?? null }),
      signal,
    });
  },

  // Company entity lookup (GRS-0100, ADR-0033) — proposes candidates; the advisor picks one.
  searchEntities(q: string, signal?: AbortSignal): Promise<CompanyEntity[]> {
    return request<CompanyEntity[]>(`/entities/search?q=${encodeURIComponent(q)}`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // The people known at an imported institution (GRS-0193, ADR-0045). Network-shared, so this is
  // deliberately NOT the same call as a prospect's own owner-private contacts.
  listRegistryContacts(targetId: string, signal?: AbortSignal): Promise<RegistryContact[]> {
    return request<RegistryContact[]>(
      `/entities/${encodeURIComponent(targetId)}/contacts`,
      { method: "GET", headers: authHeaders(), signal },
    );
  },

  // Browse the imported universe (GRS-0238). Network-shared read; the one per-advisor field in
  // the response is `already_in_my_pipeline`, joined server-side against the caller's own book.
  listRegistryTargets(
    params: { segment?: string; country?: string; q?: string; offset?: number; limit?: number },
    signal?: AbortSignal,
  ): Promise<ProspectingPage> {
    const qs = new URLSearchParams();
    if (params.segment) qs.set("segment", params.segment);
    if (params.country) qs.set("country", params.country);
    if (params.q) qs.set("q", params.q);
    if (params.offset) qs.set("offset", String(params.offset));
    if (params.limit) qs.set("limit", String(params.limit));
    const suffix = qs.toString() ? `?${qs}` : "";
    return request<ProspectingPage>(`/entities${suffix}`, { method: "GET", headers: authHeaders(), signal });
  },

  // GRS-0239 scope 3. Idempotent by design on the server: re-confirming is a no-op, not a 409,
  // so the client never has to distinguish "already done" from "just done".
  confirmCheckpoint(
    slug: string,
    lessonId: string,
    slideOrder: number,
    signal?: AbortSignal,
  ): Promise<{ confirmed: number; total: number }> {
    return request<{ confirmed: number; total: number }>(
      `/workbench/courses/${encodeURIComponent(slug)}/lessons/${lessonId}/checkpoints/${slideOrder}`,
      { method: "POST", headers: authHeaders(), signal },
    );
  },

  checkpointProgress(
    slug: string,
    lessonId: string,
    signal?: AbortSignal,
  ): Promise<{ confirmed: number; total: number }> {
    return request<{ confirmed: number; total: number }>(
      `/workbench/courses/${encodeURIComponent(slug)}/lessons/${lessonId}/checkpoints`,
      { method: "GET", headers: authHeaders(), signal },
    );
  },

  registryFacets(signal?: AbortSignal): Promise<RegistryFacets> {
    return request<RegistryFacets>("/entities/facets", { method: "GET", headers: authHeaders(), signal });
  },

  assessmentsForEntity(entityId: string, signal?: AbortSignal): Promise<Assessment[]> {
    return request<Assessment[]>(`/assessments/for-entity/${encodeURIComponent(entityId)}`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  listAssessments(signal?: AbortSignal): Promise<Assessment[]> {
    return request<Assessment[]>("/assessments", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  brokeragePortfolio(signal?: AbortSignal): Promise<BrokeragePortfolioEntry[]> {
    return request<BrokeragePortfolioEntry[]>("/assessments/portfolio", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  getAssessment(id: string, signal?: AbortSignal): Promise<Assessment> {
    return request<Assessment>(`/assessments/${id}`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  saveAssessment(id: string, doc: AssessmentDocument, signal?: AbortSignal): Promise<Assessment> {
    return request<Assessment>(`/assessments/${id}`, {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify(doc),
      signal,
    });
  },

  liveScore(id: string, signal?: AbortSignal): Promise<LiveScore> {
    return request<LiveScore>(`/assessments/${id}/live-score`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // AI-assisted wizard input suggestions (GRS-0101, ADR-0032).
  wizardSuggestions(id: string, signal?: AbortSignal): Promise<WizardSuggestions> {
    return request<WizardSuggestions>(`/assessments/${id}/suggestions`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // "What can I sell against this report?" — the deterministic gap→product join (GRS-0162,
  // ADR-0039). Finalised assessments only (409 otherwise); advisor-facing, never client-facing.
  sellOpportunities(id: string, signal?: AbortSignal): Promise<SellOpportunities> {
    return request<SellOpportunities>(`/assessments/${id}/sell-opportunities`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  finaliseAssessment(id: string, signal?: AbortSignal): Promise<Assessment> {
    return request<Assessment>(`/assessments/${id}/finalise`, {
      method: "POST",
      headers: authHeaders(),
      signal,
    });
  },

  evaluateScenarios(
    id: string,
    scenarios: { name: string; document: AssessmentDocument }[],
    signal?: AbortSignal,
  ): Promise<ScenarioComparison> {
    return request<ScenarioComparison>(`/assessments/${id}/scenarios`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ scenarios }),
      signal,
    });
  },

  // --- Rating Committee sign-off (§8, GRS-0061) ---
  committeeReviewQueue(signal?: AbortSignal): Promise<CommitteeReviewSummary[]> {
    return request<CommitteeReviewSummary[]>(`/committee/queue`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  committeeQueue(id: string, signal?: AbortSignal): Promise<CommitteeQueueEntry[]> {
    return request<CommitteeQueueEntry[]>(`/assessments/${id}/committee`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  decideCommitteeItem(
    id: string,
    decision: CommitteeDecisionRequest,
    signal?: AbortSignal,
  ): Promise<CommitteeDecision> {
    return request<CommitteeDecision>(`/assessments/${id}/committee/decide`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(decision),
      signal,
    });
  },

  // --- Founder review gate (GRS-0188, ADR-0041) ---
  // The founder signs what goes out. An approval names the document version it cleared, so any
  // edit re-opens review on its own; there is no "un-approve" call here because there is nothing
  // to un-approve.
  founderReviewQueue(signal?: AbortSignal): Promise<FounderReviewQueueEntry[]> {
    return request<FounderReviewQueueEntry[]>(`/founder-review/queue`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  submitForFounderReview(id: string, signal?: AbortSignal): Promise<Assessment> {
    return request<Assessment>(`/assessments/${id}/submit-for-review`, {
      method: "POST",
      headers: authHeaders(),
      signal,
    });
  },

  approveCurrentVersion(id: string, signal?: AbortSignal): Promise<FounderApproval> {
    return request<FounderApproval>(`/assessments/${id}/founder-approval`, {
      method: "POST",
      headers: authHeaders(),
      signal,
    });
  },
  /** Sign off a client report's prose (GRS-0245). Separate from the assessment approval because it
      is bound to a different hash — the words, not the scored document. */
  /** Who this session currently is. While acting-as (GRS-0208) it answers as the SUBJECT, which
      is what makes the banner's name the right one to show. */
  me(signal?: AbortSignal): Promise<{ id: string; full_name: string; email: string }> {
    return request(`/auth/me`, { headers: authHeaders(), signal });
  },
  /** Who this admin could act as (GRS-0208). 403 for anyone else. */
  actAsCandidates(signal?: AbortSignal): Promise<Consultant[]> {
    return request<Consultant[]>(`/auth/act-as/candidates`, { headers: authHeaders(), signal });
  },
  startActingAs(
    consultantId: string,
    signal?: AbortSignal,
  ): Promise<{
    access_token: string;
    subject_consultant_id: string;
    subject_name: string;
    subject_email: string;
  }> {
    return request(`/auth/act-as/${consultantId}`, {
      method: "POST",
      headers: authHeaders(),
      signal,
    });
  },
  stopActingAs(signal?: AbortSignal): Promise<{ access_token: string }> {
    return request(`/auth/act-as`, { method: "DELETE", headers: authHeaders(), signal });
  },
  approveReport(deliverableId: string, signal?: AbortSignal): Promise<FounderApproval> {
    return request<FounderApproval>(`/deliverables/${deliverableId}/report-approval`, {
      method: "POST",
      headers: authHeaders(),
      signal,
    });
  },
  submitReportForReview(deliverableId: string, signal?: AbortSignal): Promise<void> {
    return request<void>(`/deliverables/${deliverableId}/submit-report-for-review`, {
      method: "POST",
      headers: authHeaders(),
      signal,
    });
  },

  currentFounderApproval(id: string, signal?: AbortSignal): Promise<FounderApproval | null> {
    return request<FounderApproval | null>(`/assessments/${id}/founder-approval`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // --- Dual rating (§9, GRS-0062) ---
  lookupConsultantByEmail(email: string, signal?: AbortSignal): Promise<RaterCandidate> {
    return request<RaterCandidate>(`/consultants/by-email?email=${encodeURIComponent(email)}`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  myRatingRequests(signal?: AbortSignal): Promise<RatingRequestSummary[]> {
    return request<RatingRequestSummary[]>(`/assessments/rating-requests`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  assignRater(id: string, moduleKey: string, raterId: string, signal?: AbortSignal): Promise<ModuleRatingDraft> {
    return request<ModuleRatingDraft>(`/assessments/${id}/modules/${moduleKey}/raters`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ rater_consultant_id: raterId }),
      signal,
    });
  },

  getMyModuleRating(id: string, moduleKey: string, signal?: AbortSignal): Promise<ModuleRatingDraft> {
    return request<ModuleRatingDraft>(`/assessments/${id}/modules/${moduleKey}/my-rating`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  updateMyModuleRating(id: string, moduleKey: string, ratings: SubcomponentRating[], signal?: AbortSignal): Promise<ModuleRatingDraft> {
    return request<ModuleRatingDraft>(`/assessments/${id}/modules/${moduleKey}/my-rating`, {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify({ ratings }),
      signal,
    });
  },

  submitMyModuleRating(id: string, moduleKey: string, signal?: AbortSignal): Promise<ModuleRatingDraft> {
    return request<ModuleRatingDraft>(`/assessments/${id}/modules/${moduleKey}/my-rating/submit`, {
      method: "POST",
      headers: authHeaders(),
      signal,
    });
  },

  listModuleRatings(id: string, moduleKey: string, signal?: AbortSignal): Promise<ModuleRatingDraft[]> {
    return request<ModuleRatingDraft[]>(`/assessments/${id}/modules/${moduleKey}/ratings`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  resolveModuleConsensus(id: string, moduleKey: string, resolved: SubcomponentRating[], signal?: AbortSignal): Promise<Assessment> {
    return request<Assessment>(`/assessments/${id}/modules/${moduleKey}/consensus`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ resolved }),
      signal,
    });
  },

  guidance(subcomponentKey: string, signal?: AbortSignal): Promise<RubricAnchor[]> {
    return request<RubricAnchor[]>(`/guidance/subcomponents/${subcomponentKey}`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // --- Pipeline / prospects (GRS-0011/0014) ---
  pipelineBoard(signal?: AbortSignal): Promise<PipelineBoard> {
    return request<PipelineBoard>("/pipeline/board", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  pipelineForecast(signal?: AbortSignal): Promise<PipelineForecast> {
    return request<PipelineForecast>("/pipeline/forecast", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  createProspect(
    body: {
      company_name: string;
      sector?: string | null;
      website?: string | null;
      // GRS-0238: set when claimed from Prospecting, so the registry row and the pipeline card
      // are linked by id rather than by name.
      registry_target_id?: string | null;
    },
    signal?: AbortSignal,
  ): Promise<Prospect> {
    return request<Prospect>("/prospects", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
      signal,
    });
  },

  /** Patch a prospect's editable fields (GRS-0111). Only the fields sent are changed. */
  updateProspect(
    id: string,
    patch: Partial<
      Pick<
        Prospect,
        "company_name" | "sector" | "website" | "primary_contact_name" | "primary_contact_email" | "notes"
      >
    >,
    signal?: AbortSignal,
  ): Promise<Prospect> {
    return request<Prospect>(`/prospects/${id}`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify(patch),
      signal,
    });
  },

  getProspect(id: string, signal?: AbortSignal): Promise<Prospect> {
    return request<Prospect>(`/prospects/${id}`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // --- Contacts (first-class, GRS-0111) ---
  listContacts(prospectId: string, signal?: AbortSignal): Promise<Contact[]> {
    return request<Contact[]>(`/prospects/${prospectId}/contacts`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  createContact(
    prospectId: string,
    body: { name: string; email?: string | null; phone?: string | null; title?: string | null; is_primary?: boolean },
    signal?: AbortSignal,
  ): Promise<Contact> {
    return request<Contact>(`/prospects/${prospectId}/contacts`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
      signal,
    });
  },

  updateContact(
    prospectId: string,
    contactId: string,
    patch: Partial<Pick<Contact, "name" | "email" | "phone" | "title" | "is_primary">>,
    signal?: AbortSignal,
  ): Promise<Contact> {
    return request<Contact>(`/prospects/${prospectId}/contacts/${contactId}`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify(patch),
      signal,
    });
  },

  deleteContact(prospectId: string, contactId: string, signal?: AbortSignal): Promise<void> {
    return request<void>(`/prospects/${prospectId}/contacts/${contactId}`, {
      method: "DELETE",
      headers: authHeaders(),
      signal,
    });
  },

  /** The prospect's stage timeline, oldest first (GRS-0111). Owner-scoped server-side. */
  prospectHistory(id: string, signal?: AbortSignal): Promise<StageHistoryEntry[]> {
    return request<StageHistoryEntry[]>(`/prospects/${id}/history`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  /** Move a prospect to a new stage. The BACKEND owns legality — an illegal move throws
   * ApiError(409) and the caller reverts the card + surfaces the reason. */
  updateProspectStage(id: string, stage: PipelineStage, signal?: AbortSignal): Promise<Prospect> {
    return request<Prospect>(`/prospects/${id}/stage`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({ stage }),
      signal,
    });
  },

  // --- Workshops + recovery fees (GRS-0012/0014) ---
  createWorkshop(
    body: { prospect_id: string; scheduled_for?: string | null; pre_workshop_brief?: string | null },
    signal?: AbortSignal,
  ): Promise<Workshop> {
    return request<Workshop>("/workshops", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
      signal,
    });
  },

  listWorkshops(signal?: AbortSignal): Promise<Workshop[]> {
    return request<Workshop[]>("/workshops", { method: "GET", headers: authHeaders(), signal });
  },

  getWorkshop(id: string, signal?: AbortSignal): Promise<Workshop> {
    return request<Workshop>(`/workshops/${id}`, { method: "GET", headers: authHeaders(), signal });
  },

  deliverWorkshop(
    id: string,
    body: { delivered_on: string; workshop_output?: string | null },
    signal?: AbortSignal,
  ): Promise<Workshop> {
    return request<Workshop>(`/workshops/${id}/deliver`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
      signal,
    });
  },

  attributeRecoveryFee(
    id: string,
    contracted_on: string,
    signal?: AbortSignal,
  ): Promise<RecoveryFeeAttribution> {
    return request<RecoveryFeeAttribution>(`/workshops/${id}/recovery-fee`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ contracted_on }),
      signal,
    });
  },

  listRecoveryFees(signal?: AbortSignal): Promise<RecoveryFeeAttribution[]> {
    return request<RecoveryFeeAttribution[]>("/recovery-fees", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // --- Engagements (GRS-0013/0014) ---
  createEngagement(
    body: {
      prospect_id: string;
      title: string;
      started_on?: string | null;
      assessment_ids?: string[];
      deliverables?: DeliverableSlot[];
    },
    signal?: AbortSignal,
  ): Promise<Engagement> {
    return request<Engagement>("/engagements", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
      signal,
    });
  },

  listEngagements(signal?: AbortSignal): Promise<Engagement[]> {
    return request<Engagement[]>("/engagements", { method: "GET", headers: authHeaders(), signal });
  },

  getEngagement(id: string, signal?: AbortSignal): Promise<Engagement> {
    return request<Engagement>(`/engagements/${id}`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // Link a finalised assessment to an existing engagement (GRS-0039) — closes the
  // contract -> assessment -> deliverable loop. 409 if unfinalised or already linked.
  linkAssessment(engagementId: string, assessmentId: string, signal?: AbortSignal): Promise<Engagement> {
    return request<Engagement>(`/engagements/${engagementId}/assessments`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ assessment_id: assessmentId }),
      signal,
    });
  },

  appendComms(
    id: string,
    body: { channel: CommsChannel; body: string },
    signal?: AbortSignal,
  ): Promise<CommsLogEntry> {
    return request<CommsLogEntry>(`/engagements/${id}/comms`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
      signal,
    });
  },

  // --- Deliverables (GRS-0015/0018; JWT-scoped, cross-owner → 404) ---
  listDeliverables(engagementId: string, signal?: AbortSignal): Promise<Deliverable[]> {
    return request<Deliverable[]>(`/engagements/${engagementId}/deliverables`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // The advisor's own deliverables index (GRS-0186), owner-scoped, newest first.
  listAllDeliverables(signal?: AbortSignal): Promise<DeliverableIndexRow[]> {
    return request<DeliverableIndexRow[]>(`/deliverables`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  generateDeliverable(
    engagementId: string,
    body: { deliverable_type: DeliverableType; client_facing: boolean },
    signal?: AbortSignal,
  ): Promise<Deliverable> {
    return request<Deliverable>(`/engagements/${engagementId}/deliverables`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
      signal,
    });
  },

  /**
   * Download a deliverable's regenerated .docx. Not a plain link: the endpoint needs the bearer
   * token, so we fetch the blob with auth and let the caller trigger the browser download. A gate
   * refusal (draft coefficients, or `clientFacing` with an unapproved AI narrative) surfaces as an
   * `ApiError` (409) with the backend's plain-English detail — never a silently broken download.
   */
  async downloadDeliverable(
    id: string,
    opts?: { clientFacing?: boolean; signal?: AbortSignal },
  ): Promise<{ blob: Blob; filename: string }> {
    const query = opts?.clientFacing ? "?client_facing=true" : "";
    const url = `${API_BASE_URL}/deliverables/${id}/download${query}`;
    let res: Response;
    try {
      res = await fetch(url, { method: "GET", headers: authHeaders(), signal: opts?.signal });
    } catch (cause) {
      throw new ApiError(0, NETWORK_ERROR_MESSAGE, cause, isAbort(cause));
    }
    if (!res.ok) {
      const body = await parseBody(res);
      throw new ApiError(res.status, messageFromBody(body, `Download failed (${res.status})`), body);
    }
    const blob = await res.blob();
    const disposition = res.headers.get("content-disposition") ?? "";
    const match = /filename="?([^"]+)"?/.exec(disposition);
    return { blob, filename: match?.[1] ?? `${id}.docx` };
  },

  // --- The client report (GRS-0211/0219/0220) ------------------------------------------------

  /** The advisor's six sections. An unwritten report returns an empty draft, never a blank page. */
  getReportProse(
    deliverableId: string,
    signal?: AbortSignal,
  ): Promise<{
    sections: Record<string, ReportProseSection>;
    written: boolean;
    /** Per section key: the figures the run declares (GRS-0230 scope 3). */
    available_figures?: Record<string, DeclaredFigure[]>;
    /** Whose report this is (GRS-0231) — the identity the PDF cover prints. */
    subject?: string | null;
    engagement_title?: string | null;
    provenance?: string | null;
    operating_model?: string | null;
  }> {
    return request(`/deliverables/${deliverableId}/report-prose`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  saveReportProse(
    deliverableId: string,
    sections: Record<string, ReportProseSection>,
    signal?: AbortSignal,
  ): Promise<{
    sections: Record<string, ReportProseSection>;
    written: boolean;
    /** Per section key: the figures the run declares (GRS-0230 scope 3). */
    available_figures?: Record<string, DeclaredFigure[]>;
    /** Whose report this is (GRS-0231) — the identity the PDF cover prints. */
    subject?: string | null;
    engagement_title?: string | null;
    provenance?: string | null;
    operating_model?: string | null;
  }> {
    return request(`/deliverables/${deliverableId}/report-prose`, {
      method: "PUT",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ sections }),
      signal,
    });
  },

  /**
   * The branded PDF (GRS-0219). A report with unwritten sections returns 409 naming them, which
   * surfaces to the advisor as the backend's own sentence rather than a generic failure.
   */
  async downloadClientReportPdf(
    deliverableId: string,
    signal?: AbortSignal,
  ): Promise<{ blob: Blob; filename: string }> {
    const url = `${API_BASE_URL}/deliverables/${deliverableId}/client-report.pdf`;
    let res: Response;
    try {
      res = await fetch(url, { method: "GET", headers: authHeaders(), signal });
    } catch (cause) {
      throw new ApiError(0, NETWORK_ERROR_MESSAGE, cause, isAbort(cause));
    }
    if (!res.ok) {
      const body = await parseBody(res);
      throw new ApiError(res.status, messageFromBody(body, `Download failed (${res.status})`), body);
    }
    const blob = await res.blob();
    const disposition = res.headers.get("content-disposition") ?? "";
    const match = /filename="?([^"]+)"?/.exec(disposition);
    return { blob, filename: match?.[1] ?? `${deliverableId}.pdf` };
  },

  listReportLinks(deliverableId: string, signal?: AbortSignal): Promise<ClientReportLink[]> {
    return request(`/deliverables/${deliverableId}/links`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  /** The plaintext token comes back exactly once, here. It is not stored and cannot be re-read. */
  createReportLink(
    deliverableId: string,
    body: { recipient_label: string; expires_in_days?: number },
    signal?: AbortSignal,
  ): Promise<{ link: ClientReportLink; token: string; share_path: string }> {
    return request(`/deliverables/${deliverableId}/links`, {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  },

  revokeReportLink(linkId: string, signal?: AbortSignal): Promise<ClientReportLink> {
    return request(`/report-links/${linkId}/revoke`, {
      method: "POST",
      headers: authHeaders(),
      signal,
    });
  },

  reportLinkReads(linkId: string, signal?: AbortSignal): Promise<ReportReadReport> {
    return request(`/report-links/${linkId}/reads`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  /**
   * Preview a FINALISED assessment's deliverable as a watermarked .docx — WITHOUT an engagement
   * (GRS-0154). This is the solo/sandbox "see the real deliverable" path: internal-only (never
   * client-facing), so it renders even for a draft wealth/exchange profile. A 409 (unfinalised, or a
   * committee gate) surfaces as an ApiError with the backend's plain-English detail.
   */
  async previewAssessmentDeliverable(
    assessmentId: string,
    opts?: { deliverableType?: string; signal?: AbortSignal },
  ): Promise<{ blob: Blob; filename: string }> {
    const type = opts?.deliverableType ?? "platform_power_report";
    const url = `${API_BASE_URL}/assessments/${assessmentId}/deliverable-preview?deliverable_type=${type}`;
    let res: Response;
    try {
      res = await fetch(url, { method: "GET", headers: authHeaders(), signal: opts?.signal });
    } catch (cause) {
      throw new ApiError(0, NETWORK_ERROR_MESSAGE, cause, isAbort(cause));
    }
    if (!res.ok) {
      const body = await parseBody(res);
      throw new ApiError(res.status, messageFromBody(body, `Preview failed (${res.status})`), body);
    }
    const blob = await res.blob();
    const disposition = res.headers.get("content-disposition") ?? "";
    const match = /filename="?([^"]+)"?/.exec(disposition);
    return { blob, filename: match?.[1] ?? `preview-${assessmentId}.docx` };
  },

  // --- AI narratives (GRS-0017; propose is AI, approve is human — the runtime gate) ---
  listNarratives(deliverableId: string, signal?: AbortSignal): Promise<AINarrative[]> {
    return request<AINarrative[]>(`/deliverables/${deliverableId}/narratives`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  proposeNarratives(
    deliverableId: string,
    sections?: NarrativeSection[],
    signal?: AbortSignal,
  ): Promise<AINarrative[]> {
    return request<AINarrative[]>(`/deliverables/${deliverableId}/narratives`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(sections ? { sections } : {}),
      signal,
    });
  },

  approveNarrative(
    narrativeId: string,
    body: { final_text?: string },
    signal?: AbortSignal,
  ): Promise<AINarrative> {
    return request<AINarrative>(`/narratives/${narrativeId}/approve`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
      signal,
    });
  },

  // --- Workbench: bench queue + performance (GRS-0026) ---
  benchQueue(signal?: AbortSignal): Promise<BenchQueue> {
    return request<BenchQueue>("/bench/queue", { method: "GET", headers: authHeaders(), signal });
  },

  performance(advisorId: string, signal?: AbortSignal): Promise<PerformanceSummary> {
    return request<PerformanceSummary>(`/bench/performance/${advisorId}`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // --- Workbench: certification (GRS-0023) ---
  certification(advisorId: string, signal?: AbortSignal): Promise<CertificationRecord> {
    return request<CertificationRecord>(`/certification/${advisorId}`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  certificationEvents(advisorId: string, signal?: AbortSignal): Promise<CertificationEvent[]> {
    return request<CertificationEvent[]>(`/certification/${advisorId}/events`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // Course / product certifications (GRS-0127) — the caller's own set.
  courseCertifications(signal?: AbortSignal): Promise<CourseCertification[]> {
    return request<CourseCertification[]>("/workbench/certifications/course", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // --- Workbench: learning + drills (GRS-0024) ---
  learningModules(signal?: AbortSignal): Promise<LearningModule[]> {
    return request<LearningModule[]>("/workbench/learning/modules", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  completeLearningModule(
    moduleId: string,
    body?: { score?: number },
    signal?: AbortSignal,
  ): Promise<ContentCompletion> {
    return request<ContentCompletion>(`/workbench/learning/modules/${moduleId}/complete`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body ?? {}),
      signal,
    });
  },

  drillCards(signal?: AbortSignal): Promise<DrillCard[]> {
    return request<DrillCard[]>("/workbench/drills/cards", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  dueDrillCards(signal?: AbortSignal): Promise<DrillCard[]> {
    return request<DrillCard[]>("/workbench/drills/cards/due", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  answerDrillCard(cardId: string, grade: number, signal?: AbortSignal): Promise<DrillCard> {
    return request<DrillCard>(`/workbench/drills/cards/${cardId}/answer`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ grade }),
      signal,
    });
  },

  // --- Bruntsfield Academy courses (GRS-0121) ---
  listCourses(signal?: AbortSignal): Promise<Course[]> {
    return request<Course[]>("/workbench/courses", { method: "GET", headers: authHeaders(), signal });
  },

  getCourse(slug: string, signal?: AbortSignal): Promise<Course> {
    return request<Course>(`/workbench/courses/${slug}`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  createCourse(
    body: { slug: string; title: string; summary: string; certification_credit: CertificationCredit },
    signal?: AbortSignal,
  ): Promise<Course> {
    return request<Course>("/workbench/courses", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
      signal,
    });
  },

  saveCourseDraft(slug: string, tree: CourseTree, signal?: AbortSignal): Promise<Course> {
    return request<Course>(`/workbench/courses/${slug}/draft`, {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify(tree),
      signal,
    });
  },

  approveCourseLesson(slug: string, lessonId: string, signal?: AbortSignal): Promise<Course> {
    return request<Course>(`/workbench/courses/${slug}/lessons/${lessonId}/approve`, {
      method: "POST",
      headers: authHeaders(),
      signal,
    });
  },

  publishCourse(slug: string, signal?: AbortSignal): Promise<CourseVersion> {
    return request<CourseVersion>(`/workbench/courses/${slug}/publish`, {
      method: "POST",
      headers: authHeaders(),
      signal,
    });
  },

  listCourseVersions(slug: string, signal?: AbortSignal): Promise<CourseVersion[]> {
    return request<CourseVersion[]>(`/workbench/courses/${slug}/versions`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // --- Bruntsfield Academy: learner reads (GRS-0135) — org-wide catalog + own progress ---
  listPublishedCourses(signal?: AbortSignal): Promise<CourseVersion[]> {
    return request<CourseVersion[]>("/workbench/courses/published", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  getPublishedCourse(slug: string, signal?: AbortSignal): Promise<CourseVersion> {
    return request<CourseVersion>(`/workbench/courses/${slug}/published`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  listLessonCompletions(slug: string, signal?: AbortSignal): Promise<LessonCompletion[]> {
    return request<LessonCompletion[]>(`/workbench/courses/${slug}/completions`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  completeLesson(slug: string, lessonId: string, signal?: AbortSignal): Promise<LessonCompletion> {
    return request<LessonCompletion>(`/workbench/courses/${slug}/lessons/${lessonId}/complete`, {
      method: "POST",
      headers: authHeaders(),
      signal,
    });
  },

  sectionProgress(slug: string, signal?: AbortSignal): Promise<SectionProgress[]> {
    return request<SectionProgress[]>(`/workbench/courses/${slug}/section-progress`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  /** Sit a section's test. The server marks it — the client sends choices, never a score. */
  attemptSectionTest(
    slug: string,
    moduleId: string,
    answers: number[],
    signal?: AbortSignal,
  ): Promise<SectionTestAttempt> {
    return request<SectionTestAttempt>(`/workbench/courses/${slug}/sections/${moduleId}/test`, {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ answers }),
      signal,
    });
  },

  // --- Workbench: Practice Arena (GRS-0025) ---
  arenaScenarios(signal?: AbortSignal): Promise<ArenaScenario[]> {
    return request<ArenaScenario[]>("/arena/scenarios", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  arenaSessions(signal?: AbortSignal): Promise<ArenaSession[]> {
    return request<ArenaSession[]>("/arena/sessions", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  startArenaSession(scenarioId: string, signal?: AbortSignal): Promise<ArenaSession> {
    return request<ArenaSession>(`/arena/scenarios/${scenarioId}/sessions`, {
      method: "POST",
      headers: authHeaders(),
      signal,
    });
  },

  submitArenaSession(
    sessionId: string,
    transcript: ArenaTurn[],
    signal?: AbortSignal,
  ): Promise<ArenaSession> {
    return request<ArenaSession>(`/arena/sessions/${sessionId}/submit`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ transcript }),
      signal,
    });
  },

  // --- Workbench: calibration (GRS-0022; blind while OPEN, revealed on CLOSE) ---
  calibrationSessions(signal?: AbortSignal): Promise<CalibrationSession[]> {
    return request<CalibrationSession[]>("/calibration/sessions", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  calibrationSession(sessionId: string, signal?: AbortSignal): Promise<CalibrationSession> {
    return request<CalibrationSession>(`/calibration/sessions/${sessionId}`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  submitCalibrationRating(
    sessionId: string,
    entries: RatingEntry[],
    signal?: AbortSignal,
  ): Promise<CalibrationRating> {
    return request<CalibrationRating>(`/calibration/sessions/${sessionId}/ratings`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ entries }),
      signal,
    });
  },

  myCalibrationRating(sessionId: string, signal?: AbortSignal): Promise<CalibrationRating> {
    return request<CalibrationRating>(`/calibration/sessions/${sessionId}/my-rating`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  calibrationResult(sessionId: string, signal?: AbortSignal): Promise<CalibrationResult> {
    return request<CalibrationResult>(`/calibration/sessions/${sessionId}/results`, {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // --- Earnings / commissions (GRS-0028; self-service, principal-scoped by the JWT) ---
  earningsSummary(signal?: AbortSignal): Promise<EarningsSummary> {
    return request<EarningsSummary>("/earnings/summary", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  listCommissions(signal?: AbortSignal): Promise<CommissionLine[]> {
    return request<CommissionLine[]>("/earnings/commissions", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  productCommissions(signal?: AbortSignal): Promise<ProductCommissionCarrot[]> {
    return request<ProductCommissionCarrot[]>("/earnings/product-commissions", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  // The Stream-B rate card (GRS-0187). Not personal data, so every signed-in advisor sees it.
  consultancyCommissions(signal?: AbortSignal): Promise<ConsultancyCommissionCarrot[]> {
    return request<ConsultancyCommissionCarrot[]>("/earnings/consultancy-commissions", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  earningsTimeline(signal?: AbortSignal): Promise<EarningsTimeline> {
    return request<EarningsTimeline>("/earnings/timeline", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  /**
   * The earnings statement is a `.docx` stream, so (like `downloadDeliverable`) we fetch the blob
   * with auth and let the caller trigger the browser save — `request()` is JSON-only.
   */
  async downloadEarningsStatement(signal?: AbortSignal): Promise<{ blob: Blob; filename: string }> {
    const url = `${API_BASE_URL}/earnings/statement`;
    let res: Response;
    try {
      res = await fetch(url, { method: "GET", headers: authHeaders(), signal });
    } catch (cause) {
      throw new ApiError(0, NETWORK_ERROR_MESSAGE, cause, isAbort(cause));
    }
    if (!res.ok) {
      const body = await parseBody(res);
      throw new ApiError(res.status, messageFromBody(body, `Download failed (${res.status})`), body);
    }
    const blob = await res.blob();
    const disposition = res.headers.get("content-disposition") ?? "";
    const match = /filename="?([^"]+)"?/.exec(disposition);
    return { blob, filename: match?.[1] ?? "earnings-statement.docx" };
  },

  /* -------------------------------------------------------- Voice notes (GRS-0249) */

  /**
   * The founder-approved consent line. Fetched, never hardcoded here: there is one copy of this
   * wording in the system and it lives in the contracts package. A recorder that showed its own
   * text and uploaded anyway would be refused by the API, which is the point of fetching it.
   */
  consentLine(signal?: AbortSignal): Promise<ConsentLine> {
    return request<ConsentLine>("/transcripts/consent-line", {
      method: "GET",
      headers: authHeaders(),
      signal,
    });
  },

  /**
   * Upload a recording and get back the transcript.
   *
   * `media_base64` rather than multipart, matching the existing ingest. The caller must keep the
   * original blob until this resolves — a rejected upload stores nothing at all, and the recording
   * of a conversation that already happened is the one thing here that cannot be made again.
   */
  uploadRecording(payload: UploadRecordingRequest, signal?: AbortSignal): Promise<MeetingTranscript> {
    return request<MeetingTranscript>("/transcripts/media", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload),
      signal,
    });
  },
};
