/**
 * The client-facing report page (GRS-0220).
 *
 * The web rendition of the SAME content model the PDF prints (GRS-0211/0219). It never says anything
 * the PDF does not — the payload it renders is the snapshot taken when the link was issued, so a
 * client who read this last week and quotes it back is quoting something that still exists.
 *
 * Three things here are product requirements rather than styling choices:
 *
 * 1. **The appendix is disclosed, not deleted.** It sits behind a native <details> so the body reads
 *    as a story while nothing is hidden from a client who wants the numbers. Native, because a
 *    hand-rolled expander is one more thing to get wrong for a keyboard or a screen reader.
 * 2. **Tracking is disclosed on the page.** The notice is rendered before any event is sent, and it
 *    is not dismissible. We record which sections were opened and for how long; the reader is told
 *    so in plain words.
 * 3. **Reduced motion is honoured.** Everything here is CSS transitions the media query disables.
 */

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

// GRS-0235: the titles and the dwell ceiling come from one place each, mirrored from the contract
// and drift-tested against it. This file used to carry its own copy of both.
import { MAX_DWELL_MS as CONTRACT_MAX_DWELL_MS } from "@/lib/readTracking";
import { SECTION_TITLES } from "@/lib/reportSections";

export type Figure = {
  labels: string[];
  values: number[];
  /** One line per entry, shown on hover (GRS-0233 scope 4). May be absent on older snapshots. */
  notes?: string[];
  /** True when the ORDER carries meaning and must be rendered as given (GRS-0233 scope 2). */
  ordered?: boolean;
};

export type SharedReportPayload = {
  report: {
    subject: string;
    methodology_version: string;
    coefficient_version: string;
    sections: {
      kind: string;
      heading: string;
      body: string[];
      figures: { key: string; label: string; rendered: string; source: string }[];
    }[];
  };
  figures: Record<string, Figure>;
  tracking_notice: string;
  /** Demo or sandbox provenance at issue — the numbers describe nobody's actual platform. */
  non_production?: boolean;
  /** The deliverable was DRAFT_INTERNAL at issue — not approved for client use. */
  draft?: boolean;
};

/* The PDF's two marks, verbatim (`deliverables/gate.py:DRAFT_WATERMARK` and the second mark in
   `report_pdf/render.py:_draw_watermark`). Reused rather than reworded so the two renditions of the
   same record cannot tell a reader different things — GRS-0220's whole premise is one source, two
   renditions, and this is the part of it that was missing. */
const DRAFT_MARK = "DRAFT \u2014 not client-usable";
const NON_PRODUCTION_MARK = "NON-PRODUCTION DATA";

/** The banner text for a record's marks, or null when there is nothing to say. */
export function reportMarkText(payload: {
  non_production?: boolean;
  draft?: boolean;
}): string | null {
  // `?? true` is the safe direction and it matches the backend's own default. A payload with no
  // flags is a snapshot issued before GRS-0229, whose provenance nobody recorded — which is exactly
  // the case where a reader should be told the numbers may not be production. Defaulting to false
  // here would have let a legacy link render a clean, unmarked page.
  const marks = [
    (payload.draft ?? true) ? DRAFT_MARK : null,
    (payload.non_production ?? true) ? NON_PRODUCTION_MARK : null,
  ].filter(Boolean);
  if (marks.length === 0) return null;
  return `${marks.join("  \u00b7  ")} \u2014 this report does not describe a live platform`;
}

/** A tab left open overnight is not reading — the API refuses more, so don't send it. */
const MAX_DWELL_MS = CONTRACT_MAX_DWELL_MS;

/**
 * Report one section's dwell time when it leaves the screen.
 *
 * Batched on exit rather than polled: an interval would inflate every number with time the reader
 * spent on another tab, and would send far more events than the advisor's summary needs.
 */
function useSectionTracking(token: string, enabled: boolean) {
  const enteredAt = useRef<Record<string, number>>({});
  const send = useCallback(
    (section: string, dwellMs: number) => {
      if (!enabled || dwellMs < 500) return; // a scroll-past is not a read
      const base =
        process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:8000";
      const body = JSON.stringify({
        section,
        dwell_ms: Math.min(Math.round(dwellMs), MAX_DWELL_MS),
      });
      // keepalive so the last section still reports when the tab is closing.
      void fetch(`${base}/shared/report/${encodeURIComponent(token)}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
        keepalive: true,
      }).catch(() => {
        // A failed read event must never break the reader's page. Losing one is acceptable;
        // showing a client an error because our analytics call failed is not.
      });
    },
    [token, enabled]
  );

  const observe = useCallback(
    (section: string, node: HTMLElement | null) => {
      if (!node || !enabled) return undefined;
      const observer = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (entry.isIntersecting) {
              enteredAt.current[section] ??= Date.now();
            } else if (enteredAt.current[section]) {
              send(section, Date.now() - enteredAt.current[section]);
              delete enteredAt.current[section];
            }
          }
        },
        { threshold: 0.35 }
      );
      observer.observe(node);
      return () => observer.disconnect();
    },
    [send, enabled]
  );

  // Flush whatever is still on screen when the reader leaves.
  useEffect(() => {
    if (!enabled) return undefined;
    const flush = () => {
      for (const [section, at] of Object.entries(enteredAt.current)) {
        send(section, Date.now() - at);
      }
      enteredAt.current = {};
    };
    window.addEventListener("pagehide", flush);
    return () => {
      window.removeEventListener("pagehide", flush);
      flush();
    };
  }, [send, enabled]);

  return observe;
}

/**
 * A horizontal bar chart in plain SVG.
 *
 * SVG rather than an image so it scales on a phone and stays readable to a screen reader: the whole
 * chart carries a role and a label, and every bar states its own value in text. Nothing is encoded
 * by colour alone, matching the PDF's greyscale rule.
 */
function BarFigure({ figure, caption }: { figure: Figure; caption: string }) {
  const rows = useMemo(() => {
    const built = figure.labels.map((label, index) => ({
      label,
      value: figure.values[index] ?? 0,
      note: figure.notes?.[index],
    }));
    // GRS-0233 scope 2. The old renderer sorted EVERY figure ascending, which turned the value
    // build-up into four bars in the wrong sequence under a caption promising a composition. A
    // series that declares its order keeps it; a ranked one is still shown weakest-first, because
    // weakest-first is what its caption says it is.
    return figure.ordered ? built : [...built].sort((a, b) => a.value - b.value);
  }, [figure]);
  if (!rows.length) return null;

  const max = Math.max(...rows.map((r) => r.value), 100);

  return (
    <figure className="shared-figure">
      {/* GRS-0233 scope 1. This was nine unlabelled <rect>s in an SVG, with the names in a separate
          grid sorted differently — a client had to count rows against a mismatched table to know
          which bar was which. Rows of HTML instead of a stretched SVG: the label wraps at phone
          widths instead of distorting or truncating, and the value sits beside its own bar. */}
      <div
        className="shared-bars"
        role="img"
        aria-label={`${caption}. ${rows
          .map((r) => `${r.label}: ${r.value.toFixed(0)} out of 100`)
          .join(". ")}`}
      >
        {rows.map((row) => (
          <div className="shared-bar-row" key={row.label} title={row.note ?? undefined}>
            <span className="shared-bar-label">{row.label}</span>
            <span className="shared-bar-track" aria-hidden>
              <span
                className="shared-bar-fill"
                style={{ width: `${Math.max((row.value / max) * 100, 0.5)}%` }}
              />
            </span>
            <b className="shared-bar-value">{row.value.toFixed(0)}</b>
          </div>
        ))}
      </div>
      <figcaption>{caption}</figcaption>
    </figure>
  );
}

export function SharedReport({
  payload,
  token,
  trackingEnabled = true,
}: {
  payload: SharedReportPayload;
  token: string;
  /** False for the advisor's own preview — an advisor checking their work is not a client read. */
  trackingEnabled?: boolean;
}) {
  const observe = useSectionTracking(token, trackingEnabled);
  const { report, figures } = payload;
  const mark = reportMarkText(payload);
  const body = report.sections.filter((s) => s.kind !== "appendix");
  const appendix = report.sections.find((s) => s.kind === "appendix");

  return (
    <article className="shared-report">
      {/* Fixed, so it is on screen at every scroll position — the PDF repeats its watermark on
          every page and a banner that scrolls away is not the same guarantee. role="alert" rather
          than "note": this is the one thing on the page a reader must not miss. */}
      {mark ? (
        <p className="shared-report-mark" role="alert" data-testid="report-mark">
          {mark}
        </p>
      ) : null}
      <header className="shared-report-head">
        <p className="eyebrow">Bruntsfield Advisory Network</p>
        <h1>{report.subject}</h1>
        <p className="shared-report-sub">Platform assessment</p>
      </header>

      {/* Rendered before any event is sent, and not dismissible. */}
      <p className="shared-report-notice" role="note">
        {payload.tracking_notice}
      </p>

      {body.map((section) => (
        <Section
          key={section.kind}
          kind={section.kind}
          heading={SECTION_TITLES[section.kind] ?? section.heading}
          paragraphs={section.body}
          observe={observe}
        >
          {section.kind === "constraint" && figures.maturity ? (
            <BarFigure
              figure={figures.maturity}
              caption="Module maturity across the assessed modules (0–100)."
            />
          ) : null}
          {section.kind === "value" && figures.value_buildup ? (
            <BarFigure
              figure={figures.value_buildup}
              caption="How Platform Value builds up from the underlying indices."
            />
          ) : null}
        </Section>
      ))}

      {appendix ? (
        <details className="shared-appendix">
          <summary>
            {SECTION_TITLES.appendix}
            <span> — the numbers behind everything above</span>
          </summary>
          <SectionBody
            kind="appendix"
            paragraphs={appendix.body}
            observe={observe}
          />
          {figures.module_breakdown ? (
            <BarFigure
              figure={figures.module_breakdown}
              caption="Every assessed module, weakest first. Unassessed modules are omitted, not scored zero."
            />
          ) : null}
          {appendix.figures.length ? (
            <table className="shared-figures-table">
              <caption>Every figure quoted in this report</caption>
              <thead>
                <tr>
                  <th scope="col">Figure</th>
                  <th scope="col">Value</th>
                  <th scope="col">Source</th>
                </tr>
              </thead>
              <tbody>
                {appendix.figures.map((figure) => (
                  <tr key={figure.key}>
                    <td>{figure.label}</td>
                    <td className="mono">{figure.rendered}</td>
                    <td className="mono">{figure.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </details>
      ) : null}

      <footer className="shared-report-foot">
        Confidential — prepared for {report.subject}. Methodology {report.methodology_version} ·
        coefficients {report.coefficient_version}.
      </footer>
    </article>
  );
}

function Section({
  kind,
  heading,
  paragraphs,
  observe,
  children,
}: {
  kind: string;
  heading: string;
  paragraphs: string[];
  observe: (section: string, node: HTMLElement | null) => (() => void) | undefined;
  children?: React.ReactNode;
}) {
  return (
    <section className="shared-section" aria-labelledby={`h-${kind}`}>
      <h2 id={`h-${kind}`}>{heading}</h2>
      <SectionBody kind={kind} paragraphs={paragraphs} observe={observe} />
      {children}
    </section>
  );
}

function SectionBody({
  kind,
  paragraphs,
  observe,
}: {
  kind: string;
  paragraphs: string[];
  observe: (section: string, node: HTMLElement | null) => (() => void) | undefined;
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [node, setNode] = useState<HTMLDivElement | null>(null);
  useEffect(() => observe(kind, node), [observe, kind, node]);
  return (
    <div
      ref={(element) => {
        ref.current = element;
        setNode(element);
      }}
    >
      {paragraphs.map((paragraph, index) => (
        <p key={index}>{paragraph}</p>
      ))}
    </div>
  );
}
