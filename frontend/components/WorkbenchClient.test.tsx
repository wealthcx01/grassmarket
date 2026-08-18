import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { WorkbenchClient } from "@/components/workbench/WorkbenchClient";
import { getSession, type Session } from "@/lib/session";

vi.mock("@/lib/session", () => ({ getSession: vi.fn() }));

// The bench dashboard mounts on the default tab; stub its calls so the role-gating assertions run
// without touching the network.
vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  const queue = { owner_consultant_id: "c1", generated_at: "2026-07-14T00:00:00+00:00", items: [] };
  const perf = {
    owner_consultant_id: "c1",
    level: "trained",
    engagements_active: 0,
    engagements_completed: 0,
    prospects_total: 0,
    pipeline_conversion_rate: 0,
    coursework_complete: false,
    exam_passed: false,
    drills_due: 0,
    drill_best_streak: 0,
    arena_sessions_scored: 0,
    arena_best_completeness: null,
    arena_trend: [],
  };
  return {
    ...actual,
    api: {
      ...actual.api,
      benchQueue: vi.fn().mockResolvedValue(queue),
      performance: vi.fn().mockResolvedValue(perf),
      // The Founder review tab is mounted by ASKING the server, so the gate under test here is
      // whether this call succeeds — not a claim read from the token.
      founderReviewQueue: vi.fn().mockRejectedValue(new Error("403")),
    },
  };
});

const mockedSession = getSession as unknown as ReturnType<typeof vi.fn>;

function session(over: Partial<Session> = {}): Session {
  return {
    consultantId: "c1",
    email: "advisor@bruntsfieldcapital.com",
    role: "consultant",
    assessorLevel: "trained",
    isAdmin: false,
    actingAsConsultantId: null,
    isCommittee: false,
    isCertifiedLead: false,
    ...over,
  };
}

describe("WorkbenchClient — tabs and gating (GRS-0027, ADR-0041)", () => {
  // clearAllMocks resets calls but NOT implementations, so a resolved queue set by one test would
  // leak into the next and quietly hand it a founder tab. Re-arm the refusal each time.
  beforeEach(async () => {
    vi.clearAllMocks();
    const { api } = await import("@/lib/api");
    (api.founderReviewQueue as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("403"),
    );
  });

  it("shows an ordinary consultant four tabs and no founder review", async () => {
    mockedSession.mockReturnValue(session());
    render(<WorkbenchClient />);
    expect(await screen.findByRole("tab", { name: "Bench" })).toBeTruthy();
    expect(screen.getAllByRole("tab").map((t) => t.textContent)).toEqual([
      "Bench",
      "Certification",
      "Academy",
      "Practice Arena",
    ]);
    expect(screen.queryByRole("tab", { name: "Founder review" })).toBeNull();
  });

  it("mounts Founder review when the server answers the queue", async () => {
    mockedSession.mockReturnValue(session({ email: "john@bruntsfield.capital" }));
    const { api } = await import("@/lib/api");
    (api.founderReviewQueue as unknown as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    render(<WorkbenchClient />);
    expect(await screen.findByRole("tab", { name: "Founder review" })).toBeTruthy();
  });

  it("does not mount Founder review for an admin who is not the reviewer", async () => {
    mockedSession.mockReturnValue(session({ role: "admin", isAdmin: true }));
    render(<WorkbenchClient />);
    expect(await screen.findByRole("tab", { name: "Bench" })).toBeTruthy();
    expect(screen.queryByRole("tab", { name: "Founder review" })).toBeNull();
  });

  it("carries no retired governance tab", async () => {
    mockedSession.mockReturnValue(session({ role: "admin", isAdmin: true, isCommittee: true }));
    render(<WorkbenchClient />);
    await screen.findByRole("tab", { name: "Bench" });
    for (const gone of ["Committee", "Calibration", "Rating requests"]) {
      expect(screen.queryByRole("tab", { name: gone })).toBeNull();
    }
  });

  it("prompts sign-in when there is no session", () => {
    mockedSession.mockReturnValue(null);
    render(<WorkbenchClient />);
    expect(screen.getByText(/sign in/i)).toBeTruthy();
    expect(screen.queryByRole("tablist")).toBeNull();
  });
});
