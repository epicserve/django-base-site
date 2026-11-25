/**
 * When a signed-in user's session ends (it expired, or they signed out in another tab), their next `/api/` call gets a
 * 401, and the SPA sends them to sign in again and then back to the page they were on. `app.ts` wires this up.
 */

// Any origin works as the base: only the path matters.
const BASE = 'http://same-origin.invalid';

/**
 * Whether a 401 from `url` means the session ended: it came from `/api/` while the SPA thinks someone is signed in.
 * allauth's `/_allauth/` answers 401 on purpose (while a two-factor code is pending, after signing out), and someone who
 * never signed in has no session to lose.
 */
export function sessionEnded(url: string, signedIn: boolean): boolean {
  return signedIn && new URL(url, BASE).pathname.startsWith('/api/');
}

/** The sign-in page to send someone to when their session has ended, coming back to `path` afterward. */
export function signInAgainUrl(path: string): string {
  return `/accounts/login/?${new URLSearchParams({ next: path, session: 'expired' })}`;
}
