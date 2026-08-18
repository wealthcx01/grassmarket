"use client";

/**
 * The persistent "you are viewing someone else's account" banner (GRS-0208 scope 2).
 *
 * The ticket's word is act-as, *not* impersonate-silently, and this component is most of the
 * difference between the two. An admin who forgets they are acting as an advisor will read that
 * advisor's pipeline as their own, and — worse — will *write* as them without noticing. So the
 * banner is:
 *
 * - **always on screen**, fixed rather than scrolled away, for the same reason the non-production
 *   report mark is (GRS-0229): a warning visible only at the top of a long page is a warning that
 *   is absent from the second screen onwards;
 * - **naming the advisor**, because "acting as another user" tells an admin nothing they can act on;
 * - **one click back**, because a state you cannot leave easily is a state people stay in.
 *
 * It reads the session claim rather than asking the server on every render: the claim is signed and
 * cannot be forged, and the server is the actual boundary regardless — this is a mirror of what the
 * API will already enforce, never a gate of its own.
 */

import { useCallback, useEffect, useState } from "react";

import { ApiError, api, getRefreshToken, setTokens } from "@/lib/api";
import { getSession } from "@/lib/session";

export function ActingAsBanner() {
  const [subject, setSubject] = useState<{ name: string; email: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const session = getSession();
    if (!session?.actingAsConsultantId) {
      setSubject(null);
      return;
    }
    try {
      // Ask who this session is, rather than trusting a name passed through the client. The
      // endpoint answers as the SUBJECT while acting-as, which is exactly the name to display.
      const me = await api.me();
      setSubject({ name: me.full_name, email: me.email });
    } catch {
      // A name we cannot fetch must not silence the banner — the dangerous state is the invisible
      // one, so fall back to saying so without a name.
      setSubject({ name: "another advisor", email: "" });
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const stop = async () => {
    setBusy(true);
    setError(null);
    try {
      const back = await api.stopActingAs();
      // Keep the existing refresh token: the admin's original login issued it, and
      // stopping act-as returns them to that same session rather than starting a new one.
      setTokens(back.access_token, getRefreshToken() ?? "");
      // A full reload rather than a router refresh: every page in the app was rendered against the
      // other advisor's scope, and re-fetching piecemeal would leave their data on screen beside
      // yours. Cheap, and unambiguous.
      window.location.assign("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not stop acting as this advisor.");
      setBusy(false);
    }
  };

  if (!subject) return null;

  return (
    <div className="acting-as-banner" role="status" data-testid="acting-as-banner">
      <span>
        Viewing as <strong>{subject.name}</strong>
        {subject.email ? ` (${subject.email})` : ""} — anything you do here is recorded against
        their account and yours.
      </span>
      <button type="button" onClick={stop} disabled={busy}>
        {busy ? "Stopping…" : "Stop viewing as them"}
      </button>
      {error ? <span className="acting-as-error">{error}</span> : null}
    </div>
  );
}
