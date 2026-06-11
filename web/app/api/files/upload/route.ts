import { forward, relayJson } from "@/lib/backend";

/**
 * Mental Model:
 *   The upload door of the BFF. The browser posts multipart form-data here; we
 *   re-forward the same FormData to FastAPI with the session's Bearer token.
 *   We pass the FormData straight to fetch so it sets the multipart boundary
 *   itself — forward() must NOT force a JSON Content-Type, or the boundary is
 *   lost and the backend can't parse the file. The JSON response (or a
 *   413/415/422 error) is relayed back untouched.
 */
export const runtime = "nodejs";

export async function POST(request: Request) {
  const form = await request.formData();
  return relayJson(
    await forward("/api/files/upload", { method: "POST", body: form }),
  );
}
