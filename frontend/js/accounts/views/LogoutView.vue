<script setup lang="ts">
import { onMounted } from 'vue';
import { useAppStore } from '@/stores/app';
import { authApi } from '../api';

const appStore = useAppStore();

onMounted(async () => {
  if (appStore.isAuthenticated) {
    try {
      // Headless logout returns 401 (no longer authenticated) on success.
      // Our request() throws on non-2xx, so catch is expected.
      await authApi.logout();
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
