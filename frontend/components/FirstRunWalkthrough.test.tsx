/**
 * GRS-0065: the first-run walkthrough shows once for a signed-in advisor, persists that it was seen,
 * and steps through to a clear start action.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FirstRunWalkthrough } from "@/components/FirstRunWalkthrough";
import { getToken } from "@/lib/api";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, replace: vi.fn() }) }));
vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return { ...actual, getToken: vi.fn() };
});
const mockedToken = getToken as unknown as ReturnType<typeof vi.fn>;

describe("FirstRunWalkthrough (GRS-0065)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockedToken.mockReturnValue("a-token");
  });

  it("shows on a signed-in advisor's first visit", () => {
    render(<FirstRunWalkthrough />);
    expect(screen.getByRole("dialog")).toBeTruthy();
    expect(screen.getByText("Welcome to the Advisor Studio")).toBeTruthy();
  });

  it("does not show when already seen", () => {
    localStorage.setItem("bas.onboarding_seen", "1");
    render(<FirstRunWalkthrough />);
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("does not show when signed out", () => {
    mockedToken.mockReturnValue(null);
    render(<FirstRunWalkthrough />);
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("Skip dismisses and records it as seen", () => {
    render(<FirstRunWalkthrough />);
    fireEvent.click(screen.getByRole("button", { name: /Skip/ }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(localStorage.getItem("bas.onboarding_seen")).toBe("1");
  });

  it("steps through to a start action that navigates and dismisses", () => {
    render(<FirstRunWalkthrough />);
    // 4 slides → click Next three times to reach the last.
    fireEvent.click(screen.getByRole("button", { name: /^Next/ }));
    fireEvent.click(screen.getByRole("button", { name: /^Next/ }));
    fireEvent.click(screen.getByRole("button", { name: /^Next/ }));
    const go = screen.getByRole("button", { name: /Go to my pipeline/ });
    fireEvent.click(go);
    expect(push).toHaveBeenCalledWith("/pipeline");
    expect(localStorage.getItem("bas.onboarding_seen")).toBe("1");
  });
});
