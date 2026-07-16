import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { WelcomeBanner } from "@/components/WelcomeBanner";
import { getSession, type Session } from "@/lib/session";

vi.mock("@/lib/session", () => ({ getSession: vi.fn() }));
const mockedGetSession = getSession as unknown as ReturnType<typeof vi.fn>;

const SESSION: Session = {
  consultantId: "u1",
  email: "john.gallagher@bruntsfieldcapital.com",
  role: "consultant",
  assessorLevel: "trained",
  isAdmin: false,
  isCommittee: false,
  isCertifiedLead: false,
};

describe("WelcomeBanner (GRS-0089)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("personalises the greeting from the session email", async () => {
    mockedGetSession.mockReturnValue(SESSION);
    render(<WelcomeBanner />);
    // "Good {morning|afternoon|evening}, John" — the ", John" suffix is stable across the day.
    expect(await screen.findByText(/,\s*John$/)).toBeTruthy();
  });

  it("orients the advisor with first-assessment / portfolio / pipeline links", async () => {
    mockedGetSession.mockReturnValue(SESSION);
    render(<WelcomeBanner />);
    expect(await screen.findByRole("link", { name: /first assessment/i })).toBeTruthy();
    expect(screen.getByRole("link", { name: /portfolio/i })).toBeTruthy();
    expect(screen.getByRole("link", { name: /pipeline/i })).toBeTruthy();
  });

  it("still renders the studio title when signed out (no personalisation available)", () => {
    mockedGetSession.mockReturnValue(null);
    render(<WelcomeBanner />);
    expect(screen.getByRole("heading", { name: /Advisor Studio/i })).toBeTruthy();
  });
});
