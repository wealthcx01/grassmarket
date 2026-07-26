/**
 * Registry contacts for a prospect's institution (GRS-0193, ADR-0045).
 *
 * The prospect record is the advisor's own; this panel shows what the SHARED imported registry
 * knows about the same institution, which is a different thing with different scoping. The two are
 * kept visually distinct for that reason: nothing here is the advisor's data, and nothing here is
 * editable from the prospect.
 *
 * The institution is resolved through the same entity search the wizard uses, so a company that has
 * not been imported says exactly that rather than rendering an empty contact list, which would read
 * as the false claim that nobody works there.
 */

"use client";

import { useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import type { CompanyEntity, RegistryContact } from "@/lib/types";

type State =
  | { kind: "loading" }
  | { kind: "unmatched" }
  | { kind: "error"; message: string }
  | { kind: "matched"; entity: CompanyEntity; contacts: RegistryContact[] };

export function RegistryContactsPanel({ companyName }: { companyName: string }) {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    const signal = controller.signal;
    setState({ kind: "loading" });
    api
      .searchEntities(companyName, signal)
      .then(async (candidates) => {
        const entity = candidates[0];
        // Only an exact name match is treated as this institution. A ranked near-miss would
        // attach one firm's people to another's record, which is worse than showing nothing.
        if (!entity || entity.name.toLowerCase() !== companyName.trim().toLowerCase()) {
          setState({ kind: "unmatched" });
          return;
        }
        const contacts = await api.listRegistryContacts(entity.entity_id, signal);
        setState({ kind: "matched", entity, contacts });
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0 && err.aborted) return;
        // A 404 means the resolved entity is a seeded stub company with no imported rows behind
        // it, which is the unmatched case rather than a failure.
        if (err instanceof ApiError && err.status === 404) {
          setState({ kind: "unmatched" });
          return;
        }
        setState({
          kind: "error",
          message: err instanceof ApiError ? err.message : "Could not load registry contacts.",
        });
      });
    return () => controller.abort();
  }, [companyName]);

  return (
    <section className="card" style={{ padding: "1.15rem 1.3rem" }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: "0.75rem", flexWrap: "wrap" }}>
        <h2 style={{ margin: 0, fontSize: "1.05rem" }}>Registry contacts</h2>
        <span style={{ fontSize: "0.76rem", color: "var(--color-ink-faint)" }}>
          Shared across the network, not your own pipeline
        </span>
      </div>
      <Body state={state} companyName={companyName} />
    </section>
  );
}

function Body({ state, companyName }: { state: State; companyName: string }) {
  if (state.kind === "loading") {
    return <p style={{ margin: "0.75rem 0 0", color: "var(--color-ink-muted)", fontSize: "0.9rem" }}>Looking up {companyName}…</p>;
  }
  if (state.kind === "error") {
    return (
      <p className="callout callout-warn" style={{ marginTop: "0.75rem" }}>
        {state.message}
      </p>
    );
  }
  if (state.kind === "unmatched") {
    return (
      <p style={{ margin: "0.75rem 0 0", color: "var(--color-ink-muted)", fontSize: "0.9rem", lineHeight: 1.55 }}>
        {companyName} is not in the imported registry, so there is nothing to show here. This does
        not mean the institution has no contacts, only that it has not been imported.
      </p>
    );
  }
  if (state.contacts.length === 0) {
    return (
      <p style={{ margin: "0.75rem 0 0", color: "var(--color-ink-muted)", fontSize: "0.9rem", lineHeight: 1.55 }}>
        {state.entity.name} is in the registry, but no contacts have been imported for it yet.
      </p>
    );
  }
  return (
    <ul style={{ listStyle: "none", margin: "0.9rem 0 0", padding: 0, display: "grid", gap: "0.6rem" }}>
      {state.contacts.map((contact) => (
        <li
          key={contact.contact_id}
          style={{ display: "grid", gap: "0.2rem", paddingBottom: "0.6rem", borderBottom: "1px solid var(--color-border)" }}
        >
          <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", flexWrap: "wrap" }}>
            <span style={{ fontWeight: 600 }}>{contact.full_name}</span>
            {contact.verified ? (
              <span className="tag" style={{ fontSize: "0.66rem" }}>Verified</span>
            ) : (
              <span
                className="tag"
                style={{ fontSize: "0.66rem", color: "var(--color-ink-soft)" }}
                title="Imported but not confirmed by a person against a named source."
              >
                Unverified
              </span>
            )}
          </div>
          {contact.job_role ? (
            <span style={{ fontSize: "0.88rem", color: "var(--color-ink-muted)" }}>{contact.job_role}</span>
          ) : null}
          <div style={{ display: "flex", gap: "0.9rem", flexWrap: "wrap", fontSize: "0.82rem", color: "var(--color-ink-soft)" }}>
            {contact.email ? <span>{contact.email}</span> : null}
            {contact.phone ? <span>{contact.phone}</span> : null}
            {contact.linkedin ? (
              <a href={contact.linkedin} target="_blank" rel="noopener noreferrer">
                LinkedIn
              </a>
            ) : null}
          </div>
          <span className="mono" style={{ fontSize: "0.7rem", color: "var(--color-ink-faint)" }}>
            {contact.source} · imported {contact.imported_on}
          </span>
        </li>
      ))}
    </ul>
  );
}
