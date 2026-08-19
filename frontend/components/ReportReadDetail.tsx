/**
 * What a client actually read, in the words the client saw (GRS-0235).
 *
 * The deliverable page used to render this:
 *
 *     Read: business, advantage, constraint, actions, value, appendix
 *
 * — internal section keys, comma-joined, with the reader-facing titles one import away and dwell
 * time recorded but never shown. Three things follow from the ticket's framing that shape this
 * component:
 *
 * 1. **What was NOT read is the preparation signal.** A list of the sections a client opened tells
 *    an advisor far less than knowing they skipped "What that is worth" — so every section is
 *    listed in reading order and unread ones are shown as unread, never omitted.
 * 2. **Dwell is soft evidence and must not read as hard.** Coarse buckets, an explicit marker at
 *    the cap, and a caption stating what the number cannot tell you.
 * 3. **Titles come from one registry.** `lib/reportSections` mirrors the contract, so this panel,
 *    the editor, the web report and the PDF cannot disagree about what a section is called.
 */

import { SECTION_ORDER, sectionTitle } from "@/lib/reportSections";
import {
  type SectionReadRow,
  formatDwell,
  formatReadMoment,
  isAtCap,
  readWindow,
} from "@/lib/readTracking";

export interface ReportReadDetailProps {
  sections: readonly SectionReadRow[];
}

/** "3 of 6 sections", or the honest absence. Used in the table cell. */
export function readCoverageLabel(sections: readonly SectionReadRow[]): string {
  const opened = sections.filter((s) => s.views > 0).length;
  if (!opened) return "not opened yet";
  return `${opened} of ${SECTION_ORDER.length} sections`;
}

/** "12 Aug 09:14" for a single visit, "12 Aug 09:14 → 14 Aug 16:02" when they came back. */
export function readWindowLabel(sections: readonly SectionReadRow[]): string {
  const { first, last } = readWindow(sections);
  const opened = formatReadMoment(first);
  if (!opened) return "—";
  const latest = formatReadMoment(last);
  return latest && latest !== opened ? `${opened} → ${latest}` : opened;
}

export function ReportReadDetail({ sections }: ReportReadDetailProps) {
  const bySection = new Map(sections.map((s) => [s.section, s]));

  return (
    <div className="read-detail" data-testid="read-detail">
      <ul className="read-detail-list">
        {/* Reading order, from the registry — not the order the API happened to return, and not
            the order the client happened to read in. The advisor is scanning for gaps. */}
        {SECTION_ORDER.map((key) => {
          const row = bySection.get(key);
          const opened = (row?.views ?? 0) > 0;
          const dwellMs = row?.total_dwell_ms ?? 0;
          return (
            <li key={key} className={opened ? "read-row" : "read-row read-row-unread"}>
              <span className="read-row-title">{sectionTitle(key)}</span>
              {opened ? (
                <span className="read-row-dwell">
                  {formatDwell(dwellMs)}
                  {isAtCap(dwellMs) ? (
                    <span className="read-row-cap" title="A single view was capped at six hours.">
                      {" "}
                      (at the cap)
                    </span>
                  ) : null}
                </span>
              ) : (
                <span className="read-row-unread-label">not read</span>
              )}
            </li>
          );
        })}
      </ul>
      {/* The caption is the point of the whole panel: a number without its limits invites exactly
          the over-reading the rounding is designed to prevent. */}
      <p className="read-detail-caption">
        Time is rounded to the nearest 10 seconds and batched, so treat it as rough. A single view
        stops counting after six hours, and a client who reads the PDF instead of the link will show
        as unread — absence here is not proof they did not read it.
      </p>
    </div>
  );
}
