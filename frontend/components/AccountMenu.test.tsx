import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AccountMenu } from "@/components/AccountMenu";
import { clearToken } from "@/lib/api";
import { getSession, type Session } from "@/lib/session";

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace: vi.fn(), push: vi.fn() }) }));
vi.mock("@/lib/session", () => ({ getSession: vi.fn() }));
vi.mock("@/lib/api", () => ({ clearToken: vi.fn() }));

const mockedGetSession = getSession as unknown as ReturnType<typeof vi.fn>;

const SESSION: Session = {
  consultantId: "u1",
  email: "alice@bruntsfieldcapital.com",
  role: "consultant",
  assessorLevel: "trained",
  isAdmin: false,
  isCommittee: false,
  isCertifiedLead: false,
};

describe("AccountMenu (GRS-0087)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows a sign-in link when signed out", async () => {
    mockedGetSession.mockReturnValue(null);
    render(<AccountMenu />);
    expect(await screen.findByRole("link", { name: /sign in/i })).toBeTruthy();
  });

  it("shows the identity and an account menu with Profile / Settings / public site / Log out", async () => {
    mockedGetSession.mockReturnValue(SESSION);
    render(<AccountMenu />);
    const trigger = await screen.findByRole("button", { name: /account menu/i });
    expect(trigger.textContent).toContain(SESSION.email);
    fireEvent.click(trigger);
    expect(screen.getByRole("menuitem", { name: /profile/i })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /settings/i })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /bruntsfield\.capital/i })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /log out/i })).toBeTruthy();
  });

  it("logs out from the menu — clears the session (the old footer behaviour)", async () => {
    mockedGetSession.mockReturnValue(SESSION);
    render(<AccountMenu />);
    fireEvent.click(await screen.findByRole("button", { name: /account menu/i }));
    fireEvent.click(screen.getByRole("menuitem", { name: /log out/i }));
    expect(clearToken).toHaveBeenCalledOnce();
  });
});
