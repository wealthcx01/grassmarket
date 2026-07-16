/**
 * Client-side view of the access token (GRS-0027). The server is the only security boundary — every
 * query is JWT-scoped and role-checked server-side. This decode is used ONLY to mirror those claims
 * in the UI (show the committee tab to committee members, gate a Certified-Lead action), so the
 * screen matches what the API will allow. It never grants access; a forged token still hits a 403.
 */

import { getToken } from "@/lib/api";

export type Role = "consultant" | "committee_member" | "admin";
export type AssessorLevel = "trained" | "shadow" | "observed_lead" | "certified_lead";

export interface Session {
  consultantId: string;
  email: string;
  role: Role;
  assessorLevel: AssessorLevel;
  isAdmin: boolean;
  isCommittee: boolean;
  isCertifiedLead: boolean;
}

function decodePayload(token: string): Record<string, unknown> | null {
  const parts = token.split(".");
  const payload = parts[1];
  if (parts.length !== 3 || !payload) return null;
  try {
    // JWT uses base64url; normalise to base64 before decoding.
    const b64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(b64);
    return JSON.parse(json) as Record<string, unknown>;
  } catch {
    return null;
  }
}

/** True when the token's `exp` (seconds) is in the past. A malformed/absent exp is treated as
 *  expired — a token we cannot vouch for is not a live session (GRS-0120). */
function isExpired(claims: Record<string, unknown>): boolean {
  const exp = claims.exp;
  if (typeof exp !== "number") return true;
  return exp * 1000 <= Date.now();
}

/** The current session from the stored token, or null when signed out / token malformed / EXPIRED.
 *  Treating an expired token as signed-out stops the chrome from showing signed-in while every API
 *  call 401s (GRS-0120) — the confusing symptom advisers reported. */
export function getSession(): Session | null {
  const token = getToken();
  if (!token) return null;
  const claims = decodePayload(token);
  if (!claims) return null;
  if (isExpired(claims)) return null;

  const role = claims.role as Role | undefined;
  const level = claims.assessor_level as AssessorLevel | undefined;
  const sub = claims.sub as string | undefined;
  if (!role || !level || !sub) return null;

  return {
    consultantId: sub,
    email: (claims.email as string) ?? "",
    role,
    assessorLevel: level,
    isAdmin: role === "admin",
    isCommittee: role === "committee_member" || role === "admin",
    isCertifiedLead: level === "certified_lead",
  };
}
