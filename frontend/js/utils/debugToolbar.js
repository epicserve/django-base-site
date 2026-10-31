// The Django Debug Toolbar is rendered into the HTML by the server, and the server shows it only while this
// cookie is "1" (apps/base/debug_toolbar.py), so toggling means setting the cookie and reloading the page.
const COOKIE = 'debug_toolbar';
const ONE_YEAR = 60 * 60 * 24 * 365;

export function isDebugToolbarOn() {
  return document.cookie.split('; ').includes(`${COOKIE}=1`);
}

export function toggleDebugToolbar() {
  const turnOn = !isDebugToolbarOn();
  document.cookie = `${COOKIE}=${turnOn ? '1' : '0'}; path=/; max-age=${ONE_YEAR}; SameSite=Lax`;
  if (turnOn) {
    // The toolbar remembers if it was collapsed to its handle; turning it on should show the panels.
    document.cookie = `djdt=show; path=/; max-age=${ONE_YEAR}; SameSite=Lax`;
  }
  window.location.reload();
}
