import { onMounted, onUnmounted } from 'vue';

export function readUrlParams(defaults = {}) {
  const params = new URLSearchParams(window.location.search),
    result = {};
  Object.keys(defaults).forEach((key) => {
    const val = params.get(key);
    if (val !== null) {
      result[key] = typeof defaults[key] === 'number' ? parseInt(val, 10) || defaults[key] : val;
    } else {
      result[key] = defaults[key];
    }
  });
  return result;
}

export function pushUrlParams(params) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value && value !== '' && value !== 0) {
      search.set(key, value);
    }
  });
  window.history.pushState(null, '', search.toString()
    ? `${window.location.pathname}?${search}` : window.location.pathname);
}

export function usePopState(callback) {
  onMounted(() => window.addEventListener('popstate', callback));
  onUnmounted(() => window.removeEventListener('popstate', callback));
}
