/**
 * Explains a bad-id bounce (GRS-0172). Detail pages redirect an unknown/malformed id back to
 * their list (GRS-0143) — silently, which personas read as a "mystery redirect". The bounce now
 * carries `?notfound=1`; this notice says what happened, then strips the flag so a refresh or
 * bookmark doesn't re-trigger it.
 */

"use client";

import { useEffect, useState } from "react";

export function NotFoundNotice({ noun }: { noun: string }) {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("notfound")) {
      setShow(true);
      params.delete("notfound");
      const q = params.toString();
      window.history.replaceState(null, "", window.location.pathname + (q ? `?${q}` : ""));
    }
  }, []);
  if (!show) return null;
  return (
    <p
      role="status"
      className="callout callout-warn"
      style={{ display: "flex", justifyContent: "space-between", gap: "0.75rem", alignItems: "baseline", fontSize: "0.85rem", margin: 0 }}
    >
      <span>
        That {noun} doesn&rsquo;t exist or isn&rsquo;t in your book — you&rsquo;re back at the
        list.
      </span>
      <button
        type="button"
        className="btn btn-ghost"
        style={{ padding: "0.15rem 0.5rem", fontSize: "0.75rem" }}
        onClick={() => setShow(false)}
      >
        Dismiss
      </button>
    </p>
  );
}
