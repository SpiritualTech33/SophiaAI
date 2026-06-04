import { forward, relayJson } from "@/lib/backend";

/**
 * Mental Model:
 *   Fetch one document's full markdown for the reader overlay. The corpus list
 *   itself is loaded server-side at page render; only the on-demand full text
 *   needs a client relay, since the reader opens lazily when a document (or a
 *   source chip) is clicked.
 */
export async function GET(_req: Request, ctx: RouteContext<"/api/corpus/[id]">) {
  const { id } = await ctx.params;
  return relayJson(await forward(`/api/corpus/${id}`));
}
