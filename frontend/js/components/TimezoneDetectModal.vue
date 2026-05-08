<script setup>
import { ref, onMounted, onUnmounted, inject } from 'vue';
import { useRoute } from 'vue-router';
import { patch } from '@/utils/api';

const AUTH_FLOW_ROUTES = new Set(['two-factor', 'account-reauthenticate']);

const appStore = inject('appStore');
const route = useRoute();
const visible = ref(false);
const browserTz = ref('');
const browserTzDisplay = ref('');
const userTzDisplay = ref('');

function dismiss() {
  const dismissKey = `tz-dismissed-${appStore.user.timezone}-${browserTz.value}`;
  sessionStorage.setItem(dismissKey, '1');
  visible.value = false;
}

async function updateTimezone() {
  await patch(`/api/users/${appStore.user.id}/`, { timezone: browserTz.value });
  appStore.user.timezone = browserTz.value;
  appStore.user.timezone_display = browserTzDisplay.value;
  visible.value = false;
}

let onVisibilityChange = null;

onMounted(() => {
  if (!appStore.user) return;
  if (appStore.user.is_hijacked) return;

  const runDetection = () => {
    if (route.meta.guest || AUTH_FLOW_ROUTES.has(route.name)) return;
    let detected;
    try {
      detected = Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch {
      return;
    }
    if (!detected || detected === appStore.user.timezone) return;

    const dismissKey = `tz-dismissed-${appStore.user.timezone}-${detected}`;
    if (sessionStorage.getItem(dismissKey)) return;

    browserTz.value = detected;
    browserTzDisplay.value = detected;
    userTzDisplay.value = appStore.user.timezone_display || appStore.user.timezone;
    visible.value = true;
  };

  if (typeof window.requestIdleCallback === 'function') {
    window.requestIdleCallback(runDetection, { timeout: 1000 });
  } else {
    setTimeout(runDetection, 300);
  }

  onVisibilityChange = () => {
    if (document.visibilityState === 'visible' && !visible.value) {
      runDetection();
    }
  };
  document.addEventListener('visibilitychange', onVisibilityChange);
});

onUnmounted(() => {
  if (onVisibilityChange) {
    document.removeEventListener('visibilitychange', onVisibilityChange);
    onVisibilityChange = null;
  }
});
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[100] bg-black/50">
    <div
      class="fixed left-1/2 top-1/2 z-[101] w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg bg-white shadow-xl dark:bg-gray-800"
    >
      <div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Your timezone has changed</h3>
      </div>
      <div class="px-6 py-4">
        <p class="mb-4 text-sm text-gray-600 dark:text-gray-400">
          It looks like you're now in a different timezone. Would you like to update your timezone setting?
        </p>
        <div class="flex items-center gap-4">
          <div class="flex-1 rounded-md bg-red-50 p-3 text-center dark:bg-red-900/20">
            <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Current Setting</div>
            <div class="mt-1 text-sm font-semibold text-gray-900 dark:text-white">
              {{ userTzDisplay }}
            </div>
          </div>
          <div class="text-gray-400">&rarr;</div>
          <div class="flex-1 rounded-md bg-green-50 p-3 text-center dark:bg-green-900/20">
            <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Detected</div>
            <div class="mt-1 text-sm font-semibold text-gray-900 dark:text-white">
              {{ browserTzDisplay }}
            </div>
          </div>
        </div>
      </div>
      <div class="flex justify-end gap-2 border-t border-gray-200 px-6 py-4 dark:border-gray-700">
        <button
          class="cursor-pointer px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
          @click="dismiss"
        >
          Keep current
        </button>
        <button
          class="cursor-pointer rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          @click="updateTimezone"
        >
          Update timezone
        </button>
      </div>
    </div>
  </div>
</template>
