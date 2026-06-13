import { forward, relayJson } from "@/lib/backend";

/**
 * Mental Model:
 *   The image-generation door of the BFF. The browser posts { prompt } as
 *   JSON; we relay it to FastAPI, which calls Pollinations.ai, stores the
 *   PNG as a UserFile, and answers with { id, filename, mime, url }. We relay
 *   that JSON (or a 502/422 error) back untouched.
 */
export const runtime = "nodejs";

export async function POST(request: Request) {
  const body = await request.text();
  return relayJson(
    await forward("/api/images/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    }),
  );
}
