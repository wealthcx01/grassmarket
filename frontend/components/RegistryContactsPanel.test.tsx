/**
 * GRS-0193: the registry contacts panel on a prospect record. It renders role, verification flag
 * and source provenance, and it distinguishes "this institution is not imported" from "this
 * institution has no contacts" — the two say different things and must not collapse into one
 * empty state.
 */

import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";
import type { CompanyEntity, RegistryContact } from "@/lib/types";

const searchEntities = vi.fn();
const listRegistryContacts = vi.fn();

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    api: { searchEntities: (...a: unknown[]) => searchEntities(...a), listRegistryContacts: (...a: unknown[]) => listRegistryContacts(...a) },
  };
});

import { RegistryContactsPanel } from "@/components/RegistryContactsPanel";

const ENTITY: CompanyEntity = {
  entity_id: "lseg-barclays",
  name: "Barclays",
  aliases: [],
  domain: "barclays.com",
  segment: "Sell-side research",
};

function contact(over: Partial<RegistryContact> = {}): RegistryContact {
  return {
    contact_id: "lseg-barclays:jo",
    target_id: "lseg-barclays",
    full_name: "Jo Analyst",
    email: "jo@barclays.example",
    phone: null,
    job_role: "Equity Analyst",
    linkedin: null,
    verified: false,
    source: "lseg-roster",
    imported_on: "2026-07-25",
    ...over,
  };
}

describe("RegistryContactsPanel (GRS-0193)", () => {
  beforeEach(() => {
    searchEntities.mockReset();
    listRegistryContacts.mockReset();
  });

  it("renders each contact with role, verification flag and provenance", async () => {
    searchEntities.mockResolvedValue([ENTITY]);
    listRegistryContacts.mockResolvedValue([
      contact({ verified: true, full_name: "Verified Owner", job_role: "Global Head of Research" }),
      contact({ contact_id: "lseg-barclays:jo2", full_name: "Jo Analyst" }),
    ]);
    render(<RegistryContactsPanel companyName="Barclays" />);

    await waitFor(() => expect(screen.getByText("Verified Owner")).toBeTruthy());
    expect(screen.getByText("Global Head of Research")).toBeTruthy();
    expect(screen.getByText("Verified")).toBeTruthy();
    expect(screen.getByText("Unverified")).toBeTruthy();
    expect(screen.getAllByText(/lseg-roster · imported 2026-07-25/).length).toBe(2);
  });

  it("says the institution is not imported rather than showing an empty list", async () => {
    searchEntities.mockResolvedValue([]);
    render(<RegistryContactsPanel companyName="Nowhere Ltd" />);
    await waitFor(() => expect(screen.getByText(/not in the imported registry/)).toBeTruthy());
    expect(screen.getByText(/does not mean the institution has no contacts/)).toBeTruthy();
    expect(listRegistryContacts).not.toHaveBeenCalled();
  });

  it("never attaches another firm's people on a near-miss match", async () => {
    // "Barclays Investment Bank" ranked first for "Barclays Bank" is NOT this institution.
    searchEntities.mockResolvedValue([{ ...ENTITY, name: "Barclays Investment Bank" }]);
    render(<RegistryContactsPanel companyName="Barclays Bank" />);
    await waitFor(() => expect(screen.getByText(/not in the imported registry/)).toBeTruthy());
    expect(listRegistryContacts).not.toHaveBeenCalled();
  });

  it("distinguishes an imported institution with no contacts yet", async () => {
    searchEntities.mockResolvedValue([ENTITY]);
    listRegistryContacts.mockResolvedValue([]);
    render(<RegistryContactsPanel companyName="Barclays" />);
    await waitFor(() =>
      expect(screen.getByText(/no contacts have been imported for it yet/)).toBeTruthy(),
    );
  });

  it("surfaces a real failure rather than rendering as empty", async () => {
    searchEntities.mockRejectedValue(new ApiError(500, "Backend fell over", null));
    render(<RegistryContactsPanel companyName="Barclays" />);
    await waitFor(() => expect(screen.getByText("Backend fell over")).toBeTruthy());
  });

  it("labels the panel as shared rather than the advisor's own data", async () => {
    searchEntities.mockResolvedValue([]);
    render(<RegistryContactsPanel companyName="Nowhere Ltd" />);
    expect(screen.getByText(/Shared across the network, not your own pipeline/)).toBeTruthy();
    await waitFor(() => expect(screen.getByText(/not in the imported registry/)).toBeTruthy());
  });
});
