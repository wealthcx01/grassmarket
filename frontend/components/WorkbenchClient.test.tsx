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
    isCommittee: false,
    isCertifiedLead: false,
    ...over,
  };
}

describe("WorkbenchClient — role gating (GRS-0027)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("hides the Committee tab from an ordinary consultant", async () => {
    mockedSession.mockReturnValue(session());
    render(<WorkbenchClient />);
    expect(await screen.findByRole("tab", { name: "Bench" })).toBeTruthy();
    expect(screen.queryByRole("tab", { name: "Committee" })).toBeNull();
  });

  it("shows the Committee tab to a committee member", async () => {
    mockedSession.mockReturnValue(session({ role: "committee_member", isCommittee: true }));
    render(<WorkbenchClient />);
    expect(await screen.findByRole("tab", { name: "Committee" })).toBeTruthy();
  });

  it("shows the Committee tab to an admin", async () => {
    mockedSession.mockReturnValue(session({ role: "admin", isAdmin: true, isCommittee: true }));
    render(<WorkbenchClient />);
    expect(await screen.findByRole("tab", { name: "Committee" })).toBeTruthy();
  });

  it("prompts sign-in when there is no session", () => {
    mockedSession.mockReturnValue(null);
    render(<WorkbenchClient />);
    expect(screen.getByText(/sign in/i)).toBeTruthy();
    expect(screen.queryByRole("tablist")).toBeNull();
  });
});
