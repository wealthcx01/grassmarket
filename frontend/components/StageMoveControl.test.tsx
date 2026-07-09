import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { StageMoveControl } from "@/components/StageMoveControl";
import { ApiError } from "@/lib/api";

describe("StageMoveControl — the backend owns legality", () => {
  it("reverts the card and shows the reason on an illegal-move 409", async () => {
    const reason = "Illegal pipeline transition prospect → contracted.";
    const onMove = vi.fn().mockRejectedValue(new ApiError(409, reason, null));
    render(<StageMoveControl prospectId="p1" currentStage="prospect" onMove={onMove} />);

    const select = screen.getByTestId("stage-select") as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "contracted" } });

    // The reason is surfaced...
    await waitFor(() => expect(screen.getByTestId("move-error").textContent).toBe(reason));
    // ...and the card REVERTED to its previous stage — not a silent success.
    expect(select.value).toBe("prospect");
    expect(onMove).toHaveBeenCalledWith("p1", "contracted");
  });

  it("keeps the new stage on a successful move", async () => {
    const onMove = vi.fn().mockResolvedValue({});
    render(<StageMoveControl prospectId="p1" currentStage="prospect" onMove={onMove} />);

    const select = screen.getByTestId("stage-select") as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "workshop_scheduled" } });

    await waitFor(() => expect(onMove).toHaveBeenCalledWith("p1", "workshop_scheduled"));
    expect(select.value).toBe("workshop_scheduled");
    expect(screen.queryByTestId("move-error")).toBeNull();
  });
});
