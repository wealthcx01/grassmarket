import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { RETIRED_COPY } from "@/lib/retiredCopy";

/**
 * The mechanism GRS-0243 scope 1 asks for: the two sentences the founder retired cannot come back.
 *
 * They were flagged on 26/07, survived a full copy sweep (GRS-0174), and were still on the home
 * page verbatim on 31/07. Rewriting copy is easy; keeping it rewritten is what failed, because a
 * sentence carries no record of having been objected to. This test is that record.
 */

const ROOTS = ["app", "components", "lib"];
const EXTENSIONS = [".tsx", ".ts"];
// This file and the register itself quote the retired phrases on purpose.
const EXEMPT = ["retiredCopy.ts", "retiredCopy.test.ts"];

function sourceFiles(dir: string): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    if (name === "node_modules" || name === ".next") continue;
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      out.push(...sourceFiles(full));
    } else if (EXTENSIONS.some((e) => name.endsWith(e)) && !EXEMPT.includes(name)) {
      out.push(full);
    }
  }
  return out;
}

/** JSX wraps text at arbitrary points, so both haystack and needle are flattened before compare. */
function normalise(text: string): string {
  return text.replace(/\s+/g, " ").replace(/[""]/g, '"').replace(/['']/g, "'");
}

describe("retired copy (GRS-0243)", () => {
  const files = ROOTS.flatMap((root) => sourceFiles(root));

  it("scans a real source tree, not an empty one", () => {
    // Without this, a broken glob would make every assertion below pass vacuously — which is the
    // failure mode of every "nothing matched" test.
    expect(files.length).toBeGreaterThan(50);
  });

  it.each(RETIRED_COPY)("$where — the retired wording is gone", ({ phrase, why }) => {
    const needle = normalise(phrase);
    const offenders = files.filter((file) => normalise(readFileSync(file, "utf8")).includes(needle));
    expect(
      offenders,
      `This wording was retired and has come back.\n\nWhy it was rejected: ${why}\n\nFound in: ${offenders.join(", ")}`,
    ).toEqual([]);
  });

  it("every entry says why, not just what", () => {
    // A register of banned strings with no reasons teaches the next author nothing, and they will
    // write a new sentence with the same problem.
    for (const entry of RETIRED_COPY) {
      expect(entry.why.length).toBeGreaterThan(40);
      expect(entry.where.length).toBeGreaterThan(0);
    }
  });
});
