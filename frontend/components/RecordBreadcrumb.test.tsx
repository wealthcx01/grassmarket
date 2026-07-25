/**
 * GRS-0186: the record breadcrumb links to the client's prospect record (Pipeline › Company › this),
 * so the full record is one click from any surface that names the client.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RecordBreadcrumb } from "@/components/RecordBreadcrumb";

describe("RecordBreadcrumb (GRS-0186)", () => {
  it("links Pipeline and the company (to the prospect record), and shows the current record", () => {
    render(<RecordBreadcrumb prospectId="p1" companyName="Meridian Securities" current="Q3 engagement" />);
    expect(screen.getByRole("link", { name: "Pipeline" }).getAttribute("href")).toBe("/pipeline");
    const company = screen.getByRole("link", { name: "Meridian Securities" });
    expect(company.getAttribute("href")).toBe("/prospects/p1");
    expect(screen.getByText("Q3 engagement")).toBeTruthy();
  });
});
