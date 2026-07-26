/**
 * GRS-0190: the shared lesson body. One component serves the learner reader and the authoring
 * preview, so what is asserted here is what an author sees and what an advisor sees.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LessonBody, youtubeId } from "@/components/workbench/LessonBody";
import type { LessonAsset, SourceRef } from "@/lib/types";

const DIAGRAM: LessonAsset = {
  caption: "The terminal barbell",
  alt: "Two heavy ends joined by a thin bar",
  svg: `<svg viewBox="0 0 100 20"><rect x="0" y="0" width="20" height="20" fill="#1A3B26" /><rect x="80" y="0" width="20" height="20" fill="#1A3B26" /></svg>`,
};

const REFERENCES: SourceRef[] = [
  { title: "OpenBB Platform reference", url: "https://docs.openbb.co/platform", kind: "docs" },
  { title: "The pivot, explained", url: "https://openbb.co/blog/pivot", kind: "blog" },
];

describe("youtubeId", () => {
  it("accepts the watch, short, embed and bare-id forms", () => {
    expect(youtubeId("https://www.youtube.com/watch?v=dQw4w9WgXcQ")).toBe("dQw4w9WgXcQ");
    expect(youtubeId("https://youtu.be/dQw4w9WgXcQ")).toBe("dQw4w9WgXcQ");
    expect(youtubeId("https://www.youtube.com/embed/dQw4w9WgXcQ")).toBe("dQw4w9WgXcQ");
    expect(youtubeId("dQw4w9WgXcQ")).toBe("dQw4w9WgXcQ");
  });

  it("rejects anything else, including a lookalike host", () => {
    expect(youtubeId("https://vimeo.com/123456")).toBeNull();
    expect(youtubeId("https://notyoutube.com/watch?v=dQw4w9WgXcQ")).toBeNull();
    expect(youtubeId("http://www.youtube.com/watch?v=dQw4w9WgXcQ")).toBeNull();
  });
});

describe("LessonBody (GRS-0190)", () => {
  it("renders the markdown body", () => {
    const { container } = render(<LessonBody body={"## A heading\n\nSome **prose**."} />);
    expect(container.querySelector("h4")?.textContent).toBe("A heading");
    expect(container.querySelector("strong")?.textContent).toBe("prose");
  });

  it("embeds a YouTube video privately and lazily", () => {
    const { container } = render(
      <LessonBody body="x" videoRef="https://www.youtube.com/watch?v=dQw4w9WgXcQ" />,
    );
    const iframe = container.querySelector("iframe")!;
    expect(iframe.getAttribute("src")).toBe("https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ");
    expect(iframe.getAttribute("loading")).toBe("lazy");
  });

  it("embeds a bare 11-character id the same way", () => {
    const { container } = render(<LessonBody body="x" videoRef="dQw4w9WgXcQ" />);
    expect(container.querySelector("iframe")?.getAttribute("src")).toContain("dQw4w9WgXcQ");
  });

  it("renders a non-YouTube https video as a link card, never as an iframe", () => {
    // Iframing an arbitrary origin inside an authenticated page hands that origin a frame.
    const { container } = render(<LessonBody body="x" videoRef="https://vimeo.com/123456" />);
    expect(container.querySelector("iframe")).toBeNull();
    const anchor = container.querySelector("a")!;
    expect(anchor.getAttribute("href")).toBe("https://vimeo.com/123456");
    expect(anchor.getAttribute("rel")).toBe("noopener noreferrer");
    expect(anchor.textContent).toContain("vimeo.com");
  });

  it("says so rather than rendering a dead link when a video ref is neither", () => {
    const { container } = render(<LessonBody body="x" videoRef="javascript:alert(1)" />);
    expect(container.querySelector("iframe")).toBeNull();
    expect(container.querySelector("a")).toBeNull();
    expect(screen.getByText(/cannot be shown/)).toBeTruthy();
  });

  it("renders references as link cards with kind, title and host", () => {
    render(<LessonBody body="x" references={REFERENCES} />);
    expect(screen.getByText("Sources")).toBeTruthy();
    expect(screen.getByText("OpenBB Platform reference")).toBeTruthy();
    expect(screen.getByText("Docs")).toBeTruthy();
    expect(screen.getByText("Article")).toBeTruthy();
    expect(screen.getByText(/docs\.openbb\.co/)).toBeTruthy();
  });

  it("omits the sources section entirely when there are none", () => {
    render(<LessonBody body="x" />);
    expect(screen.queryByText("Sources")).toBeNull();
  });

  it("renders a sanitised asset as real SVG elements with its caption and alt", () => {
    const { container } = render(<LessonBody body="x" assets={[DIAGRAM]} />);
    const svg = container.querySelector("svg")!;
    expect(svg.getAttribute("aria-label")).toBe("Two heavy ends joined by a thin bar");
    expect(svg.getAttribute("role")).toBe("img");
    expect(svg.querySelectorAll("rect")).toHaveLength(2);
    expect(screen.getByText("The terminal barbell")).toBeTruthy();
  });

  it("refuses a scripted asset loudly instead of stripping it and rendering the rest", () => {
    const { container } = render(
      <LessonBody
        body="x"
        assets={[{ ...DIAGRAM, svg: `<svg viewBox="0 0 1 1"><script>alert(1)</script></svg>` }]}
      />,
    );
    expect(container.querySelector("svg")).toBeNull();
    expect(container.querySelector("script")).toBeNull();
    expect(screen.getByText(/failed sanitisation/)).toBeTruthy();
  });

  it("renders a lesson with none of the new fields exactly as plain prose", () => {
    // The pre-GRS-0190 corpus: every seeded lesson must be unaffected.
    const { container } = render(<LessonBody body={"First para.\n\nSecond para."} />);
    expect(container.querySelector("iframe")).toBeNull();
    expect(container.querySelector("svg")).toBeNull();
    expect(screen.queryByText("Sources")).toBeNull();
  });
});
