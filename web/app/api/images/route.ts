import { forward, relayJson } from "@/lib/backend";

/**
 * Mental Model:
 *   The list endpoint door of the BFF. The browser asks for the user's
 *   generated images; we relay the GET to FastAPI with the session JWT,
 *   and return the JSON array (or error) untouched.
 */
export const runtime = "nodejs";

export async function GET() {
  return relayJson(await forward("/api/images", { method: "GET" }));
}
