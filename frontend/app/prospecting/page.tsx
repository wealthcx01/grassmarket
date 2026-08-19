"use client";

/**
 * Prospecting — browse the imported universe (GRS-0238).
 *
 * The founder said twice that they could not see prospective clients from the bcap database. They
 * were right: the only ways in were entity search (which needs a name you already know) and a
 * per-prospect panel that needs the prospect to exist first. This page is the missing front door.
 *
 * Three decisions here are about honesty rather than layout, and each one is measured rather than
 * assumed (evidence in `docs/reviews/GRS-0238-prospecting-surface/`):
 *
 * 1. **Segments are grouped by KIND.** The stored column mixes what a firm IS ("Bank",
 *    "Sell-side research house") with what a supplier SUPPLIES ("Data", "Indices", "Fixings"),
 *    because two import sources filled one column from two different spreadsheet fields. Listing
 *    them flat would tell an advisor they are alternatives of one kind. They are not.
 * 2. **Unverified names are marked, never replaced.** 128 institutions arrived named after their
 *    domain stem — `gs`, `db`, `citi`, and from broken source rows `uk` and `us`. The row shows the
 *    stem and says the name is unverified. It does NOT render "Goldman Sachs", because that is a
 *    guess and a guess shown without a mark is indistinguishable from a fact.
 * 3. **It is not a CRM.** Read, filter, and claim as a prospect. No outreach, no sequencing, no
 *    contact editing — GRS-0207 owns that decision and this page must not pre-empt it.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError, api, getToken } from "@/lib/api";
import type { ProspectingTarget, RegistryFacets, SegmentFacet } from "@/lib/types";

const PAGE_SIZE = 25;

/** Firm types first: they are the filter an advisor actually prospects on. */
function groupSegments(facets: SegmentFacet[]): { title: string; items: SegmentFacet[] }[] {
  const of = (kind: string) => facets.filter((f) => f.kind === kind);
  return [
    { title: "Kind of firm", items: of("firm_type") },
    { title: "What they supply", items: of("content_type") },
    { title: "Unclassified", items: of("unknown") },
  ].filter((g) => g.items.length > 0);
}

export default function ProspectingPage() {
  const router = useRouter();
  const [facets, setFacets] = useState<RegistryFacets | null>(null);
  const [rows, setRows] = useState<ProspectingTarget[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [segment, setSegment] = useState<string>("");
  const [country, setCountry] = useState<string>("");
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  useEffect(() => {
    const controller = new AbortController();
    api
      .registryFacets(controller.signal)
      .then(setFacets)
      .catch(() => setFacets(null));
    return () => controller.abort();
  }, []);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      try {
        const page = await api.listRegistryTargets(
          { segment: segment || undefined, country: country || undefined, q: q || undefined, offset, limit: PAGE_SIZE },
          signal,
        );
        setRows(page.targets);
        setTotal(page.total);
      } catch (err) {
        if ((err as Error)?.name === "AbortError") return;
        setError(err instanceof ApiError ? err.message : "Could not load the registry.");
      } finally {
        setLoading(false);
      }
    },
    [segment, country, q, offset],
  );

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const groups = useMemo(() => groupSegments(facets?.segments ?? []), [facets]);

  const claim = async (target: ProspectingTarget) => {
    setClaiming(target.target_id);
    setError(null);
    try {
      await api.createProspect({
        company_name: target.name,
        website: target.domain ? `https://${target.domain}` : null,
        registry_target_id: target.target_id,
      });
      // Reflect the claim without a full reload — the row's own state is the only thing that moved.
      setRows((current) =>
        current.map((r) =>
          r.target_id === target.target_id ? { ...r, already_in_my_pipeline: true } : r,
        ),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add this firm to your pipeline.");
    } finally {
      setClaiming(null);
    }
  };

  return (
    <main className="container" style={{ paddingBottom: "3rem" }}>
      <header style={{ margin: "1.5rem 0 1rem" }}>
        <h1 style={{ margin: 0 }}>Prospecting</h1>
        <p style={{ margin: "0.4rem 0 0", color: "var(--color-ink-muted)", maxWidth: "48rem" }}>
          Every institution the network has imported, with the people we know there. Claim one and
          it becomes a prospect in your pipeline. Nothing here contacts anybody.
        </p>
      </header>

      <section
        aria-label="Filters"
        style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", margin: "1rem 0" }}
      >
        <label style={{ display: "flex", flexDirection: "column", fontSize: "0.8rem" }}>
          Search
          <input
            type="search"
            value={q}
            placeholder="Name contains…"
            onChange={(e) => {
              setOffset(0);
              setQ(e.target.value);
            }}
          />
        </label>

        <label style={{ display: "flex", flexDirection: "column", fontSize: "0.8rem" }}>
          Segment
          <select
            value={segment}
            onChange={(e) => {
              setOffset(0);
              setSegment(e.target.value);
            }}
          >
            <option value="">All segments</option>
            {/* Grouped, because "Bank" and "Supplies: indices" answer different questions. */}
            {groups.map((group) => (
              <optgroup key={group.title} label={group.title}>
                {group.items.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label} ({s.count})
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </label>

        <label style={{ display: "flex", flexDirection: "column", fontSize: "0.8rem" }}>
          Country
          <select
            value={country}
            onChange={(e) => {
              setOffset(0);
              setCountry(e.target.value);
            }}
          >
            <option value="">All countries</option>
            {(facets?.countries ?? []).map((c) => (
              <option key={c.value} value={c.value}>
                {c.value} ({c.count})
              </option>
            ))}
          </select>
        </label>
      </section>

      {error ? (
        <p role="alert" className="hint" style={{ color: "var(--color-danger, #a33)" }}>
          {error}
        </p>
      ) : null}

      <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }} data-testid="result-count">
        {loading
          ? "Loading…"
          : total === 0
            ? "No institutions match these filters."
            : `${total.toLocaleString()} institution${total === 1 ? "" : "s"}`}
      </p>

      {rows.length ? (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th scope="col" style={{ textAlign: "left" }}>Institution</th>
              <th scope="col" style={{ textAlign: "left" }}>Segment</th>
              <th scope="col" style={{ textAlign: "left" }}>Country</th>
              <th scope="col" style={{ textAlign: "left" }}>Contacts</th>
              <th scope="col" style={{ textAlign: "left" }}>Imported</th>
              <th scope="col" />
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.target_id} style={{ borderTop: "1px solid var(--color-border)" }}>
                <td>
                  <span style={{ fontWeight: 600 }}>{t.name}</span>
                  {t.domain ? (
                    <span style={{ color: "var(--color-ink-muted)", fontSize: "0.8rem" }}>
                      {" "}
                      {t.domain}
                    </span>
                  ) : null}
                  {/* Marked, not replaced. Rendering a guessed company name here would be the
                      fabrication the whole codebase refuses. */}
                  {t.name_unverified ? (
                    <span
                      className="badge badge-warn"
                      data-testid="name-unverified"
                      title="Imported from a data feed that stored the domain stem instead of the company name. Nobody has verified what this firm is called."
                    >
                      name unverified
                    </span>
                  ) : null}
                </td>
                <td>{t.segment_label}</td>
                <td>{t.country ?? "—"}</td>
                <td>{t.contact_count || "—"}</td>
                <td style={{ color: "var(--color-ink-muted)", fontSize: "0.8rem" }}>
                  {t.source} · {t.imported_on}
                </td>
                <td style={{ textAlign: "right" }}>
                  {t.already_in_my_pipeline ? (
                    <span style={{ color: "var(--color-ink-muted)", fontSize: "0.8rem" }}>
                      In your pipeline
                    </span>
                  ) : (
                    <button
                      type="button"
                      className="btn btn-ghost"
                      disabled={claiming === t.target_id}
                      onClick={() => claim(t)}
                    >
                      {claiming === t.target_id ? "Adding…" : "Add to pipeline"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}

      {total > PAGE_SIZE ? (
        <nav
          aria-label="Pagination"
          style={{ display: "flex", gap: "1rem", alignItems: "center", marginTop: "1rem" }}
        >
          <button
            type="button"
            className="btn btn-ghost"
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
          >
            Previous
          </button>
          <span style={{ fontSize: "0.85rem", color: "var(--color-ink-muted)" }}>
            {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total.toLocaleString()}
          </span>
          <button
            type="button"
            className="btn btn-ghost"
            disabled={offset + PAGE_SIZE >= total}
            onClick={() => setOffset(offset + PAGE_SIZE)}
          >
            Next
          </button>
        </nav>
      ) : null}
    </main>
  );
}
