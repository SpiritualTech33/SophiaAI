import type { SourceOut, WebResult } from "@/lib/types";

/**
 * Mental Model:
 *   The client-side view of a single message. It is richer than the wire
 *   MessageOut: it already carries parsed sources and (for a fresh answer) the
 *   web results and search mode from the stream's meta frame, plus transient
 *   flags for the streaming and error states. `key` is a stable React key,
 *   not a backend id (a streaming answer has no id yet).
 */
export type ChatMessage = {
  key: string;
  role: "user" | "sophia";
  content: string;
  sources: SourceOut[];
  webResults: WebResult[];
  searchMode: string;
  streaming?: boolean;
  error?: boolean;
  /** Raw-image URLs to show inside a user bubble (the photos they attached). */
  imageUrls?: string[];
};

/** Loading lines shown while Sophia thinks — one picked at random per query. */
export const CONTEMPLATION_PHRASES = [
  "Sophia is philosophizing…",
  "Sophia is connecting with higher dimensions…",
  "Sophia is thinking…",
  "Sophia is symbiotizing…",
  "Sophia is contemplating…",
  "Sophia is reasoning…",
  "Sophia is connecting with Nous…",
];

export function randomPhrase(): string {
  return CONTEMPLATION_PHRASES[Math.floor(Math.random() * CONTEMPLATION_PHRASES.length)];
}
