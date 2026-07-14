/**
 * Workbench (GRS-0027, PRD §6) — the advisor's development surface: bench-time queue, certification,
 * learning + drills, practice arena, calibration, and the members-only committee entry point. All
 * data is JWT-scoped server-side; the client shell just mirrors the role gates.
 */

import { WorkbenchClient } from "@/components/workbench/WorkbenchClient";

export default function WorkbenchPage() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <header>
        <p className="mono" style={{ margin: 0, fontSize: "0.72rem", letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--color-ink-muted)" }}>
          Workbench
        </p>
        <h1 style={{ fontSize: "1.6rem", margin: "0.3rem 0 0" }}>Develop your practice</h1>
      </header>
      <WorkbenchClient />
    </div>
  );
}
