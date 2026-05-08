<script setup>
import { RouterLink } from 'vue-router';
</script>

<template>
  <div class="flex min-h-[60vh] items-center justify-center">
    <div class="text-center">
      <h1 class="text-6xl font-bold text-gray-300 dark:text-gray-600">404</h1>
      <p class="mt-4 text-lg text-gray-600 dark:text-gray-400">Page not found</p>
      <RouterLink
        to="/"
        class="cursor-pointer mt-6 inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
      >
        Go Home
      </RouterLink>
    </div>
  </div>
</template>
