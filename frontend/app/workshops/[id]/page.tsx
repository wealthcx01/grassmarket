/**
 * Workshop detail (GRS-0014): schedule → deliver, then attribute a recovery fee. The recovery fee is
 * shown straight from the API's `Money` (currency + amount) via MoneyAmount — never recomputed or
 * combined client-side. Eligibility is the backend's call: an out-of-window attribution returns 409
 * and the UI surfaces the reason.
 */

"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

import { MoneyAmount } from "@/components/MoneyAmount";
import { ApiError, api, getToken } from "@/lib/api";
import type { RecoveryFeeAttribution, Workshop } from "@/lib/types";

export default function WorkshopDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [workshop, setWorkshop] = useState<Workshop | null>(null);
  const [fee, setFee] = useState<RecoveryFeeAttribution | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(
    (signal?: AbortSignal) =>
      Promise.all([api.getWorkshop(id, signal), api.listRecoveryFees(signal)])
        .then(([w, fees]) => {
          setWorkshop(w);
          setFee(fees.find((f) => f.workshop_id === id) ?? null);
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0) return;
          // 404/422 (missing or malformed id) → not a real record; bounce to the pipeline rather than
          // leak a raw "Request failed (422)" (GRS-0143b).
          if (err instanceof ApiError && (err.status === 404 || err.status === 422))
            return router.replace("/pipeline");
          setError(err instanceof ApiError ? err.message : "Could not load the workshop.");
        }),
    [id, router],
  );

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    reload(ctrl.signal);
    return () => ctrl.abort();
  }, [router, reload]);

  if (error) return <p style={{ color: "var(--color-error)" }}>{error}</p>;
  if (!workshop) return <p>Loading…</p>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem", maxWidth: "42rem" }}>
      <div>
        <Link href={`/prospects/${workshop.prospect_id}`} style={{ fontSize: "0.8rem" }}>
          ← Prospect
        </Link>
        <h1 style={{ fontSize: "1.5rem", margin: "0.2rem 0 0.3rem" }}>Workshop</h1>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>
          State <strong>{workshop.state}</strong>
          {workshop.scheduled_for ? ` · scheduled ${workshop.scheduled_for}` : ""}
          {workshop.delivered_on ? ` · delivered ${workshop.delivered_on}` : ""}
        </p>
      </div>

      {workshop.pre_workshop_brief ? (
        <Card label="Pre-workshop brief">{workshop.pre_workshop_brief}</Card>
      ) : null}
      {workshop.workshop_output ? <Card label="Workshop output">{workshop.workshop_output}</Card> : null}

      {workshop.state === "scheduled" ? (
        <DeliverForm workshopId={id} onDone={reload} />
      ) : (
        <RecoveryFeeSection workshopId={id} fee={fee} onDone={reload} />
      )}
    </div>
  );
}

function Card({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius)", padding: "0.7rem 0.9rem", background: "var(--color-paper-raised)" }}>
      <div className="mono" style={{ fontSize: "0.66rem", letterSpacing: "0.06em", color: "var(--color-ink-muted)", marginBottom: "0.3rem" }}>
        {label.toUpperCase()}
      </div>
      <div style={{ fontSize: "0.88rem", whiteSpace: "pre-wrap" }}>{children}</div>
    </div>
  );
}

function DeliverForm({ workshopId, onDone }: { workshopId: string; onDone: () => Promise<unknown> }) {
  const [deliveredOn, setDeliveredOn] = useState("");
  const [output, setOutput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function deliver(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.deliverWorkshop(workshopId, {
        delivered_on: deliveredOn,
        workshop_output: output || null,
      });
      await onDone();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not deliver the workshop.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={deliver} style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      <h2 style={{ fontSize: "1.05rem", margin: 0 }}>Deliver workshop</h2>
      <label style={labelStyle}>
        Delivered on
        <input type="date" required value={deliveredOn} onChange={(e) => setDeliveredOn(e.target.value)} style={inputStyle} />
      </label>
      <label style={labelStyle}>
        Workshop output
        <textarea rows={3} value={output} onChange={(e) => setOutput(e.target.value)} style={inputStyle} />
      </label>
      <button type="submit" className="btn btn-primary" disabled={busy || !deliveredOn}>
        Mark delivered
      </button>
      {error ? <p style={{ color: "var(--color-error)", fontSize: "0.8rem" }}>{error}</p> : null}
    </form>
  );
}

function RecoveryFeeSection({
  workshopId,
  fee,
  onDone,
}: {
  workshopId: string;
  fee: RecoveryFeeAttribution | null;
  onDone: () => Promise<unknown>;
}) {
  const [contractedOn, setContractedOn] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function attribute(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.attributeRecoveryFee(workshopId, contractedOn);
      await onDone();
    } catch (err: unknown) {
      // Outside the window (or already attributed) → 409; surface the backend's reason.
      setError(err instanceof ApiError ? err.message : "Could not attribute the recovery fee.");
    } finally {
      setBusy(false);
    }
  }

  if (fee) {
    return (
      <div style={{ border: "1px solid var(--color-accent)", borderRadius: "var(--radius)", padding: "0.9rem 1rem", background: "var(--color-paper-raised)" }}>
        <h2 style={{ fontSize: "1.05rem", margin: "0 0 0.4rem" }}>Recovery fee attributed</h2>
        <p style={{ margin: 0, fontSize: "1.4rem" }}>
          <MoneyAmount money={fee.fee} />
        </p>
        <p style={{ margin: "0.4rem 0 0", fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
          Prospect contracted {fee.contracted_on}, within the {fee.window_days}-day window from
          delivery {fee.delivered_on}. Rate {fee.rate_ref}.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={attribute} style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      <h2 style={{ fontSize: "1.05rem", margin: 0 }}>Recovery-fee eligibility</h2>
      <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "0.82rem" }}>
        If the prospect contracts within the attribution window, a recovery fee is due. Enter the
        contract date — the backend checks eligibility and computes the fee.
      </p>
      <label style={labelStyle}>
        Contracted on
        <input type="date" required value={contractedOn} onChange={(e) => setContractedOn(e.target.value)} style={inputStyle} />
      </label>
      <button type="submit" className="btn btn-primary" disabled={busy || !contractedOn}>
        Check &amp; attribute fee
      </button>
      {error ? <p role="alert" style={{ color: "var(--color-warn)", fontSize: "0.82rem" }}>{error}</p> : null}
    </form>
  );
}

const labelStyle: React.CSSProperties = { display: "flex", flexDirection: "column", gap: "0.25rem", fontSize: "0.82rem" };
// Controls inherit the global form styling; only the size is nudged here.
const inputStyle: React.CSSProperties = {
  fontSize: "0.85rem",
};
