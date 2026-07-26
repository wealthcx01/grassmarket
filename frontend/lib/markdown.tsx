/**
 * A markdown renderer for lesson bodies (GRS-0190).
 *
 * Hand-written, for one reason: it builds React elements directly and never touches
 * `dangerouslySetInnerHTML`, so the HTML-injection surface is zero rather than "small, assuming the
 * library and its transitive dependencies stay correct". Lesson bodies are authored in-repo and by
 * admins, but a published `CourseVersion` is served to every advisor, so the blast radius of a
 * mistake there is the whole network.
 *
 * The supported subset is exactly what the content programme (GRS-0191) needs and no more:
 * `#`/`##`/`###` headings, paragraphs, `**bold**`, `*italic*`, `` `code` ``, fenced code blocks,
 * ordered and unordered lists at one nesting level, GFM pipe tables, and https links.
 *
 * Three rules make the subset safe:
 *
 * - Raw HTML is never parsed. `<script>alert(1)</script>` renders as that literal text, because
 *   text only ever becomes a React text node.
 * - A link URL that does not start `https://` renders as plain text, so `javascript:` and
 *   downgraded `http://` links cannot become anchors.
 * - Markdown image syntax is unsupported. Diagrams are `LessonAsset` SVGs, which go through the
 *   sanitiser; there is no second image path that would bypass it.
 */

import type { ReactNode } from "react";

const HEADING = /^(#{1,3})\s+(.*)$/;
const UNORDERED = /^[-*]\s+(.+)$/;
const ORDERED = /^\d+[.)]\s+(.+)$/;
const FENCE = /^```/;
const TABLE_DIVIDER = /^\|?[\s:|-]+\|[\s:|-]*$/;

/** An https link is the only kind that becomes an anchor. Everything else stays text. */
export function isSafeUrl(url: string): boolean {
  return /^https:\/\/[^\s]+$/.test(url.trim());
}

/** The host, shown on link cards and next to external links so a reader sees where they are going. */
export function hostOf(url: string): string {
  const match = /^https:\/\/([^/?#]+)/.exec(url.trim());
  return match ? match[1]!.replace(/^www\./, "") : url;
}

/**
 * Inline spans: bold, italic, code, and links. Applied by splitting on one alternation so the
 * segments never overlap, which is what keeps a single pass correct without a nested parser.
 */
export function renderInline(text: string, keyPrefix = ""): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*\n]+\*|`[^`\n]+`|\[[^\]\n]+\]\([^)\s]+\))/g);
  return parts.filter((p) => p !== "").map((part, i) => {
    const key = `${keyPrefix}i${i}`;
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return <strong key={key}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
      return (
        <code key={key} className="mono" style={{ fontSize: "0.88em", background: "var(--color-paper-sunken)", padding: "0.1em 0.3em", borderRadius: "3px" }}>
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      return <em key={key}>{part.slice(1, -1)}</em>;
    }
    const link = /^\[([^\]]+)\]\(([^)\s]+)\)$/.exec(part);
    if (link) {
      const [, label, url] = link;
      // A non-https URL renders as the literal markdown rather than as an anchor. Rendering the
      // label alone would quietly hide that a link was intended and where it pointed.
      if (!isSafeUrl(url!)) return <span key={key}>{part}</span>;
      return (
        <a key={key} href={url} target="_blank" rel="noopener noreferrer">
          {label}
          <span aria-hidden style={{ fontSize: "0.85em", marginLeft: "0.15em" }}>
            ↗
          </span>
        </a>
      );
    }
    return <span key={key}>{part}</span>;
  });
}

function splitRow(line: string): string[] {
  return line
    .replace(/^\||\|$/g, "")
    .split("|")
    .map((cell) => cell.trim());
}

/** Parse a lesson body into React elements. Never returns HTML, only elements and text nodes. */
export function renderMarkdown(source: string): ReactNode[] {
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const out: ReactNode[] = [];
  let paragraph: string[] = [];
  let index = 0;

  const flushParagraph = () => {
    if (paragraph.length === 0) return;
    const text = paragraph.join(" ").trim();
    paragraph = [];
    if (text) {
      out.push(
        <p key={`p${out.length}`} style={{ margin: out.length === 0 ? 0 : "0.7rem 0 0", fontSize: "0.92rem", lineHeight: 1.65 }}>
          {renderInline(text, `p${out.length}`)}
        </p>,
      );
    }
  };

  while (index < lines.length) {
    const line = lines[index]!;

    if (FENCE.test(line.trim())) {
      flushParagraph();
      const code: string[] = [];
      index += 1;
      while (index < lines.length && !FENCE.test(lines[index]!.trim())) {
        code.push(lines[index]!);
        index += 1;
      }
      index += 1; // consume the closing fence, or fall off the end on an unclosed block
      out.push(
        <pre
          key={`code${out.length}`}
          className="mono"
          style={{ margin: "0.8rem 0 0", padding: "0.8rem 1rem", background: "var(--color-paper-sunken)", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", overflowX: "auto", fontSize: "0.82rem", lineHeight: 1.5 }}
        >
          {code.join("\n")}
        </pre>,
      );
      continue;
    }

    const heading = HEADING.exec(line);
    if (heading) {
      flushParagraph();
      const depth = heading[1]!.length;
      // h3-h5: the lesson title above is already an h2, so a body heading never outranks it.
      const Tag = (["h3", "h4", "h5"] as const)[depth - 1]!;
      const size = ["1.02rem", "0.96rem", "0.9rem"][depth - 1]!;
      out.push(
        <Tag key={`h${out.length}`} style={{ margin: "1rem 0 0.3rem", fontSize: size }}>
          {renderInline(heading[2]!, `h${out.length}`)}
        </Tag>,
      );
      index += 1;
      continue;
    }

    // A table needs a header row and the `|---|` divider beneath it, so a lone pipe in prose is
    // never mistaken for one.
    if (line.includes("|") && index + 1 < lines.length && TABLE_DIVIDER.test(lines[index + 1]!.trim()) && lines[index + 1]!.includes("|")) {
      flushParagraph();
      const header = splitRow(line);
      index += 2;
      const rows: string[][] = [];
      while (index < lines.length && lines[index]!.includes("|") && lines[index]!.trim() !== "") {
        rows.push(splitRow(lines[index]!));
        index += 1;
      }
      const key = `t${out.length}`;
      out.push(
        <div key={key} style={{ overflowX: "auto", margin: "0.8rem 0 0" }}>
          <table style={{ borderCollapse: "collapse", fontSize: "0.86rem", minWidth: "100%" }}>
            <thead>
              <tr>
                {header.map((cell, c) => (
                  <th key={c} style={{ textAlign: "left", padding: "0.4rem 0.7rem", borderBottom: "1px solid var(--color-border-strong)" }}>
                    {renderInline(cell, `${key}h${c}`)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, r) => (
                <tr key={r}>
                  {row.map((cell, c) => (
                    <td key={c} style={{ padding: "0.4rem 0.7rem", borderBottom: "1px solid var(--color-border)", verticalAlign: "top" }}>
                      {renderInline(cell, `${key}r${r}c${c}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    const unordered = UNORDERED.exec(line);
    const ordered = ORDERED.exec(line);
    if (unordered || ordered) {
      flushParagraph();
      const isOrdered = ordered !== null;
      const items: string[] = [];
      while (index < lines.length) {
        const current = lines[index]!;
        const match = isOrdered ? ORDERED.exec(current) : UNORDERED.exec(current);
        if (!match) break;
        items.push(match[1]!);
        index += 1;
      }
      const ListTag = isOrdered ? "ol" : "ul";
      const key = `l${out.length}`;
      out.push(
        <ListTag key={key} style={{ margin: "0.6rem 0 0", paddingLeft: "1.2rem", fontSize: "0.92rem", lineHeight: 1.6 }}>
          {items.map((item, i) => (
            <li key={i} style={{ marginBottom: "0.2rem" }}>
              {renderInline(item, `${key}n${i}`)}
            </li>
          ))}
        </ListTag>,
      );
      continue;
    }

    if (line.trim() === "") {
      flushParagraph();
    } else {
      paragraph.push(line.trim());
    }
    index += 1;
  }

  flushParagraph();
  return out;
}
