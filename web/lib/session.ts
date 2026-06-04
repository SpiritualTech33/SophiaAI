/**
 * Mental Model:
 *   Pure session constants — no `next/headers`, no runtime-specific imports —
 *   so this module is safe to pull into the proxy (edge), route handlers
 *   (node), and server components alike. The session is one httpOnly cookie,
 *   `sophia_token`, holding the JWT FastAPI issued. httpOnly keeps it out of
 *   reach of client JavaScript; the token only ever moves server-side.
 */

export const SESSION_COOKIE = "sophia_token";

/** 24 hours — mirrors the backend JWT lifetime (sophia/auth/security.py). */
export const SESSION_MAX_AGE = 60 * 60 * 24;

/** Cookie options for the session. `secure` only outside development. */
export function sessionCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_MAX_AGE,
  };
}
