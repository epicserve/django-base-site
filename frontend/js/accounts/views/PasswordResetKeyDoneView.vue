<script setup>
import { RouterLink } from 'vue-router';
import AuthLayout from '@/layouts/AuthLayout.vue';
</script>

<template>
  <AuthLayout>
    <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">Password Changed</h1>
    <p class="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
      Your password has been reset successfully. You can now sign in with your new password.
    </p>
    <div class="mt-6">
      <RouterLink
        :to="{ name: 'login' }"
        class="block w-full cursor-pointer rounded-lg bg-blue-600 px-4 py-2.5 text-center text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
      >
        Sign In
      </RouterLink>
    </div>
  </AuthLayout>
</template>
