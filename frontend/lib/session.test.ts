import { beforeEach, describe, expect, it } from "vitest";

import { TOKEN_KEY } from "@/lib/api";
import { getSession } from "@/lib/session";

function b64url(obj: unknown): string {
  return btoa(JSON.stringify(obj)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function makeToken(claims: Record<string, unknown>): string {
  return `${b64url({ alg: "HS256", typ: "JWT" })}.${b64url(claims)}.signature`;
}

const BASE = { sub: "u1", email: "a@b.com", role: "consultant", assessor_level: "trained" };

describe("getSession expiry handling (GRS-0120)", () => {
  beforeEach(() => window.localStorage.clear());

  it("returns a session for a valid, unexpired token", () => {
    const exp = Math.floor(Date.now() / 1000) + 3600;
    window.localStorage.setItem(TOKEN_KEY, makeToken({ ...BASE, exp }));
    const session = getSession();
    expect(session?.email).toBe("a@b.com");
    expect(session?.consultantId).toBe("u1");
  });

  it("returns null for an EXPIRED token — the UI no longer shows signed-in while calls 401", () => {
    const exp = Math.floor(Date.now() / 1000) - 10;
    window.localStorage.setItem(TOKEN_KEY, makeToken({ ...BASE, exp }));
    expect(getSession()).toBeNull();
  });

  it("treats a token with no exp claim as expired (cannot vouch for it)", () => {
    window.localStorage.setItem(TOKEN_KEY, makeToken(BASE));
    expect(getSession()).toBeNull();
  });

  it("returns null when there is no token", () => {
    expect(getSession()).toBeNull();
  });
});
