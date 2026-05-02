/**
 * Sanitize a `?next=` redirect target. Only same-origin paths starting with a
 * single `/` are allowed. Protocol-relative (`//evil`) and backslash-prefixed
 * (`/\evil`) values are rejected because browsers normalize them to a
 * different origin. By default `/accounts/*` is also rejected to avoid
 * bouncing the user back into the auth flow they just completed; pass
 * `allowAccounts: true` for flows (e.g. reauth) that legitimately land back
 * inside `/accounts/`.
 */
export function safeNextUrl(next, fallback = '/', { allowAccounts = false } = {}) {
  if (typeof next !== 'string' || next.length === 0) return fallback;
  if (next[0] !== '/') return fallback;
  if (next.length > 1 && (next[1] === '/' || next[1] === '\\')) return fallback;
  if (!allowAccounts && next.startsWith('/accounts/')) return fallback;
  return next;
}
