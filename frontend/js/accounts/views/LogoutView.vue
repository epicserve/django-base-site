<script setup>
import { onMounted, inject } from 'vue';
import { del } from '../../utils/api';

const appStore = inject('appStore');

onMounted(async () => {
  if (appStore.isAuthenticated) {
    try {
      // Headless logout returns 401 (no longer authenticated) on success.
      // Our request() throws on non-2xx, so catch is expected.
      await del('/_allauth/browser/v1/auth/session');
    } catch {
      // Session destroyed — 401 is the expected response
    }
  }
  appStore.clearUser();
  window.location.href = '/accounts/login/';
});
</script>

<template>
  <div class="flex min-h-[60vh] items-center justify-center">
    <p class="text-sm text-gray-500 dark:text-gray-400">Signing out...</p>
  </div>
</template>
