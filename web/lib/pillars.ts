import type { Pillar } from "./types";

/**
 * Mental Model:
 *   The four pillars of Sophia's mind, each with one accent colour. The CSS
 *   already defines --pillar-<id> variables; this module is the single place
 *   that knows the canonical order and labels, and how to hand a pillar's
 *   colour to a component via the `--p` custom property (e.g. a source chip
 *   or a corpus document inherits its pillar's hue).
 */

export const PILLARS: { id: Pillar; label: string }[] = [
  { id: "mind", label: "Mind" },
  { id: "philosophy", label: "Philosophy" },
  { id: "science", label: "Science" },
  { id: "spirit", label: "Spirit" },
];

/** A style object that sets --p to the given pillar's accent colour. */
export function pillarVar(pillar: string): React.CSSProperties {
  return { ["--p" as string]: `var(--pillar-${pillar})` } as React.CSSProperties;
}
