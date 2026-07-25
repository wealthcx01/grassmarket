/**
 * GRS-0186: the primary nav renders the section links with correct hrefs and an active state, and
 * on mobile the hamburger toggles a drawer that Escape closes.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const pathname = { value: "/pipeline" };
vi.mock("next/navigation", () => ({ usePathname: () => pathname.value }));

import { PrimaryNav } from "@/components/PrimaryNav";

function setViewport(maxWidthMatches: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: maxWidthMatches,
    media: query,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
    onchange: null,
  }));
}

describe("PrimaryNav (GRS-0186)", () => {
  beforeEach(() => {
    pathname.value = "/pipeline";
  });
  afterEach(() => vi.clearAllMocks());

  it("renders all section links with their hrefs on a wide viewport", () => {
    setViewport(false);
    render(<PrimaryNav />);
    const expected: [string, string][] = [
      ["Pipeline", "/pipeline"],
      ["Portfolio", "/assessments"],
      ["Engagements", "/engagements"],
      ["Deliverables", "/deliverables"],
      ["Workbench", "/workbench"],
      ["Earnings", "/earnings"],
    ];
    for (const [label, href] of expected) {
      expect(screen.getByRole("link", { name: label }).getAttribute("href")).toBe(href);
    }
  });

  it("marks the active section with aria-current", () => {
    pathname.value = "/assessments/abc"; // a sub-path of Portfolio
    setViewport(false);
    render(<PrimaryNav />);
    expect(screen.getByRole("link", { name: "Portfolio" }).getAttribute("aria-current")).toBe("page");
    expect(screen.getByRole("link", { name: "Pipeline" }).getAttribute("aria-current")).toBeNull();
  });

  it("toggles the mobile drawer and closes it on Escape", () => {
    setViewport(true);
    render(<PrimaryNav />);
    const button = screen.getByRole("button", { name: /open navigation/i });
    expect(button.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(button);
    expect(button.getAttribute("aria-expanded")).toBe("true");
    // The drawer's links are now present.
    expect(screen.getByRole("link", { name: "Deliverables" })).toBeTruthy();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(button.getAttribute("aria-expanded")).toBe("false");
  });
});
