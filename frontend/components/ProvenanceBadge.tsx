/**
 * The non-production watermark (ADR-0029 / GRS-0119). A `sandbox` or `demo` record is self-approved
 * and its deliverables are never client-facing, so it must be permanently and loudly labelled
 * wherever it appears. Renders nothing for a production record.
 */

import type { RecordProvenance } from "@/lib/types";

const LABEL: Partial<Record<RecordProvenance, string>> = {
  sandbox: "SANDBOX — non-production, not client-facing",
  demo: "DEMO — illustrative only",
};

export function ProvenanceBadge({ provenance }: { provenance: RecordProvenance }) {
  const label = LABEL[provenance];
  if (!label) return null;
  return (
    <span
      role="status"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.35rem",
        fontSize: "0.66rem",
        fontWeight: 700,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        padding: "0.2rem 0.55rem",
        borderRadius: "var(--radius-pill)",
        color: "#8a5a00",
        background: "#fbf1d8",
        border: "1px solid #e6c979",
      }}
    >
      {label}
    </span>
  );
}
