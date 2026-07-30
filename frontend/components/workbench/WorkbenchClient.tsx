"use client";

/**
 * The Workbench (GRS-0027, PRD §6) — one coherent surface over the Loop 5 APIs: the bench-time
 * dashboard, certification, learning + drills, and the practice arena.
 *
 * Calibration, rating requests and the Rating Committee were retired here under ADR-0041. They were
 * built for a network larger than this one; the founder signs what goes out instead. Their panels
 * and routes are dormant rather than deleted, so the decision is reversible.
 *
 * The Founder review tab is mounted by ASKING the server: if the queue answers, the caller is the
 * reviewer. That keeps one authority for who the founder is, rather than baking a second copy of
 * their identity into the frontend build.
 */

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { getSession } from "@/lib/session";
import { BenchDashboard } from "@/components/workbench/BenchDashboard";
import { CertificationPanel } from "@/components/workbench/CertificationPanel";
import { FounderReviewPanel } from "@/components/workbench/FounderReviewPanel";
import { LearningDrillsPanel } from "@/components/workbench/LearningDrillsPanel";
import { ArenaPanel } from "@/components/workbench/ArenaPanel";
import { api } from "@/lib/api";

type TabKey = "bench" | "certification" | "learning" | "arena" | "founder-review";

export function WorkbenchClient() {
  // The session comes from localStorage, which the server can't read — reading it during render
  // makes the first client paint diverge from the server HTML (hydration mismatch, React #418).
  // Gate on `mounted` so the server and first client render agree, then read it after mount.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const session = useMemo(() => (mounted ? getSession() : null), [mounted]);

  // Ask the server whether this caller is the founder reviewer, rather than deriving it here. A
  // 403 is the expected answer for everyone else and is not an error worth surfacing.
  const [isReviewer, setIsReviewer] = useState(false);
  useEffect(() => {
    if (!mounted || !session) return;
    const ctrl = new AbortController();
    api
      .founderReviewQueue(ctrl.signal)
      .then(() => setIsReviewer(true))
      .catch(() => undefined);
    return () => ctrl.abort();
  }, [mounted, session]);

  const tabs = useMemo(() => {
    const base: { key: TabKey; label: string }[] = [
      { key: "bench", label: "Bench" },
      { key: "certification", label: "Certification" },
      { key: "learning", label: "Learning & Drills" },
      { key: "arena", label: "Practice Arena" },
    ];
    if (isReviewer) base.push({ key: "founder-review", label: "Founder review" });
    return base;
  }, [isReviewer]);
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
        {tab === "founder-review" && isReviewer && <FounderReviewPanel />}
      </div>
    </div>
  );
}
