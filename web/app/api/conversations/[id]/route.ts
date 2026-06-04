import { forward, relayJson } from "@/lib/backend";

/**
 * Mental Model:
 *   The per-conversation BFF relay. Opening a past conversation (GET),
 *   renaming it (PATCH), and deleting it (DELETE) all flow through here with
 *   the session's Bearer token attached. The backend enforces ownership; we
 *   just pass the user's intent and the backend's verdict back and forth.
 */

export async function GET(_req: Request, ctx: RouteContext<"/api/conversations/[id]">) {
  const { id } = await ctx.params;
  return relayJson(await forward(`/api/conversations/${id}`));
}

export async function PATCH(req: Request, ctx: RouteContext<"/api/conversations/[id]">) {
  const { id } = await ctx.params;
  const body = await req.text();
  return relayJson(
    await forward(`/api/conversations/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body,
    }),
  );
}

export async function DELETE(_req: Request, ctx: RouteContext<"/api/conversations/[id]">) {
  const { id } = await ctx.params;
  const res = await forward(`/api/conversations/${id}`, { method: "DELETE" });
  return new Response(null, { status: res.status });
}
