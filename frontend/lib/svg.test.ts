/**
 * GRS-0190: the SVG asset sanitiser. It returns an allowlisted node TREE rather than a string, so
 * the renderer never has to inject markup; these tests pin both the allowlist and that contract.
 */

import { describe, expect, it } from "vitest";

import { sanitizeSvg } from "@/lib/svg";

const CLEAN = `<svg viewBox="0 0 100 40" xmlns="http://www.w3.org/2000/svg">
  <title>A bar</title>
  <rect x="0" y="10" width="60" height="12" fill="#1A3B26" rx="3" />
  <line x1="0" y1="30" x2="100" y2="30" stroke="#ccc" stroke-width="1" />
  <text x="50" y="8" font-size="6" text-anchor="middle">Platform Value</text>
</svg>`;

describe("sanitizeSvg (GRS-0190)", () => {
  describe("what it accepts", () => {
    it("returns a node tree for a clean diagram, not a string", () => {
      const tree = sanitizeSvg(CLEAN);
      expect(tree).not.toBeNull();
      expect(typeof tree).toBe("object");
      expect(tree!.name).toBe("svg");
      expect(tree!.children.map((c) => (c.type === "element" ? c.name : "#text"))).toContain("rect");
    });

    it("preserves the allowlisted attributes and camelCases the ones React needs", () => {
      const tree = sanitizeSvg(CLEAN)!;
      expect(tree.attributes.viewBox).toBe("0 0 100 40");
      // xmlns is dropped: React supplies the namespace itself.
      expect(tree.attributes.xmlns).toBeUndefined();
      const rect = tree.children.find((c) => c.type === "element" && c.name === "rect");
      expect(rect && rect.type === "element" && rect.attributes.fill).toBe("#1A3B26");
      const line = tree.children.find((c) => c.type === "element" && c.name === "line");
      expect(line && line.type === "element" && line.attributes["stroke-width"]).toBe("1");
    });

    it("keeps text content inside a text element", () => {
      const tree = sanitizeSvg(CLEAN)!;
      const text = tree.children.find((c) => c.type === "element" && c.name === "text");
      expect(text && text.type === "element" && text.children[0]).toEqual({
        type: "text",
        value: "Platform Value",
      });
    });

    it("accepts gradients with their camelCase element names", () => {
      const tree = sanitizeSvg(
        `<svg viewBox="0 0 10 10"><defs><linearGradient id="g"><stop offset="0" stop-color="#fff" /></linearGradient></defs></svg>`,
      );
      expect(tree).not.toBeNull();
      const defs = tree!.children[0]!;
      expect(defs.type).toBe("element");
      const gradient = defs.type === "element" ? defs.children[0]! : null;
      expect(gradient && gradient.type === "element" ? gradient.name : null).toBe("linearGradient");
    });
  });

  describe("what it refuses", () => {
    it("refuses a script element", () => {
      expect(sanitizeSvg(`<svg viewBox="0 0 1 1"><script>alert(1)</script></svg>`)).toBeNull();
    });

    it("refuses an event-handler attribute", () => {
      expect(sanitizeSvg(`<svg viewBox="0 0 1 1" onload="alert(1)"></svg>`)).toBeNull();
      expect(sanitizeSvg(`<svg viewBox="0 0 1 1"><rect onclick="x()" /></svg>`)).toBeNull();
    });

    it("refuses foreignObject, which would smuggle arbitrary HTML in", () => {
      expect(
        sanitizeSvg(`<svg viewBox="0 0 1 1"><foreignObject><div>hi</div></foreignObject></svg>`),
      ).toBeNull();
    });

    it("refuses any href, external or otherwise", () => {
      expect(sanitizeSvg(`<svg viewBox="0 0 1 1"><use href="https://evil.example/x#a" /></svg>`)).toBeNull();
      expect(sanitizeSvg(`<svg viewBox="0 0 1 1"><rect xlink:href="#a" /></svg>`)).toBeNull();
    });

    it("refuses a namespaced element rather than allowlisting its local name", () => {
      expect(sanitizeSvg(`<svg viewBox="0 0 1 1"><xhtml:script>x</xhtml:script></svg>`)).toBeNull();
    });

    it("refuses a url() or javascript: value even in an allowlisted attribute", () => {
      expect(sanitizeSvg(`<svg viewBox="0 0 1 1"><rect fill="url(https://evil.example/x)" /></svg>`)).toBeNull();
    });

    it("refuses an attribute that is not on the allowlist", () => {
      expect(sanitizeSvg(`<svg viewBox="0 0 1 1"><rect style="behavior:url(x)" /></svg>`)).toBeNull();
    });

    it("refuses comments and CDATA, which can hide markup from a tag scan", () => {
      expect(sanitizeSvg(`<svg viewBox="0 0 1 1"><!-- <script>x</script> --></svg>`)).toBeNull();
      expect(sanitizeSvg(`<svg viewBox="0 0 1 1"><![CDATA[<script>x</script>]]></svg>`)).toBeNull();
    });

    it("refuses anything that is not rooted in a single svg element", () => {
      expect(sanitizeSvg(`<div>not an svg</div>`)).toBeNull();
      expect(sanitizeSvg(``)).toBeNull();
      expect(sanitizeSvg(`<svg viewBox="0 0 1 1"></svg><svg viewBox="0 0 1 1"></svg>`)).toBeNull();
    });

    it("refuses mismatched or unclosed nesting", () => {
      expect(sanitizeSvg(`<svg viewBox="0 0 1 1"><g><rect /></svg>`)).toBeNull();
      expect(sanitizeSvg(`<svg viewBox="0 0 1 1"><g></rect></g></svg>`)).toBeNull();
    });
  });
});
