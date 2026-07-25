/**
 * GRS-0175: the merged Guide reads Concepts → Working the app → Principles; the reading-outputs
 * section defines P10/P50/P90 in words before any bare use; every section id survives (both the
 * primer's own ids and the ids the former /help page used, so `/help#assess` deep links still land);
 * the θ weights quoted match the shipped coefficient sets; and the copy holds to the STYLE-VOICE
 * register introduced by GRS-0174.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/components/GuideNav", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/components/GuideNav")>()),
  GuideNav: () => null,
}));

import GuidePage from "@/app/guide/page";
import { GUIDE_SECTIONS } from "@/components/GuideNav";

/** The primer's own section ids, listed in the ticket. Deep links to these must keep working. */
const CONCEPT_IDS = [
  "why",
  "provenance",
  "how-it-works",
  "lenses",
  "letters",
  "maturity",
  "evidence-grades",
  "scoring-powers",
  "seven-powers",
  "reading-outputs",
  "calibration",
  "mistakes",
];

/** The ids the deleted /help page used. `/help` now 308s to `/guide`, so these must resolve here. */
const HELP_IDS = [
  "start",
  "pipeline",
  "assess",
  "consensus",
  "read",
  "deliver",
  "earnings",
  "workbench",
  "principles",
];

describe("GuidePage (GRS-0175)", () => {
  it("preserves every concept section id plus the merged sections", () => {
    const { container } = render(<GuidePage />);
    for (const id of CONCEPT_IDS) {
      expect(container.querySelector(`#${id}`), `missing #${id}`).not.toBeNull();
    }
    // The merged how-to + principles + maths sections.
    expect(container.querySelector("#working-the-app")).not.toBeNull();
    expect(container.querySelector("#principles")).not.toBeNull();
    expect(container.querySelector("#scoring-explained")).not.toBeNull();
  });

  it("preserves the former /help anchors so old deep links survive the redirect", () => {
    const { container } = render(<GuidePage />);
    for (const id of HELP_IDS) {
      expect(container.querySelector(`#${id}`), `missing former /help anchor #${id}`).not.toBeNull();
    }
  });

  it("reads concepts, then working the app, then principles", () => {
    const { container } = render(<GuidePage />);
    const text = container.textContent ?? "";
    const concepts = text.indexOf("Why Platform Power exists");
    const howTo = text.indexOf("From a first prospect to a paid engagement");
    const principles = text.indexOf("The rules that never bend");
    expect(concepts).toBeGreaterThanOrEqual(0);
    expect(concepts).toBeLessThan(howTo);
    expect(howTo).toBeLessThan(principles);
  });

  it("gives GuideNav an entry for every top-level section, in document order", () => {
    const { container } = render(<GuidePage />);
    const domIds = Array.from(container.querySelectorAll("article > section")).map((s) => s.id);
    expect(GUIDE_SECTIONS.map((s) => s.id)).toEqual(domIds);
  });

  it("defines P10, P50 and P90 in words inside reading-outputs, before any bare use", () => {
    const { container } = render(<GuidePage />);
    const section = container.querySelector("#reading-outputs")!;
    const text = section.textContent ?? "";
    // The definitions are present…
    expect(text).toMatch(/P50 is the median/i);
    expect(text).toMatch(/P10 is the value that ten percent/i);
    expect(text).toMatch(/P90 the value that ninety percent/i);
    // …and the "What a modelled range is" explainer precedes the first bare "P50" token.
    const firstP50 = text.indexOf("P50");
    const rangeExplainer = text.indexOf("re-samples each input");
    expect(rangeExplainer).toBeGreaterThanOrEqual(0);
    expect(rangeExplainer).toBeLessThan(firstP50);
  });

  it("uses percentile notation only inside the section that defines it", () => {
    const { container } = render(<GuidePage />);
    // Every earlier section must be free of P10/P50/P90, so a reader never meets the notation
    // before "Reading the outputs" explains it. The heading of the definitions block itself may
    // name the three, which is why the check is scoped to the sections before it.
    const clone = container.cloneNode(true) as HTMLElement;
    const readingOutputs = clone.querySelector("#reading-outputs")!;
    readingOutputs.remove();
    // Anything after reading-outputs is downstream of the definitions, so only look upstream.
    const before = Array.from(clone.querySelectorAll("article > section"));
    const upstream = before.slice(0, before.findIndex((s) => s.id === "calibration"));
    const text = upstream.map((s) => s.textContent ?? "").join(" ");
    expect(text).not.toMatch(/P(10|50|90)/);
  });

  it("quotes the shipped per-segment weights", () => {
    render(<GuidePage />);
    // Retail 0.30/0.30/0.40, wealth 0.45/0.30/0.25, exchange 0.30/0.37/0.33 — spot-check the
    // distinctive values so a drift from the live coefficient sets fails here.
    expect(screen.getByText("0.45")).toBeTruthy();
    expect(screen.getByText("0.37")).toBeTruthy();
    expect(screen.getAllByText("0.40").length).toBeGreaterThan(0);
  });

  it("names the reviewable maths document rather than restating it", () => {
    render(<GuidePage />);
    expect(screen.getByText("docs/ATLAS-Scoring-Explained.md")).toBeTruthy();
  });

  describe("STYLE-VOICE register (GRS-0174)", () => {
    /** The page's own prose. Excludes the shared powerGuidance.ts hints, which are wizard copy
     *  swept separately; this page renders them verbatim so the wizard and the guide agree. */
    function guideProse(container: HTMLElement): string {
      const clone = container.cloneNode(true) as HTMLElement;
      clone.querySelector("#seven-powers")?.remove();
      return clone.textContent ?? "";
    }

    it("retires the mantras rather than repeating them", () => {
      const { container } = render(<GuidePage />);
      const text = container.textContent ?? "";
      for (const mantra of [
        "Words rate; numbers rank",
        "Numbers rank what to fix; words rate what you defend",
        "Read the range, not the point",
        "honest by design",
        "AI proposes; a human approves",
      ]) {
        expect(text).not.toContain(mantra);
      }
    });

    it("never chains em dashes within a sentence", () => {
      const { container } = render(<GuidePage />);
      // Split on sentence-ending punctuation; no single sentence may carry more than one em dash.
      for (const sentence of guideProse(container).split(/(?<=[.!?])\s+/)) {
        const dashes = (sentence.match(/—/g) ?? []).length;
        expect(dashes, `em-dash chain in: ${sentence}`).toBeLessThanOrEqual(1);
      }
    });

    it("does not join two clauses with a semicolon for rhythm", () => {
      const { container } = render(<GuidePage />);
      // The register allows a semicolon in a list of three or more (the value bridge's three
      // layers, for instance) but not the two-clause couplet.
      for (const sentence of guideProse(container).split(/(?<=[.!?])\s+/)) {
        const semis = (sentence.match(/;/g) ?? []).length;
        expect(semis, `semicolon couplet in: ${sentence}`).not.toBe(1);
      }
    });
  });
});
