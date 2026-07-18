/**
 * Entity subject lookup (GRS-0100, ADR-0033): typing proposes companies, picking one resolves to a
 * canonical entity_id and shows the dedup count, and typing again detaches the link (manual).
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EntitySubjectField } from "@/components/EntitySubjectField";
import { api } from "@/lib/api";
import type { CompanyEntity } from "@/lib/types";

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return {
    ...actual,
    api: { ...actual.api, searchEntities: vi.fn(), assessmentsForEntity: vi.fn() },
  };
});

const mocked = api as unknown as {
  searchEntities: ReturnType<typeof vi.fn>;
  assessmentsForEntity: ReturnType<typeof vi.fn>;
};

const revolut: CompanyEntity = {
  entity_id: "revolut",
  name: "Revolut",
  aliases: ["Revolut Ltd"],
  domain: "revolut.com",
  segment: "Neobank",
};

beforeEach(() => {
  vi.clearAllMocks();
  mocked.searchEntities.mockResolvedValue([revolut]);
  mocked.assessmentsForEntity.mockResolvedValue([{ id: "a1" }, { id: "a2" }]);
});

describe("EntitySubjectField (GRS-0100)", () => {
  it("proposes companies, resolves on pick, and shows the dedup count", async () => {
    const onChange = vi.fn();
    render(<EntitySubjectField value="Rev" entityId={null} onChange={onChange} />);

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Revolut" } });
    // The typing reports a manual (unlinked) subject immediately.
    expect(onChange).toHaveBeenLastCalledWith("Revolut", null);
    // The debounced search surfaces the candidate.
    const option = await screen.findByRole("button", { name: /Revolut/ });
    fireEvent.click(option);
    // Picking resolves to the canonical entity id.
    expect(onChange).toHaveBeenLastCalledWith("Revolut", "revolut");
  });

  it("shows the linked chip + dedup count once linked, then detaches on re-typing", async () => {
    const onChange = vi.fn();
    const { rerender } = render(<EntitySubjectField value="Rev" entityId={null} onChange={onChange} />);
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Revolut" } });
    fireEvent.click(await screen.findByRole("button", { name: /Revolut/ }));
    // Reflect the resolved state the parent would pass back.
    rerender(<EntitySubjectField value="Revolut" entityId="revolut" onChange={onChange} />);
    await waitFor(() => expect(screen.getByText(/Linked to/)).toBeTruthy());
    expect(screen.getByText(/2 assessments of this company/)).toBeTruthy();

    // Typing again detaches the link — the subject becomes manual.
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Revolut X" } });
    expect(onChange).toHaveBeenLastCalledWith("Revolut X", null);
  });
});
