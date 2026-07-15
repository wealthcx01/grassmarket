import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardSessionFooter } from "@/components/DashboardSessionFooter";
import { getToken } from "@/lib/api";

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace: vi.fn(), push: vi.fn() }) }));
vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return { ...actual, getToken: vi.fn(), clearToken: vi.fn() };
});

const mockedGetToken = getToken as unknown as ReturnType<typeof vi.fn>;

describe("DashboardSessionFooter (GRS-0040)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows the sign-in link when signed out", async () => {
    mockedGetToken.mockReturnValue(null);
    render(<DashboardSessionFooter />);
    expect(await screen.findByRole("link", { name: /go to sign in/i })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /sign out/i })).toBeNull();
  });

  it("shows a sign-out control when signed in — never 'not signed in'", async () => {
    mockedGetToken.mockReturnValue("a-token");
    render(<DashboardSessionFooter />);
    expect(await screen.findByRole("button", { name: /sign out/i })).toBeTruthy();
    expect(screen.queryByText(/not signed in/i)).toBeNull();
  });
});
