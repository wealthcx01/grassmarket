/**
 * The one display-label map for deliverable types (GRS-0186). Imported by both DeliverablesPanel
 * and the deliverables index so the seven labels live in a single place and cannot drift.
 */

import type { DeliverableType } from "@/lib/types";

export const TYPE_LABEL: Record<DeliverableType, string> = {
  executive_summary: "Executive Summary",
  platform_power_report: "Platform Power Report",
  infrastructure_heatmap: "Infrastructure Heatmap",
  modernisation_roadmap: "Modernisation Roadmap",
  technical_appendix: "Technical Appendix",
  workshop_output: "Workshop Output",
  score_evolution: "Score Evolution",
};
