/**
 * An advisor's level, and whether they earned it (GRS-0242 scope 3).
 *
 * One component, used by both Bench and the Certification ladder, because the bug this fixes was
 * the two tabs describing the same person differently: Bench reported "Level: certified lead" as
 * bare fact while the ladder beside it showed no coursework, no exam and no shadow assessments.
 *
 * The level is not hidden or corrected downward. An administrator may legitimately grant one, and
 * silently demoting it on screen would be its own lie. What changes is that a level the evidence
 * does not support **says so**, in words, next to itself.
 */

import { LEVEL_LABEL } from "@/lib/levels";
import type { AssessorLevelValue } from "@/lib/types";

export function LevelBadge({
  level,
  earnedLevel,
  isEvidenced,
}: {
  level: AssessorLevelValue;
  earnedLevel: AssessorLevelValue;
  isEvidenced: boolean;
}) {
  if (isEvidenced) return <>{LEVEL_LABEL[level]}</>;
  return (
    <span>
      {LEVEL_LABEL[level]}{" "}
      <span
        style={{ color: "var(--color-warn)", fontSize: "0.78rem", whiteSpace: "nowrap" }}
        title={`The ladder evidence on record supports ${LEVEL_LABEL[earnedLevel]}.`}
      >
        · set outside the ladder
      </span>
    </span>
  );
}

/**
 * The sentence shown under the ladder when a level was granted rather than earned. Says what the
 * evidence actually supports, so the reader is not left to work out which of two screens is wrong.
 */
export function LevelProvenanceNote({
  level,
  earnedLevel,
  isEvidenced,
}: {
  level: AssessorLevelValue;
  earnedLevel: AssessorLevelValue;
  isEvidenced: boolean;
}) {
  if (isEvidenced) return null;
  return (
    <p
      style={{
        margin: "0.5rem 0 0",
        padding: "0.5rem 0.7rem",
        border: "1px solid var(--color-warn)",
        background: "var(--color-warn-tint)",
        borderRadius: "var(--radius)",
        fontSize: "0.8rem",
        lineHeight: 1.5,
      }}
    >
      You are marked as <strong>{LEVEL_LABEL[level]}</strong>, which was set outside the ladder
      rather than earned through it. The evidence recorded here supports{" "}
      <strong>{LEVEL_LABEL[earnedLevel]}</strong>. Both are true; this note is here so the two do
      not look like a mistake.
    </p>
  );
}
