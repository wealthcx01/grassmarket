/**
 * The rendered body of one lesson (GRS-0190): markdown prose, an optional video, inline SVG
 * diagrams, and the cited sources.
 *
 * One component serves both the learner reader and the authoring preview, so an author sees
 * exactly what an advisor will see rather than an approximation of it. That is the point of
 * putting it here rather than in either page.
 *
 * Only YouTube is embeddable. Every current video source is YouTube, and iframing an arbitrary
 * origin inside the Studio would hand that origin a frame in an authenticated page; any other
 * https video renders as a link card instead. The YouTube embed uses `youtube-nocookie.com` and
 * loads lazily, so opening a lesson does not set tracking cookies on the advisor.
 */

import { createElement, type ReactNode } from "react";

import { renderMarkdown, hostOf } from "@/lib/markdown";
import { sanitizeSvg, type SvgNode } from "@/lib/svg";
import type { LessonAsset, SourceRef } from "@/lib/types";

import { LessonReferences } from "./LessonReferences";

/** A YouTube watch/short/embed URL, or a bare 11-character id, yields the id. Otherwise null. */
export function youtubeId(ref: string): string | null {
  const trimmed = ref.trim();
  if (/^[A-Za-z0-9_-]{11}$/.test(trimmed)) return trimmed;
  const match =
    /^https:\/\/(?:www\.)?youtube\.com\/watch\?(?:.*&)?v=([A-Za-z0-9_-]{11})/.exec(trimmed) ??
    /^https:\/\/(?:www\.)?youtube\.com\/embed\/([A-Za-z0-9_-]{11})/.exec(trimmed) ??
    /^https:\/\/youtu\.be\/([A-Za-z0-9_-]{11})/.exec(trimmed);
  return match ? match[1]! : null;
}

function Video({ videoRef }: { videoRef: string }) {
  const id = youtubeId(videoRef);
  if (id) {
    return (
      <div style={{ position: "relative", paddingTop: "56.25%", marginTop: "0.9rem", borderRadius: "var(--radius)", overflow: "hidden", border: "1px solid var(--color-border)" }}>
        <iframe
          src={`https://www.youtube-nocookie.com/embed/${id}`}
          title="Lesson video"
          loading="lazy"
          allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          style={{ position: "absolute", inset: 0, width: "100%", height: "100%", border: 0 }}
        />
      </div>
    );
  }
  if (!/^https:\/\//.test(videoRef.trim())) {
    // Neither a YouTube id nor an https URL: say so rather than rendering a dead link.
    return (
      <p className="callout callout-warn" style={{ marginTop: "0.9rem" }}>
        This lesson has a video reference that is neither a YouTube link nor an https URL, so it
        cannot be shown.
      </p>
    );
  }
  return (
    <p style={{ marginTop: "0.9rem" }}>
      <a href={videoRef} target="_blank" rel="noopener noreferrer" className="btn btn-secondary">
        Watch on {hostOf(videoRef)} ↗
      </a>
    </p>
  );
}

/** Build React elements from the sanitised tree. No string ever becomes markup. */
function renderSvgNode(node: SvgNode, key: string): ReactNode {
  if (node.type === "text") return node.value;
  return createElement(
    node.name,
    { key, ...node.attributes },
    node.children.length === 0
      ? undefined
      : node.children.map((child, i) => renderSvgNode(child, `${key}.${i}`)),
  );
}

/**
 * One sanitised inline-SVG diagram with its caption. Exported because the slide reader
 * (GRS-0226) renders the same asset shape — a second copy would be a second sanitiser policy.
 */
export function LessonAssetFigure({ asset }: { asset: LessonAsset }) {
  const tree = sanitizeSvg(asset.svg);
  if (tree === null) {
    // Loud, not silent. A stripped-and-rendered diagram would look fine and be wrong.
    return (
      <p className="callout callout-warn" style={{ marginTop: "0.9rem" }}>
        A diagram on this lesson failed sanitisation and has not been shown. {asset.caption}
      </p>
    );
  }
  return (
    <figure style={{ margin: "1rem 0 0", maxWidth: "100%", overflowX: "auto" }}>
      {createElement(
        "svg",
        {
          ...tree.attributes,
          role: "img",
          "aria-label": asset.alt,
          style: { display: "block", maxWidth: "100%", height: "auto" },
        },
        tree.children.map((child, i) => renderSvgNode(child, `a${i}`)),
      )}
      <figcaption style={{ fontSize: "0.75rem", color: "var(--color-ink-faint)", marginTop: "0.3rem" }}>
        {asset.caption}
      </figcaption>
    </figure>
  );
}

export function LessonBody({
  body,
  videoRef,
  references = [],
  assets = [],
}: {
  body: string;
  videoRef?: string | null;
  references?: readonly SourceRef[];
  assets?: readonly LessonAsset[];
}) {
  return (
    <div>
      {renderMarkdown(body)}
      {videoRef ? <Video videoRef={videoRef} /> : null}
      {assets.map((asset, i) => (
        <LessonAssetFigure key={`${i}:${asset.caption}`} asset={asset} />
      ))}
      <LessonReferences references={references} />
    </div>
  );
}
