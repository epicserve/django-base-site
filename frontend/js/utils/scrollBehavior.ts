import type { RouterScrollBehavior } from 'vue-router';

// App.vue swaps pages with an out-in transition: the old page stays on screen while it fades out, and the new one
// mounts after it. Scrolling waits for the new page, because on the old one a saved position can be past the bottom,
// and a hash's element isn't there yet.
let mountedPath: string | null = null;
let waiting: { path: string; resolve: () => void } | null = null;

/** App.vue calls this each time it mounts the page for `path`. */
export function pageMounted(path: string) {
  mountedPath = path;
  if (waiting?.path === path) {
    waiting.resolve();
    waiting = null;
  }
}

function pageReady(path: string): Promise<void> {
  if (mountedPath === path) return Promise.resolve();
  return new Promise((resolve) => {
    // A newer navigation replaces an older one's wait; the router then ignores the older one's position.
    waiting?.resolve();
    waiting = { path, resolve };
    // A backstop, so a page that fails to mount can't hold the scroll forever.
    setTimeout(resolve, 1000);
  });
}

export const scrollBehavior: RouterScrollBehavior = async (to, from, savedPosition) => {
  if (to.path !== from.path) await pageReady(to.path);
  // Back and forward return to where the page was left.
  if (savedPosition) return savedPosition;
  if (to.hash) return { el: to.hash };
  // A change to the query alone, such as a filter or a page of results, leaves the scroll where it is.
  if (to.path === from.path) return false;
  return { top: 0 };
};
