"use client";

/**
 * The Workbench (GRS-0027, PRD §6) — one coherent surface over the Loop 5 APIs: the bench-time
 * dashboard, certification, learning + drills, the practice arena, calibration, and (members only)
 * the rating committee. Role gating here mirrors the API's JWT claims exactly — the Committee tab is
 * mounted only for a committee member or admin, the same gate the server enforces.
 */

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { getSession } from "@/lib/session";
import { BenchDashboard } from "@/components/workbench/BenchDashboard";
import { CalibrationPanel } from "@/components/workbench/CalibrationPanel";
import { CertificationPanel } from "@/components/workbench/CertificationPanel";
import { CommitteePanel } from "@/components/workbench/CommitteePanel";
import { LearningDrillsPanel } from "@/components/workbench/LearningDrillsPanel";
import { ArenaPanel } from "@/components/workbench/ArenaPanel";
import { RatingRequestsPanel } from "@/components/workbench/RatingRequestsPanel";

type TabKey =
  | "bench"
  | "certification"
  | "learning"
  | "arena"
  | "calibration"
  | "requests"
  | "committee";

export function WorkbenchClient() {
  // The session comes from localStorage, which the server can't read — reading it during render
  // makes the first client paint diverge from the server HTML (hydration mismatch, React #418).
  // Gate on `mounted` so the server and first client render agree, then read it after mount.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const session = useMemo(() => (mounted ? getSession() : null), [mounted]);
  const tabs = useMemo(() => {
    const base: { key: TabKey; label: string }[] = [
      { key: "bench", label: "Bench" },
      { key: "certification", label: "Certification" },
      { key: "learning", label: "Learning & Drills" },
      { key: "arena", label: "Practice Arena" },
      { key: "calibration", label: "Calibration" },
      { key: "requests", label: "Rating requests" },
    ];
    if (session?.isCommittee) base.push({ key: "committee", label: "Committee" });
    return base;
  }, [session]);
  const [tab, setTab] = useState<TabKey>("bench");

  // Stable placeholder for the server render and the first client paint (matches, no #418).
  if (!mounted) {
    return <p style={{ fontSize: "0.9rem", color: "var(--color-ink-muted)" }}>Loading…</p>;
  }

  if (!session) {
    return (
      <p style={{ fontSize: "0.9rem" }}>
        Please{" "}
        <Link href="/login" style={{ fontWeight: 500 }}>
          sign in
        </Link>{" "}
        to use the Workbench.
      </p>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <nav role="tablist" aria-label="Workbench sections" style={{ display: "flex", gap: "0.3rem", flexWrap: "wrap", borderBottom: "1px solid var(--color-border)" }}>
        {tabs.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            style={{
              padding: "0.5rem 0.9rem",
              border: "none",
              borderBottom: tab === t.key ? "2px solid var(--color-accent)" : "2px solid transparent",
              background: "none",
              cursor: "pointer",
              fontSize: "0.85rem",
              fontWeight: tab === t.key ? 600 : 400,
              color: tab === t.key ? "var(--color-ink)" : "var(--color-ink-muted)",
            }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div>
        {tab === "bench" && <BenchDashboard advisorId={session.consultantId} />}
        {tab === "certification" && <CertificationPanel advisorId={session.consultantId} />}
        {tab === "learning" && <LearningDrillsPanel />}
        {tab === "arena" && <ArenaPanel />}
        {tab === "calibration" && <CalibrationPanel />}
        {tab === "requests" && <RatingRequestsPanel />}
        {tab === "committee" && session.isCommittee && <CommitteePanel />}
      </div>
    </div>
  );
}
