<script setup>
import { inject } from 'vue';
import { RouterLink } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import AppToast from '@/components/AppToast.vue';

const appStore = inject('appStore');
</script>

<template>
  <nav class="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
    <div class="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex h-14 items-center justify-between">
        <RouterLink class="text-lg font-semibold text-gray-900 dark:text-white" to="/">
          {{ appStore.siteName }}
        </RouterLink>
        <div class="flex items-center gap-3 text-sm">
          <RouterLink
            class="text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white"
            :to="{ name: 'pricing' }"
          >
            Pricing
          </RouterLink>
          <ThemeToggle />
          <template v-if="!appStore.isAuthenticated">
            <RouterLink
              class="text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white"
              :to="{ name: 'login' }"
            >
              Sign in
            </RouterLink>
            <RouterLink
              v-if="appStore.signupOpen"
              class="rounded-md bg-indigo-600 px-3 py-1.5 font-medium text-white hover:bg-indigo-500"
              :to="{ name: 'signup' }"
            >
              Sign up
            </RouterLink>
          </template>
          <RouterLink v-else class="text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white" to="/">
            Dashboard
          </RouterLink>
        </div>
      </div>
    </div>
  </nav>

  <main class="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 mt-6 pb-16">
    <slot />
  </main>

  <AppToast />
</template>
