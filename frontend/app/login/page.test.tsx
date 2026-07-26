/**
 * GRS-0173: Workspace Google sign-in is the primary path. The Google action renders as the primary
 * button with the Bruntsfield label and links to the backend's OAuth start; the email/password form
 * is still present below the separator for non-Bruntsfield accounts.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace: vi.fn(), push: vi.fn() }) }));

import LoginPage from "@/app/login/page";

describe("LoginPage (GRS-0173)", () => {
  it("shows the Bruntsfield Google action as the primary sign-in", () => {
    render(<LoginPage />);
    const google = screen.getByRole("link", { name: /sign in with bruntsfield google/i });
    expect(google.className).toContain("btn-primary");
    expect(google.getAttribute("href")).toContain("/auth/google/start");
  });

  it("keeps the email and password form for non-Bruntsfield accounts", () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/email/i)).toBeTruthy();
    expect(screen.getByLabelText(/password/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /sign in with email/i })).toBeTruthy();
    expect(screen.getByText(/not on a bruntsfield account/i)).toBeTruthy();
  });
});
