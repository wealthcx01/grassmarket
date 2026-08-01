import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ActAsPicker } from "@/components/ActAsPicker";
import { api } from "@/lib/api";

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return {
    ...actual,
    api: { ...actual.api, actAsCandidates: vi.fn(), startActingAs: vi.fn() },
    getRefreshToken: vi.fn(() => "r"),
    setTokens: vi.fn(),
  };
});

const mocked = api as unknown as {
  actAsCandidates: ReturnType<typeof vi.fn>;
  startActingAs: ReturnType<typeof vi.fn>;
};

const ALICE = {
  id: "a1",
  email: "alice@bruntsfieldcapital.com",
  full_name: "Alice Advisor",
  role: "consultant" as const,
  tier: "advisor" as const,
  is_active: true,
};

describe("ActAsPicker (GRS-0208)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("lists the advisors an admin can view as", async () => {
    mocked.actAsCandidates.mockResolvedValue([ALICE]);
    render(<ActAsPicker onClose={() => {}} />);
    expect(await screen.findByText("Alice Advisor")).toBeTruthy();
    expect(screen.getByText("alice@bruntsfieldcapital.com")).toBeTruthy();
  });

  it("says the session is recorded against both accounts before it starts", async () => {
    // An admin who does not know this will eventually write something as an advisor and be
    // surprised later. The banner says it again once the session begins; saying it twice is cheap
    // and the surprise is not.
    mocked.actAsCandidates.mockResolvedValue([ALICE]);
    const { container } = render(<ActAsPicker onClose={() => {}} />);
    expect(container.textContent).toMatch(/recorded against their account/i);
    expect(container.textContent).toMatch(/and yours/i);
  });

  it("starts a session for the advisor that was clicked", async () => {
    mocked.actAsCandidates.mockResolvedValue([ALICE]);
    mocked.startActingAs.mockResolvedValue({ access_token: "t" });
    render(<ActAsPicker onClose={() => {}} />);
    fireEvent.click(await screen.findByText("Alice Advisor"));
    await waitFor(() => expect(mocked.startActingAs).toHaveBeenCalledWith("a1"));
  });

  it("surfaces a refusal rather than failing silently", async () => {
    mocked.actAsCandidates.mockRejectedValue(new Error("nope"));
    render(<ActAsPicker onClose={() => {}} />);
    expect(await screen.findByRole("alert")).toBeTruthy();
  });

  it("says so when there is nobody to view as", async () => {
    // An empty list is a real state on a one-person instance, and an empty dialog reads as broken.
    mocked.actAsCandidates.mockResolvedValue([]);
    render(<ActAsPicker onClose={() => {}} />);
    expect(await screen.findByText(/no one else to view as/i)).toBeTruthy();
  });
});
