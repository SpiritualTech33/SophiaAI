import { forward } from "@/lib/backend";

/**
 * Mental Model:
 *   The image-serving door of the BFF. The backend's /api/files/{id}/raw
 *   answers with raw bytes (an uploaded or generated image) and the correct
 *   content-type — we stream that straight back to the browser for <img src>.
 */
export const runtime = "nodejs";

export async function GET(_req: Request, ctx: RouteContext<"/api/files/[id]/raw">) {
  const { id } = await ctx.params;
  const res = await forward(`/api/files/${id}/raw`);

  if (!res.ok) {
    return new Response(await res.text(), {
      status: res.status,
      headers: { "Content-Type": res.headers.get("content-type") ?? "application/json" },
    });
  }

  const bytes = await res.arrayBuffer();
  return new Response(bytes, {
    status: 200,
    headers: {
      "Content-Type": res.headers.get("content-type") ?? "application/octet-stream",
    },
  });
}
