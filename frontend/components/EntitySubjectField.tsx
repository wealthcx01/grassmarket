/**
 * Company lookup for the assessment subject (GRS-0100, ADR-0033). As the advisor types, it proposes
 * canonical companies from the registry; picking one resolves the subject to a stable `entity_id`
 * (and shows how many assessments they already have of that company — dedup made visible). Typing a
 * name the registry doesn't cover is the explicit manual fallback: the field stays "unlinked" and no
 * id is stored. Nothing is auto-resolved — an ambiguous query just lists the candidates.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, api } from "@/lib/api";
import type { CompanyEntity } from "@/lib/types";

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.55rem 0.7rem",
  fontFamily: "inherit",
  fontSize: "0.95rem",
  color: "var(--color-ink)",
  background: "var(--color-paper-raised)",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius)",
};

export function EntitySubjectField({
  value,
  entityId,
  onChange,
}: {
  value: string;
  entityId: string | null;
  /** Report the subject text and the resolved entity id (null = manual/unlinked). */
  onChange: (subject: string, entityId: string | null) => void;
}) {
  const [results, setResults] = useState<CompanyEntity[]>([]);
  const [open, setOpen] = useState(false);
  const [linkedName, setLinkedName] = useState<string | null>(null);
  const [dedupCount, setDedupCount] = useState<number | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounced search whenever the (unlinked) text changes.
  const search = useCallback((q: string) => {
    if (timer.current) clearTimeout(timer.current);
    if (!q.trim()) {
      setResults([]);
      return;
    }
    timer.current = setTimeout(() => {
      api
        .searchEntities(q)
        .then((r) => {
          setResults(r);
          setOpen(r.length > 0);
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0) return;
          setResults([]);
        });
    }, 220);
  }, []);

  function onType(text: string) {
    // Typing detaches any existing link — the subject is manual until the advisor picks again.
    onChange(text, null);
    setLinkedName(null);
    setDedupCount(null);
    search(text);
  }

  function pick(e: CompanyEntity) {
    onChange(e.name, e.entity_id);
    setLinkedName(e.name);
    setOpen(false);
    setResults([]);
    // Surface the dedup: how many assessments the advisor already has of this company.
    api
      .assessmentsForEntity(e.entity_id)
      .then((a) => setDedupCount(a.length))
      .catch(() => setDedupCount(null));
  }

  useEffect(() => {
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  const linked = entityId !== null && linkedName !== null;

  return (
    <div style={{ position: "relative" }}>
      <input
        type="text"
        value={value}
        onChange={(e) => onType(e.target.value)}
        onFocus={() => setResults((r) => (r.length ? (setOpen(true), r) : r))}
        placeholder="Search a company — e.g. Revolut, Monzo, Interactive Brokers"
        role="combobox"
        aria-expanded={open}
        aria-controls="entity-subject-listbox"
        aria-autocomplete="list"
        aria-label="Subject company"
        autoComplete="off"
        style={inputStyle}
      />

      {open && results.length > 0 ? (
        <ul
          role="listbox"
          id="entity-subject-listbox"
          style={{
            position: "absolute",
            zIndex: 20,
            top: "calc(100% + 0.2rem)",
            left: 0,
            right: 0,
            listStyle: "none",
            margin: 0,
            padding: "0.25rem",
            background: "var(--color-paper-raised)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius)",
            boxShadow: "0 6px 18px rgba(0,0,0,0.14)",
            maxHeight: "14rem",
            overflowY: "auto",
          }}
        >
          {results.map((e) => (
            <li key={e.entity_id} role="option" aria-selected={false}>
              <button
                type="button"
                onClick={() => pick(e)}
                style={{
                  display: "flex",
                  width: "100%",
                  justifyContent: "space-between",
                  alignItems: "baseline",
                  gap: "0.6rem",
                  padding: "0.4rem 0.5rem",
                  background: "none",
                  border: "none",
                  borderRadius: "var(--radius)",
                  cursor: "pointer",
                  color: "inherit",
                  font: "inherit",
                  textAlign: "left",
                }}
              >
                <span style={{ fontWeight: 600 }}>{e.name}</span>
                {e.segment ? (
                  <span className="tag" style={{ fontSize: "0.6rem" }}>{e.segment}</span>
                ) : null}
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      <p style={{ margin: "0.35rem 0 0", fontSize: "0.72rem", color: linked ? "var(--color-accent)" : "var(--color-ink-faint)" }}>
        {linked ? (
          <>
            ✓ Linked to <strong>{linkedName}</strong>
            {dedupCount != null && dedupCount > 0
              ? ` · you have ${dedupCount} assessment${dedupCount === 1 ? "" : "s"} of this company`
              : ""}
          </>
        ) : value.trim() ? (
          "Unlinked — will be saved as a manual subject. Pick a company above to link it."
        ) : (
          "Type to find the company in the registry, or enter any name to keep it manual."
        )}
      </p>
    </div>
  );
}
