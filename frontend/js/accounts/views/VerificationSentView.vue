<script setup>
import { RouterLink } from 'vue-router';
import AuthLayout from '@/layouts/AuthLayout.vue';
</script>

<template>
  <AuthLayout>
    <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">
      Verify Your Email
    </h1>
    <p class="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
      We have sent you a verification email. Please check your inbox and click the link to verify your email address.
    </p>
    <template #footer>
      <p class="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
        <RouterLink
          :to="{ name: 'login' }"
          class="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400"
        >
          Back to Sign In
        </RouterLink>
      </p>
    </template>
  </AuthLayout>
</template>
