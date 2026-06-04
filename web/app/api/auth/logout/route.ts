import { NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/session";

/**
 * Mental Model:
 *   Logout is purely local: the JWT is stateless, so signing out just means
 *   forgetting it. We clear the httpOnly session cookie and report ok; the
 *   client then navigates to /login.
 */
export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.set(SESSION_COOKIE, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 0,
  });
  return response;
}
