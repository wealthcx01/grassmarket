/**
 * Level display names, in one place (GRS-0242).
 *
 * Bench and the Certification ladder both name an advisor's level. When each held its own mapping,
 * Bench rendered the wire value with underscores swapped for spaces ("certified lead") while the
 * ladder rendered a proper title — the same person, described two ways on adjacent tabs.
 */

import type { AssessorLevelValue } from "@/lib/types";

export const LEVEL_LABEL: Record<AssessorLevelValue, string> = {
  trained: "Trained",
  shadow: "Shadow",
  observed_lead: "Observed Lead",
  certified_lead: "Certified Lead",
};
