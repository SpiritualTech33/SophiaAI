import { NextResponse } from "next/server";
import { BACKEND_URL } from "@/lib/backend";
import { SESSION_COOKIE, sessionCookieOptions } from "@/lib/session";

/**
 * Mental Model:
 *   The register half of the BFF. FastAPI creates the account and returns a
 *   JWT immediately (auto-login), which we plant in the httpOnly cookie just
 *   like login. A 409 from the backend means the email is taken; we surface a
 *   clear message and let the form show it.
 */
export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ message: "Invalid request." }, { status: 400 });
  }

  const res = await fetch(`${BACKEND_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const message =
      res.status === 409
        ? "That email is already registered."
        : "Could not create your account.";
    return NextResponse.json({ message }, { status: res.status });
  }

  const { access_token } = (await res.json()) as { access_token: string };
  const response = NextResponse.json({ ok: true });
  response.cookies.set(SESSION_COOKIE, access_token, sessionCookieOptions());
  return response;
}
