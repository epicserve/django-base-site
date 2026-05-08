<script setup>
import { ref } from 'vue';
import { useRoute, useRouter, RouterLink } from 'vue-router';
import AuthLayout from '@/layouts/AuthLayout.vue';
import FormField from '../components/FormField.vue';
import FormErrors from '../components/FormErrors.vue';
import { authApi, parseAllauthErrors } from '../api';

const route = useRoute();
const router = useRouter();

const password = ref('');
const errors = ref({});
const loading = ref(false);
const badToken = ref(false);

async function onSubmit() {
  loading.value = true;
  errors.value = {};
  try {
    await authApi.resetPassword(route.params.key, password.value);
    router.push({ name: 'password-reset-key-done' });
  } catch (err) {
    // allauth returns 401 after a successful reset (password changed,
    // now log in). Treat 401 with is_authenticated=false as success.
    if (err.response?.status === 401 && err.data?.meta?.is_authenticated === false) {
      router.push({ name: 'password-reset-key-done' });
      return;
    }
    if (err.data) {
      const parsed = parseAllauthErrors(err.data);

      if (parsed.key || parsed.token) {
        badToken.value = true;
      } else {
        errors.value = parsed;
      }
    } else {
      errors.value = { non_field_errors: ['An unexpected error occurred.'] };
    }
    loading.value = false;
  }
}
</script>

<template>
  <AuthLayout>
    <template v-if="badToken">
      <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">
        Invalid Reset Link
      </h1>
      <p class="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
        The password reset link was invalid, possibly because it has already been used or has expired. Please request a
        new password reset.
      </p>
      <div class="mt-6">
        <RouterLink
          :to="{ name: 'password-reset' }"
          class="block w-full cursor-pointer rounded-lg bg-blue-600 px-4 py-2.5 text-center text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
        >
          Request New Reset Link
        </RouterLink>
      </div>
    </template>
    <template v-else>
      <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">Set New Password</h1>
      <p class="mt-2 text-center text-sm text-gray-500 dark:text-gray-400">Enter your new password below.</p>
      <form class="mt-6 space-y-4" @submit.prevent="onSubmit">
        <FormErrors :errors="errors.non_field_errors || []" />
        <FormField
          v-model="password"
          label="New Password"
          type="password"
          placeholder="New password"
          autocomplete="new-password"
          :errors="errors.password || errors.password1 || []"
        />
        <button
          type="submit"
          :disabled="loading"
          class="w-full cursor-pointer rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 dark:focus:ring-offset-gray-800"
        >
          {{ loading ? 'Resetting...' : 'Reset Password' }}
        </button>
      </form>
    </template>
    <template #footer>
      <p class="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
        <RouterLink :to="{ name: 'login' }" class="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400">
          Back to Sign In
        </RouterLink>
      </p>
    </template>
  </AuthLayout>
</template>
