import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ActingAsBanner } from "@/components/ActingAsBanner";
import { api } from "@/lib/api";
import { getSession } from "@/lib/session";

vi.mock("@/lib/session", () => ({ getSession: vi.fn() }));
vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return {
    ...actual,
    api: { ...actual.api, me: vi.fn(), stopActingAs: vi.fn() },
    getRefreshToken: vi.fn(() => "r"),
    setTokens: vi.fn(),
  };
});

const mockedSession = getSession as unknown as ReturnType<typeof vi.fn>;
const mocked = api as unknown as {
  me: ReturnType<typeof vi.fn>;
  stopActingAs: ReturnType<typeof vi.fn>;
};

/**
 * GRS-0208 scope 2. The ticket's word is act-as, *not* impersonate-silently, and this banner is
 * most of the difference. The tests below are all versions of one question: can this state be
 * invisible?
 */
describe("ActingAsBanner (GRS-0208)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders nothing when the session is not acting as anyone", async () => {
    mockedSession.mockReturnValue({ consultantId: "c1", actingAsConsultantId: null });
    render(<ActingAsBanner />);
    await waitFor(() => expect(screen.queryByTestId("acting-as-banner")).toBeNull());
    // And it does not ask the server either — a banner that is off should cost nothing.
    expect(mocked.me).not.toHaveBeenCalled();
  });

  it("names the advisor being viewed", async () => {
    mockedSession.mockReturnValue({ consultantId: "admin", actingAsConsultantId: "a1" });
    mocked.me.mockResolvedValue({
      id: "a1",
      full_name: "Alice Advisor",
      email: "alice@bruntsfieldcapital.com",
    });
    render(<ActingAsBanner />);
    const banner = await screen.findByTestId("acting-as-banner");
    // "Acting as another user" tells an admin nothing they can act on.
    expect(banner.textContent).toContain("Alice Advisor");
    expect(banner.textContent).toContain("alice@bruntsfieldcapital.com");
  });

  it("warns that the work is recorded against both accounts", async () => {
    mockedSession.mockReturnValue({ consultantId: "admin", actingAsConsultantId: "a1" });
    mocked.me.mockResolvedValue({ id: "a1", full_name: "Alice Advisor", email: "a@b.c" });
    render(<ActingAsBanner />);
    const banner = await screen.findByTestId("acting-as-banner");
    expect(banner.textContent).toMatch(/recorded against/i);
  });

  it("still shows the banner when the name cannot be fetched", async () => {
    // The dangerous state is the invisible one. A failed lookup must degrade to a banner without a
    // name, never to no banner — that would be the exact silent impersonation the ticket forbids.
    mockedSession.mockReturnValue({ consultantId: "admin", actingAsConsultantId: "a1" });
    mocked.me.mockRejectedValue(new Error("network"));
    render(<ActingAsBanner />);
    const banner = await screen.findByTestId("acting-as-banner");
    expect(banner.textContent).toContain("another advisor");
  });

  it("offers one click back", async () => {
    mockedSession.mockReturnValue({ consultantId: "admin", actingAsConsultantId: "a1" });
    mocked.me.mockResolvedValue({ id: "a1", full_name: "Alice Advisor", email: "a@b.c" });
    render(<ActingAsBanner />);
    // A state you cannot leave easily is a state people stay in.
    expect(await screen.findByRole("button", { name: /stop viewing as them/i })).toBeTruthy();
  });
});
