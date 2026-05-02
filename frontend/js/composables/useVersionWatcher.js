import { get } from '@/utils/api';

const POLL_INTERVAL_MS = 5 * 60 * 1000;

export function startVersionWatcher(appStore) {
  let timer = null;

  async function check() {
    if (appStore.updateAvailable) return;
    try {
      const data = await get('/api/version/');
      if (!appStore.version) {
        appStore.version = data.version;
      } else if (data.version && data.version !== appStore.version) {
        appStore.updateAvailable = true;
      }
    } catch {
      // Network blips shouldn't spam the console; next tick will retry.
    }
  }

  function onVisibility() {
    if (document.visibilityState === 'visible') check();
  }

  timer = setInterval(check, POLL_INTERVAL_MS);
  document.addEventListener('visibilitychange', onVisibility);

  return () => {
    clearInterval(timer);
    document.removeEventListener('visibilitychange', onVisibility);
  };
}
