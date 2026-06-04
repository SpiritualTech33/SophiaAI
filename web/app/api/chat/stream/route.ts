import { forward } from "@/lib/backend";

/**
 * Mental Model:
 *   The streaming heart of the BFF. The browser posts a message here; we relay
 *   it to FastAPI's SSE endpoint with the session's Bearer token and pipe the
 *   event stream straight back, token by token — no buffering, so Sophia's
 *   words appear as she forms them. Runs on the Node runtime because it holds
 *   a long-lived streaming connection.
 */
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const body = await request.text();

  const res = await forward("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });

  if (!res.ok || !res.body) {
    return new Response(
      `event: error\ndata: ${JSON.stringify({
        message: "Sophia could not answer just now. Please try again.",
      })}\n\n`,
      { status: res.status, headers: { "Content-Type": "text/event-stream" } },
    );
  }

  return new Response(res.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
