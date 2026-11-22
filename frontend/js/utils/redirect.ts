// Any origin works as the base: an address that leaves it would leave the site's own origin too.
const BASE = 'http://same-origin.invalid';

/**
 * Sanitize a `?next=` redirect target. Only same-origin paths are allowed. The value is read the way a browser reads
 * an address, which drops tabs and newlines and treats `\` as `/`, so protocol-relative (`//evil`), backslash
 * (`/\evil`), and whitespace (`/<tab>/evil`) values, which all lead to a different origin, are rejected. By default
 * `/accounts/*` is also rejected to avoid bouncing the user back into the auth flow they just completed; pass
 * `allowAccounts: true` for flows (e.g. reauth) that legitimately land back inside `/accounts/`.
 */
export function safeNextUrl(next: unknown, fallback = '/', { allowAccounts = false } = {}): string {
  if (typeof next !== 'string' || !next.startsWith('/')) return fallback;
  let url: URL;
  try {
    url = new URL(next, BASE);
  } catch {
    return fallback;
  }
  if (url.origin !== BASE) return fallback;
  if (!allowAccounts && url.pathname.startsWith('/accounts/')) return fallback;
  return next;
}
