/**
 * Human-readable labels for internal keys.
 *
 * The scoring engine emits registry keys (e.g. `BACK_OFFICE`, `CORNERED_RESOURCE`,
 * `FRONTEND/FRONTEND_PERFORMANCE`) inside blocking/finalise messages. Those keys must never reach
 * an advisor's screen raw. These helpers turn them into prose and collapse the repetitive
 * dual-rating finalise message into one line.
 */

// Tokens that should stay upper-cased (or specially cased) rather than Title Cased.
const ACRONYMS: Record<string, string> = {
  UX: "UX",
  DR: "DR",
  API: "API",
  APIS: "APIs",
  KYC: "KYC",
  AML: "AML",
  CRM: "CRM",
  EMS: "EMS",
  OEMS: "OEMS",
  OEM: "OEM",
  SLO: "SLO",
  SLA: "SLA",
  FIX: "FIX",
  AI: "AI",
  CSD: "CSD",
  CCP: "CCP",
  STP: "STP",
  NAV: "NAV",
  TTM: "TTM",
  ARPU: "ARPU",
  ESG: "ESG",
};

function titleCaseToken(token: string): string {
  const up = token.toUpperCase();
  if (ACRONYMS[up]) return ACRONYMS[up];
  return token.charAt(0).toUpperCase() + token.slice(1).toLowerCase();
}

/**
 * Humanize a single registry key. Handles `MODULE/SUBCOMPONENT` pairs (dropping a redundant module
 * prefix on the subcomponent) and snake_case. e.g.
 *   "CORNERED_RESOURCE"                         -> "Cornered Resource"
 *   "BACK_OFFICE"                               -> "Back Office"
 *   "FRONTEND/FRONTEND_PERFORMANCE"             -> "Front End · Performance"
 *   "MARKET_DATA/MARKET_DATA_DEPTH_QUALITY"     -> "Market Data · Depth Quality"
 */
export function humanizeKey(key: string): string {
  const words = (s: string) =>
    s
      .split("_")
      .filter(Boolean)
      .map(titleCaseToken)
      .join(" ");

  if (key.includes("/")) {
    const [mod = "", sub = ""] = key.split("/");
    const modLabel = words(mod);
    // Drop a leading module prefix on the subcomponent ("FRONTEND_PERFORMANCE" under "FRONTEND").
    let subKey = sub;
    if (sub.toUpperCase().startsWith(mod.toUpperCase() + "_")) {
      subKey = sub.slice(mod.length + 1);
    }
    const subLabel = words(subKey);
    return subLabel ? `${modLabel} · ${subLabel}` : modLabel;
  }
  return words(key);
}

/** Replace every ALL_CAPS registry-key token inside a free-text string with its humanized label. */
export function humanizeKeysInText(text: string): string {
  return text.replace(/\b[A-Z][A-Z0-9]*(?:[_/][A-Z0-9]+)+\b/g, (m) => humanizeKey(m));
}

export interface BlockingSummary {
  /** One concise line if a repetitive pattern was collapsed, else null. */
  headline: string | null;
  /** The remaining, individually-meaningful reasons (humanized). */
  reasons: string[];
}

/**
 * Turn the raw blocking reasons (an array, or a single concatenated finalise-error string) into a
 * concise, human-readable summary. The dual-rating finalise message repeats
 * "<KEY> is solo-rated — Methodology §9 requires two independent raters..." once per subcomponent;
 * we collapse that to a single count instead of a wall of internal keys.
 */
export function summarizeBlocking(blocking: string[] | string | null | undefined): BlockingSummary {
  const raw = Array.isArray(blocking)
    ? blocking
    : typeof blocking === "string"
      ? blocking.split(/(?<=\.)\s+(?=[A-Z])/) // split the concatenated finalise detail on sentence boundaries
      : [];

  const soloPattern = /solo-rated/i;
  const solo = raw.filter((r) => soloPattern.test(r));
  const others = raw.filter((r) => !soloPattern.test(r)).map((r) => humanizeKeysInText(r).trim());

  let headline: string | null = null;
  if (solo.length > 0) {
    headline = `${solo.length} subcomponent${solo.length === 1 ? " is" : "s are"} solo-rated — each needs a second independent rater and a resolved consensus before finalising (Methodology §9).`;
  }

  return { headline, reasons: others.filter(Boolean) };
}
