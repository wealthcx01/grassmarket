/**
 * The client report's sections: their order, and the titles a reader actually sees (GRS-0235).
 *
 * **This is the frontend's only copy.** It mirrors `bcap_contracts.client_report.SECTION_TITLES`,
 * which is authoritative — schemas win on conflict (CLAUDE.md non-negotiable #4). Before this
 * module the same six pairs were hand-copied into three places (`SharedReport.tsx`, the report
 * editor page, and a test that then asserted against its own copy rather than the product's). They
 * happened to agree; nothing made them agree, and a test comparing a copy to a copy would have gone
 * on passing after either drifted.
 *
 * `tests/test_report_section_titles_mirror.py` fails if this file and the contract disagree, so the
 * mirror is checked by the side that owns the truth rather than trusted.
 */

/** Section keys in the order a client reads them — the same order the PDF and the web page use. */
export const SECTION_ORDER = [
  "business",
  "advantage",
  "constraint",
  "actions",
  "value",
  "appendix",
] as const;

export type ReportSectionKey = (typeof SECTION_ORDER)[number];

/** Reader-facing titles. Mirrors `bcap_contracts.client_report.SECTION_TITLES` exactly. */
export const SECTION_TITLES: Record<string, string> = {
  business: "The business",
  advantage: "Where the advantage sits",
  constraint: "What is holding it back",
  actions: "What to do about it",
  value: "What that is worth",
  appendix: "Technical appendix",
};

/**
 * The title for a section key, falling back to the key itself.
 *
 * The fallback is deliberate and it is *not* a silent default: a key with no title is a registry
 * bug, and showing the raw key makes it visible in the place it broke rather than hiding it behind
 * a plausible-looking blank. GRS-0231 shipped a raw `retail` key to staging by exactly the opposite
 * reasoning, so the rule here is that unknown input stays legible, never invisible.
 */
export function sectionTitle(key: string): string {
  return SECTION_TITLES[key] ?? key;
}
