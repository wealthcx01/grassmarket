/**
 * The band-rendering honesty test (GRS-0010, ADR-0008 / §7).
 *
 * The guarantee that must NOT be lost at the view layer: a band with `modelled = false` renders as a
 * labelled POINT ("uncertainty not modelled"), never as a tight range. This proves it at the DOM.
 */

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { BandDisplay } from "@/components/BandDisplay";
import { NOT_MODELLED_LABEL } from "@/lib/band";

afterEach(cleanup);

describe("BandDisplay honesty (ADR-0008)", () => {
  it("renders an UNMODELLED band as a labelled point, never a range", () => {
    render(<BandDisplay label="B" band={{ p10: 0.5, p50: 0.5, p90: 0.5, modelled: false }} />);
    expect(screen.getByTestId("band-point")).toBeDefined();
    expect(screen.queryByTestId("band-range")).toBeNull();
    expect(screen.getByText(NOT_MODELLED_LABEL)).toBeDefined();
  });

  it("renders a MODELLED band as a range", () => {
    render(<BandDisplay label="V" band={{ p10: 0.4, p50: 0.5, p90: 0.6, modelled: true }} />);
    expect(screen.getByTestId("band-range")).toBeDefined();
    expect(screen.queryByTestId("band-point")).toBeNull();
    expect(screen.queryByText(NOT_MODELLED_LABEL)).toBeNull();
  });

  it("renders nothing meaningful for a missing band", () => {
    render(<BandDisplay label="P" band={null} />);
    expect(screen.queryByTestId("band-point")).toBeNull();
    expect(screen.queryByTestId("band-range")).toBeNull();
  });
});

describe("BandDisplay one-number rule (ADR-0040)", () => {
  it("bolds the deterministic point — never the band's P50 — with the clamped modelled range", () => {
    // MC median 58.9, deterministic 60.5 (the staging-persona scenario): the headline must be
    // 60.5, the range must stretch to include it, and no "P50" claim may remain.
    render(
      <BandDisplay
        label="V"
        band={{ p10: 0.54, p50: 0.589, p90: 0.6, modelled: true }}
        point={0.605}
      />,
    );
    const el = screen.getByTestId("band-det-point");
    expect(el.textContent).toContain("60.5");
    expect(el.textContent).not.toContain("58.9");
    expect(el.textContent).toContain("54.0–60.5"); // clamped to include the point
    expect(el.textContent).toContain("point · modelled P10–P90");
    expect(el.textContent).not.toMatch(/P50/);
  });

  it("keeps legacy rendering when no point is supplied", () => {
    render(<BandDisplay label="V" band={{ p10: 0.4, p50: 0.5, p90: 0.6, modelled: true }} />);
    expect(screen.getByTestId("band-range")).toBeDefined();
    expect(screen.queryByTestId("band-det-point")).toBeNull();
  });
});
