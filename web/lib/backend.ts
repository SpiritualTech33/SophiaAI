import { readToken } from "./auth";

/**
 * Mental Model:
 *   The one place that knows where FastAPI lives and how to speak to it with
 *   the user's session. Route handlers use `forward()` to relay an
 *   authenticated request to the backend and hand its Response straight back
 *   to the browser — the JWT is attached here, server-side, and never leaves.
 *   One swap point: SOPHIA_API_URL.
 */

export const BACKEND_URL = process.env.SOPHIA_API_URL ?? "http://127.0.0.1:8000";

/** Relay an authenticated request to FastAPI and return its raw Response. */
export async function forward(path: string, init: RequestInit = {}): Promise<Response> {
  const token = await readToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetch(`${BACKEND_URL}${path}`, { ...init, headers, cache: "no-store" });
}

/** Relay a JSON backend Response back to the client, preserving status. */
export async function relayJson(res: Response): Promise<Response> {
  const body = await res.text();
  return new Response(body || null, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("content-type") ?? "application/json" },
  });
}
