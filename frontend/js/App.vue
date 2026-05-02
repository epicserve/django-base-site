<script setup>
import { inject } from 'vue';
import { RouterView } from 'vue-router';
import AppLayout from '@/layouts/AppLayout.vue';

const appStore = inject('appStore');

function reloadForUpdate() {
  window.location.reload();
}
</script>

<template>
  <div
    v-if="appStore.loading"
    class="flex min-h-screen items-center justify-center bg-white dark:bg-gray-900"
  >
    <div class="text-gray-400 dark:text-gray-500">
      Loading...
    </div>
  </div>
  <template v-else>
    <div
      v-if="appStore.updateAvailable"
      class="fixed inset-x-0 top-0 z-50 flex items-center justify-center gap-3 bg-indigo-600 px-4 py-2 text-sm text-white shadow"
    >
      <span>A new version of the app is available.</span>
      <button
        class="cursor-pointer rounded bg-white/15 px-3 py-1 font-medium hover:bg-white/25"
        @click="reloadForUpdate"
      >
        Reload
      </button>
    </div>
    <AppLayout v-if="appStore.isAuthenticated">
      <RouterView v-slot="{ Component, route }">
        <Transition
          name="page"
          mode="out-in"
        >
          <component
            :is="Component"
            :key="route.path"
          />
        </Transition>
      </RouterView>
    </AppLayout>
    <RouterView
      v-else
      v-slot="{ Component, route }"
    >
      <Transition
        name="page"
        mode="out-in"
      >
        <component
          :is="Component"
          :key="route.path"
        />
      </Transition>
    </RouterView>
  </template>
</template>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(4px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
