import { forward, relayJson } from "@/lib/backend";

/**
 * Mental Model:
 *   Client-side refresh of the conversation list — used after a brand-new
 *   chat is created mid-stream, when the sidebar needs to learn the new
 *   conversation without a full page reload. Just an authenticated relay of
 *   GET /api/conversations.
 */
export async function GET() {
  return relayJson(await forward("/api/conversations"));
}
