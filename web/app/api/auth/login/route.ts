import { NextResponse } from "next/server";
import { BACKEND_URL } from "@/lib/backend";
import { SESSION_COOKIE, sessionCookieOptions } from "@/lib/session";

/**
 * Mental Model:
 *   The login half of the BFF. The browser posts credentials here; we relay
 *   them to FastAPI, and on success we plant the returned JWT in an httpOnly
 *   cookie. The token is set server-side and never returned to client JS — the
 *   browser only learns "ok". Bad credentials pass the backend's status and a
 *   safe message straight through.
 */
export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ message: "Invalid request." }, { status: 400 });
  }

  const res = await fetch(`${BACKEND_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const message =
      res.status === 401 ? "Invalid email or password." : "Could not sign in.";
    return NextResponse.json({ message }, { status: res.status });
  }

  const { access_token } = (await res.json()) as { access_token: string };
  const response = NextResponse.json({ ok: true });
  response.cookies.set(SESSION_COOKIE, access_token, sessionCookieOptions());
  return response;
}
