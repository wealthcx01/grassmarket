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
  Assessment,
  AssessmentDocument,
  CommsChannel,
  CommsLogEntry,
  DeliverableSlot,
  Engagement,
  LiveScore,
  PipelineBoard,
  PipelineForecast,
  PipelineStage,
  Prospect,
  RecoveryFeeAttribution,
  Registry,
  RubricAnchor,
  ScenarioComparison,
  Workshop,
} from "@/lib/types";

export const API_BASE_URL: string =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:8000";

/** Where the (skeleton) access token lives — mirrors the login page (Loop 6 replaces this). */
export const TOKEN_KEY = "bas.access_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function clearToken(): void {
  if (typeof window !== "undefined") window.localStorage.removeItem(TOKEN_KEY);
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
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
  token_type: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
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
    throw new ApiError(0, `Cannot reach API at ${API_BASE_URL}`, cause);
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

  // --- Assessments (all JWT-scoped server-side; the client carries the token) ---
  registry(signal?: AbortSignal): Promise<Registry> {
    return request<Registry>("/registry", { method: "GET", headers: authHeaders(), signal });
  },

  createAssessment(subject: string, signal?: AbortSignal): Promise<Assessment> {
    return request<Assessment>("/assessments", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ subject }),
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

  createProspect(company_name: string, signal?: AbortSignal): Promise<Prospect> {
    return request<Prospect>("/prospects", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ company_name }),
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
};
