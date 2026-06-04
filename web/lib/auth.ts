import { cookies } from "next/headers";
import { SESSION_COOKIE } from "./session";

/**
 * Mental Model:
 *   Server-side session reads. The pure constants live in ./session (safe for
 *   the proxy); this module adds the one piece that needs the request context
 *   — reading the cookie via next/headers. Kept separate so the proxy never
 *   pulls next/headers into its bundle.
 */

export { SESSION_COOKIE, SESSION_MAX_AGE, sessionCookieOptions } from "./session";

/** Read the JWT from the request cookies (server-side only). */
export async function readToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(SESSION_COOKIE)?.value ?? null;
}
