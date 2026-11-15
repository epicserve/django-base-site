import { onMounted, onUnmounted } from 'vue';

type UrlParamValue = string | number;

/**
 * Read the query string into an object shaped like `defaults`. A key that's missing from the URL keeps its default,
 * and a key whose default is a number is parsed as one (falling back to the default when it isn't a number).
 */
export function readUrlParams<Params extends Record<string, UrlParamValue>>(defaults: Params): Params {
  const params = new URLSearchParams(window.location.search),
    result: Record<string, UrlParamValue> = {};
  for (const [key, fallback] of Object.entries(defaults)) {
    const val = params.get(key);
    if (val === null) {
      result[key] = fallback;
    } else {
      result[key] = typeof fallback === 'number' ? parseInt(val, 10) || fallback : val;
    }
  }
  return result as Params;
}

export function pushUrlParams(params: Record<string, UrlParamValue | null | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      search.set(key, String(value));
    }
  });
  window.history.pushState(
    null,
    '',
    search.toString() ? `${window.location.pathname}?${search}` : window.location.pathname,
  );
}

export function usePopState(callback: (event: PopStateEvent) => void) {
  onMounted(() => window.addEventListener('popstate', callback));
  onUnmounted(() => window.removeEventListener('popstate', callback));
}
