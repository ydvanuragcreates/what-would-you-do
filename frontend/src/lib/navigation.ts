/** The cookie the backend sets on login (see backend/app/api/cookies.py). */
export const AUTH_COOKIE = "access_token";

const DEFAULT_AFTER_LOGIN = "/play";

/**
 * Go to a page with a FULL page load instead of a client-side transition.
 *
 * Use this whenever the login state just changed (log in, sign up, log out). Next.js
 * caches the result of pages it prefetched, including a redirect to /login from the
 * proxy, and a client-side navigation would replay that stale answer and bounce a
 * freshly logged-in player straight back to the login page. A full load always asks
 * the server again, with the current cookie.
 */
export function navigateWithFullReload(path: string) {
  window.location.assign(path);
}

/**
 * Where to send someone after logging in, from the `?next=` query parameter.
 *
 * Only same-site paths are accepted. Otherwise a crafted link like
 * /login?next=https://evil.example would bounce a freshly logged-in user to an
 * attacker's site (an "open redirect").
 */
export function safeNextPath(next: string | null | undefined): string {
  if (!next) return DEFAULT_AFTER_LOGIN;
  // Must start with a single "/". "//host" and "/\host" are treated as external by browsers.
  if (!next.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) {
    return DEFAULT_AFTER_LOGIN;
  }
  return next;
}
