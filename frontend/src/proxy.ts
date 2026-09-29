import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { AUTH_COOKIE } from "@/lib/navigation";

/**
 * A fast first gate: anyone WITHOUT a login cookie is sent to /login before the page
 * even renders. This only checks that the cookie exists, not that it is valid; the
 * backend is the real authority (every API call re-checks the token), and the screens
 * also handle an expired login by redirecting. So this is a convenience, not security.
 *
 * (In this Next.js version the old "middleware" file is called "proxy".)
 */
export function proxy(request: NextRequest) {
  if (request.cookies.has(AUTH_COOKIE)) return NextResponse.next();

  const login = new URL("/login", request.url);
  login.searchParams.set("next", request.nextUrl.pathname + request.nextUrl.search);
  return NextResponse.redirect(login);
}

export const config = {
  matcher: ["/play/:path*", "/results/:path*", "/history/:path*"],
};
