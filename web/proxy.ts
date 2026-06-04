import { NextResponse, type NextRequest } from "next/server";
import { SESSION_COOKIE } from "@/lib/session";

/**
 * Mental Model:
 *   The gatekeeper at the edge (Next.js 16 renamed Middleware to Proxy). It
 *   runs before the matched routes and does one cheap, optimistic check: is a
 *   session cookie present? No cookie and you're heading for /chat → bounce to
 *   /login. Already have a cookie and you're heading for /login or /register →
 *   bounce to /chat. This is presence-only; the real authority is the backend,
 *   which rejects an expired or forged token on the next API call.
 */
export function proxy(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  const { pathname } = request.nextUrl;

  if (pathname.startsWith("/chat") && !token) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }

  if ((pathname === "/login" || pathname === "/register") && token) {
    const url = request.nextUrl.clone();
    url.pathname = "/chat";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/chat/:path*", "/login", "/register"],
};
