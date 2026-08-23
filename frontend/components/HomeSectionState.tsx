"use client";

/**
 * The live one-liner under each home card (GRS-0243 scope 3).
 *
 * The founder walked every section and said none of it made sense. Part of that is that the home
 * page described what each section *is* — five blurbs written once, true forever, and identical for
 * an advisor with forty prospects and one with none. Nothing on the first screen told them what was
 * actually waiting for them.
 *
 * Two rules shape what a line may say:
 *
 * 1. **A count is only shown when it means something.** "0 drafts in progress" is noise; the empty
 *    case says what would put a number there instead, which is the same discipline the section
 *    empty states now follow (scope 4).
 * 2. **A failed fetch shows nothing at all.** Not "—", not "0". The home page is the first screen
 *    after sign-in and it must not report an outage as an absence of work: an advisor who reads
 *    "no deliverables awaiting prose" when the API is down will act on it.
 *
 * Each line is fetched independently, so one slow or broken section cannot blank the others.
 */

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

export type SectionKey = "pipeline" | "portfolio" | "deliverables" | "workbench" | "earnings";

/** What the line says, or null when there is nothing honest to say. */
type Line = { text: string; muted?: boolean } | null;

async function lineFor(key: SectionKey, signal: AbortSignal): Promise<Line> {
  switch (key) {
    case "pipeline": {
      const board = await api.pipelineBoard(signal);
      const cards = board.entries ?? [];
      if (cards.length === 0) {
        return { text: "No prospects yet — add one to start the flow.", muted: true };
      }
      // Stale cards are the thing worth surfacing: the board already computes the flag, and a
      // prospect nobody has touched is the one that quietly dies.
      const stale = cards.filter((c) => c.stale).length;
      return stale
        ? { text: `${cards.length} in the pipeline · ${stale} going stale` }
        : { text: `${cards.length} in the pipeline` };
    }
    case "portfolio": {
      const rows = await api.listAssessments(signal);
      if (rows.length === 0) {
        return { text: "No assessments yet — scoring one puts it here.", muted: true };
      }
      const drafts = rows.filter((r) => r.state !== "finalised").length;
      return drafts
        ? { text: `${rows.length} assessed · ${drafts} still in progress` }
        : { text: `${rows.length} assessed, all finalised` };
    }
    case "deliverables": {
      const rows = await api.listAllDeliverables(signal);
      if (rows.length === 0) {
        return { text: "None yet — they come from a finalised assessment.", muted: true };
      }
      return { text: `${rows.length} produced` };
    }
    case "workbench": {
      // Deliberately not a count. The Workbench's useful signal is what to do next, and a bare
      // number of courses is exactly the decorative metadata this ticket is about.
      return { text: "Certification, drills and the Academy.", muted: true };
    }
    case "earnings": {
      const summary = await api.earningsSummary(signal);
      const unpaid = summary.projected_unpaid?.amount_minor ?? 0;
      if (unpaid > 0) {
        return { text: "Money owed to you that has not arrived yet." };
      }
      return { text: "Nothing outstanding — lines appear as work is recorded.", muted: true };
    }
  }
}

export function HomeSectionState({ section }: { section: SectionKey }) {
  const [line, setLine] = useState<Line>(null);

  useEffect(() => {
    const controller = new AbortController();
    lineFor(section, controller.signal)
      .then(setLine)
      // Silence on failure is the point — see the note at the top of this file.
      .catch(() => setLine(null));
    return () => controller.abort();
  }, [section]);

  if (!line) return null;
  return (
    <span
      data-testid={`home-state-${section}`}
      style={{
        display: "block",
        marginTop: "0.5rem",
        fontSize: "0.78rem",
        color: line.muted ? "var(--color-ink-faint)" : "var(--color-accent)",
      }}
    >
      {line.text}
    </span>
  );
}
