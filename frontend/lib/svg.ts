/**
 * SVG sanitisation for lesson assets (GRS-0190).
 *
 * A lesson asset is an inline SVG string authored in-repo and rendered into a page every advisor
 * sees. SVG is not a passive image format: it can carry `<script>`, event-handler attributes,
 * `<foreignObject>` wrapping arbitrary HTML, and external references.
 *
 * The output is a **parsed node tree**, not a string. That is the important design choice here.
 * Returning a sanitised string would mean the renderer had to inject it with
 * `dangerouslySetInnerHTML`, and the whole page would then be one sanitiser bug away from HTML
 * injection. Returning a tree means the renderer builds React elements from an allowlisted
 * structure, so there is no injection point at all — the same reason the markdown renderer is
 * hand-written.
 *
 * The contract is reject-not-strip at the document level: disallowed content returns `null`, and
 * the renderer says so loudly. Quietly stripping a `<script>` and rendering the rest would leave a
 * broken diagram on the page with nobody told, which is the silent-fallback failure mode this
 * codebase refuses (#3).
 */

export interface SvgElementNode {
  type: "element";
  name: string;
  attributes: Record<string, string>;
  children: SvgNode[];
}

export interface SvgTextNode {
  type: "text";
  value: string;
}

export type SvgNode = SvgElementNode | SvgTextNode;

const ALLOWED_ELEMENTS = new Set([
  "svg",
  "g",
  "defs",
  "title",
  "desc",
  "path",
  "rect",
  "circle",
  "ellipse",
  "line",
  "polyline",
  "polygon",
  "text",
  "tspan",
  "marker",
  "lineargradient",
  "radialgradient",
  "stop",
  "clippath",
  "mask",
  "pattern",
]);

/** Elements whose SVG name is camelCase, which React requires spelled exactly. */
const ELEMENT_CASE: Record<string, string> = {
  lineargradient: "linearGradient",
  radialgradient: "radialGradient",
  clippath: "clipPath",
};

const ALLOWED_ATTRIBUTES = new Set([
  "viewbox",
  "width",
  "height",
  "x",
  "y",
  "x1",
  "y1",
  "x2",
  "y2",
  "cx",
  "cy",
  "r",
  "rx",
  "ry",
  "d",
  "points",
  "transform",
  "fill",
  "fill-opacity",
  "fill-rule",
  "stroke",
  "stroke-width",
  "stroke-opacity",
  "stroke-linecap",
  "stroke-linejoin",
  "stroke-dasharray",
  "opacity",
  "font-size",
  "font-family",
  "font-weight",
  "font-style",
  "text-anchor",
  "dominant-baseline",
  "letter-spacing",
  "class",
  "id",
  "offset",
  "stop-color",
  "stop-opacity",
  "gradientunits",
  "gradienttransform",
  "patternunits",
  "clip-path",
  "mask",
  "marker-end",
  "marker-start",
  "markerwidth",
  "markerheight",
  "refx",
  "refy",
  "orient",
  "xmlns",
  "role",
  "aria-label",
  "aria-hidden",
]);

/** Attributes React expects in camelCase. Hyphenated SVG attributes pass through as authored. */
const ATTRIBUTE_CASE: Record<string, string> = {
  viewbox: "viewBox",
  gradientunits: "gradientUnits",
  gradienttransform: "gradientTransform",
  patternunits: "patternUnits",
  markerwidth: "markerWidth",
  markerheight: "markerHeight",
  refx: "refX",
  refY: "refY",
  refy: "refY",
  class: "className",
  "clip-path": "clipPath",
};

const VOID_SAFE = new Set(["path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "stop"]);

function decodeEntities(text: string): string {
  return text
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&");
}

function attributesOf(raw: string): Record<string, string> | null {
  const out: Record<string, string> = {};
  const pattern = /([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/g;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(raw)) !== null) {
    const key = match[1]!.toLowerCase();
    const value = decodeEntities(match[2]!.replace(/^["']|["']$/g, ""));

    // Every event handler, in one rule rather than a list that will fall behind.
    if (key.startsWith("on")) return null;
    // No href of any kind. A fragment href would be safe, but `use` is not allowlisted, so no
    // element that needs one survives anyway; refusing outright keeps the rule simple.
    if (key === "href" || key.endsWith(":href")) return null;
    if (key.startsWith("xlink:") || key.startsWith("xmlns:")) return null;
    if (!ALLOWED_ATTRIBUTES.has(key)) return null;
    if (/url\s*\(|javascript\s*:|expression\s*\(/i.test(value)) return null;
    if (key === "xmlns") continue; // React supplies the namespace itself
    out[ATTRIBUTE_CASE[key] ?? key] = value;
  }
  return out;
}

/**
 * Parse an SVG string into an allowlisted node tree, or `null` if anything is disallowed.
 *
 * The scanner is hand-written rather than DOM-based: this also runs during server rendering, where
 * `DOMParser` does not exist, and a scanner cannot be tricked by a browser's error recovery into
 * seeing a different document than the one that would render.
 */
export function sanitizeSvg(svg: string): SvgElementNode | null {
  const source = svg.trim();
  if (!source.startsWith("<svg")) return null;
  // Comments and CDATA can hide markup from a tag scan; a diagram needs neither.
  if (/<!--|<!\[CDATA\[|<!DOCTYPE/i.test(source)) return null;

  const root: SvgElementNode = { type: "element", name: "svg", attributes: {}, children: [] };
  const stack: SvgElementNode[] = [];
  const tagPattern = /<\s*(\/)?\s*([a-zA-Z][a-zA-Z0-9:-]*)((?:[^>"']|"[^"]*"|'[^']*')*?)(\/)?>/g;
  let cursor = 0;
  let match: RegExpExecArray | null;
  let seenRoot = false;

  while ((match = tagPattern.exec(source)) !== null) {
    const [full, closing, rawName, rawAttributes, selfClosing] = match;
    const name = rawName!.toLowerCase();

    // Text between the previous tag and this one.
    const between = source.slice(cursor, match.index);
    cursor = match.index + full.length;
    if (between.trim() && stack.length > 0) {
      stack[stack.length - 1]!.children.push({ type: "text", value: decodeEntities(between) });
    }

    // Namespaced elements are refused outright: allowlisting the local name would let a
    // `xhtml:script` through.
    if (rawName!.includes(":")) return null;
    if (!ALLOWED_ELEMENTS.has(name)) return null;

    if (closing) {
      const open = stack.pop();
      if (!open || open.name.toLowerCase() !== name) return null; // mismatched nesting
      continue;
    }

    const attributes = attributesOf(rawAttributes ?? "");
    if (attributes === null) return null;

    if (name === "svg") {
      if (seenRoot || stack.length > 0) return null; // exactly one root
      seenRoot = true;
      root.attributes = attributes;
      stack.push(root);
      if (selfClosing) stack.pop();
      continue;
    }
    if (!seenRoot || stack.length === 0) return null; // content outside the root

    const node: SvgElementNode = {
      type: "element",
      name: ELEMENT_CASE[name] ?? name,
      attributes,
      children: [],
    };
    stack[stack.length - 1]!.children.push(node);
    if (!selfClosing) {
      stack.push(node);
    } else if (!VOID_SAFE.has(name) && !selfClosing) {
      return null;
    }
  }

  // Anything unclosed, or trailing markup after the root closed, is malformed.
  if (!seenRoot || stack.length > 0) return null;
  if (source.slice(cursor).includes("<")) return null;
  return root;
}
