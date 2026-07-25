/**
 * GRS-0190: the lesson markdown subset. The security assertions matter more than the formatting
 * ones — this renderer serves published course versions to every advisor, so raw HTML must stay
 * text and a non-https link must never become an anchor.
 */

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { hostOf, isSafeUrl, renderMarkdown } from "@/lib/markdown";

function draw(source: string) {
  const { container } = render(<div>{renderMarkdown(source)}</div>);
  return container;
}

describe("renderMarkdown (GRS-0190)", () => {
  describe("injection surface", () => {
    it("renders raw HTML as literal text, never as elements", () => {
      const container = draw("Before <script>alert(1)</script> after");
      expect(container.querySelector("script")).toBeNull();
      expect(container.textContent).toContain("<script>alert(1)</script>");
    });

    it("renders an inline HTML tag as text", () => {
      const container = draw('An <img src=x onerror="alert(1)"> in prose');
      expect(container.querySelector("img")).toBeNull();
      expect(container.textContent).toContain("<img src=x");
    });

    it("refuses to make a javascript: link an anchor", () => {
      const container = draw("[click me](javascript:alert(1))");
      expect(container.querySelector("a")).toBeNull();
      // The literal markdown is shown, so it is visible that a link was intended and where to.
      expect(container.textContent).toContain("javascript:alert(1)");
    });

    it("refuses to make an http:// link an anchor", () => {
      const container = draw("[downgraded](http://example.com)");
      expect(container.querySelector("a")).toBeNull();
      expect(container.textContent).toContain("http://example.com");
    });

    it("does not support markdown images, so there is no second image path", () => {
      const container = draw("![alt](https://example.com/x.png)");
      expect(container.querySelector("img")).toBeNull();
    });

    it("renders an https link with the external-safety attributes", () => {
      const anchor = draw("[docs](https://docs.openbb.co/platform)").querySelector("a")!;
      expect(anchor.getAttribute("href")).toBe("https://docs.openbb.co/platform");
      expect(anchor.getAttribute("target")).toBe("_blank");
      expect(anchor.getAttribute("rel")).toBe("noopener noreferrer");
      expect(anchor.textContent).toContain("docs");
    });
  });

  describe("block structure", () => {
    it("renders paragraphs split on blank lines", () => {
      const container = draw("First para.\n\nSecond para.");
      expect(container.querySelectorAll("p")).toHaveLength(2);
    });

    it("renders headings as h3 to h5 so they never outrank the lesson title", () => {
      const container = draw("# One\n\n## Two\n\n### Three");
      expect(container.querySelector("h3")?.textContent).toBe("One");
      expect(container.querySelector("h4")?.textContent).toBe("Two");
      expect(container.querySelector("h5")?.textContent).toBe("Three");
      expect(container.querySelector("h1")).toBeNull();
      expect(container.querySelector("h2")).toBeNull();
    });

    it("renders unordered and ordered lists", () => {
      const unordered = draw("- one\n- two");
      expect(unordered.querySelectorAll("ul li")).toHaveLength(2);
      const ordered = draw("1. first\n2. second");
      expect(ordered.querySelectorAll("ol li")).toHaveLength(2);
      expect(ordered.querySelector("ol li")?.textContent).toBe("first");
    });

    it("renders a fenced code block verbatim without interpreting it", () => {
      const container = draw("```\nobb.equity.price.historical('AAPL')\n**not bold**\n```");
      const pre = container.querySelector("pre")!;
      expect(pre.textContent).toContain("obb.equity.price.historical('AAPL')");
      expect(pre.textContent).toContain("**not bold**");
      expect(pre.querySelector("strong")).toBeNull();
    });

    it("renders a pipe table with its header", () => {
      const container = draw("| Field | Meaning |\n|---|---|\n| ric | The ticker |\n| ctb | The bank |");
      expect(container.querySelectorAll("thead th")).toHaveLength(2);
      expect(container.querySelectorAll("tbody tr")).toHaveLength(2);
      expect(container.querySelector("thead th")?.textContent).toBe("Field");
    });

    it("does not mistake a lone pipe in prose for a table", () => {
      const container = draw("Use the pipe | character carefully.");
      expect(container.querySelector("table")).toBeNull();
      expect(container.querySelectorAll("p")).toHaveLength(1);
    });

    it("survives an unclosed code fence without dropping the content", () => {
      const container = draw("```\nunterminated");
      expect(container.querySelector("pre")?.textContent).toContain("unterminated");
    });

    it("renders an empty body as nothing rather than throwing", () => {
      expect(draw("").textContent).toBe("");
    });
  });

  describe("inline spans", () => {
    it("renders bold, italic and inline code", () => {
      const container = draw("**bold** and *italic* and `code`");
      expect(container.querySelector("strong")?.textContent).toBe("bold");
      expect(container.querySelector("em")?.textContent).toBe("italic");
      expect(container.querySelector("code")?.textContent).toBe("code");
    });

    it("renders inline spans inside list items and headings", () => {
      expect(draw("- a **bold** item").querySelector("li strong")?.textContent).toBe("bold");
      expect(draw("## a **bold** heading").querySelector("h4 strong")?.textContent).toBe("bold");
    });

    it("leaves a bare asterisk alone", () => {
      const container = draw("2 * 3 = 6");
      expect(container.querySelector("em")).toBeNull();
      expect(container.textContent).toContain("2 * 3 = 6");
    });
  });

  describe("plain prose (the pre-GRS-0190 corpus)", () => {
    it("renders an existing seeded body exactly as before: paragraphs with bold spans", () => {
      const container = draw(
        "The Sales Egoist doctrine starts from **discomfort**.\n\nYou earn the right to advise.",
      );
      expect(container.querySelectorAll("p")).toHaveLength(2);
      expect(container.querySelector("strong")?.textContent).toBe("discomfort");
      expect(container.textContent).toContain("You earn the right to advise.");
    });
  });
});

describe("isSafeUrl / hostOf", () => {
  it("accepts only https", () => {
    expect(isSafeUrl("https://example.com/x")).toBe(true);
    expect(isSafeUrl("http://example.com")).toBe(false);
    expect(isSafeUrl("javascript:alert(1)")).toBe(false);
    expect(isSafeUrl("//example.com")).toBe(false);
    expect(isSafeUrl("https://has space.com")).toBe(false);
  });

  it("shows the host without the www prefix", () => {
    expect(hostOf("https://www.youtube.com/watch?v=abc")).toBe("youtube.com");
    expect(hostOf("https://docs.openbb.co/platform")).toBe("docs.openbb.co");
  });
});
