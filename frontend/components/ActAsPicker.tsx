"use client";

/**
 * The control that STARTS an act-as session (GRS-0208 scope 2).
 *
 * The mechanism shipped without one: the API, the narrowing, the audit and the exit banner all
 * existed, and the only way to begin was an API call. A capability an admin cannot reach from the
 * browser is a capability they do not have, so this is the missing half rather than a nicety.
 *
 * Two deliberate choices:
 *
 * - **It lives in the account menu, not in a settings page.** Acting as someone is a change to who
 *   you are for the next few minutes, and the account menu is where a person looks to see and change
 *   who they are signed in as.
 * - **It names what will happen before it happens.** The confirmation says the session is recorded
 *   against both accounts, because an admin who does not know that will eventually write something
 *   as an advisor and be surprised later. The banner says it again once the session starts; saying
 *   it twice is cheap and the surprise is not.
 */

import { useCallback, useEffect, useState } from "react";

import { ApiError, api, getRefreshToken, setTokens } from "@/lib/api";
import type { Consultant } from "@/lib/types";

export function ActAsPicker({ onClose }: { onClose: () => void }) {
  const [candidates, setCandidates] = useState<Consultant[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      setCandidates(await api.actAsCandidates(signal));
    } catch (err) {
      if (err instanceof ApiError && err.aborted) return;
      setError(err instanceof ApiError ? err.message : "Could not load the advisor list.");
    }
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    void load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  const start = async (consultant: Consultant) => {
    setBusy(consultant.id);
    setError(null);
    try {
      const started = await api.startActingAs(consultant.id);
      setTokens(started.access_token, getRefreshToken() ?? "");
      // Full reload, for the same reason stopping does one: every mounted page was rendered against
      // the admin's scope, and refreshing piecemeal would leave their data on screen beside the
      // advisor's.
      window.location.assign("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start the session.");
      setBusy(null);
    }
  };

  return (
    <div className="act-as-picker" role="dialog" aria-label="View as another advisor">
      <p className="act-as-picker-lede">
        Open a session scoped to one advisor and see exactly what they see. Everything you do is
        recorded against their account <strong>and yours</strong>.
      </p>
      {error ? (
        <p role="alert" className="act-as-picker-error">
          {error}
        </p>
      ) : null}
      {candidates === null && !error ? <p>Loading…</p> : null}
      {candidates !== null && candidates.length === 0 ? (
        <p>There is no one else to view as.</p>
      ) : null}
      <ul className="act-as-picker-list">
        {(candidates ?? []).map((c) => (
          <li key={c.id}>
            <button type="button" onClick={() => void start(c)} disabled={busy !== null}>
              <span className="act-as-name">{c.full_name}</span>
              <span className="act-as-email">{c.email}</span>
            </button>
          </li>
        ))}
      </ul>
      <button type="button" className="act-as-picker-cancel" onClick={onClose}>
        Cancel
      </button>
    </div>
  );
}
