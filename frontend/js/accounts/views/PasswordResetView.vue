<script setup>
import { ref } from 'vue';
import { useRouter, RouterLink } from 'vue-router';
import AuthLayout from '@/layouts/AuthLayout.vue';
import FormField from '../components/FormField.vue';
import FormErrors from '../components/FormErrors.vue';
import { authApi, parseAllauthErrors } from '../api';

const router = useRouter();

const email = ref('');
const errors = ref({});
const loading = ref(false);

async function onSubmit() {
  loading.value = true;
  errors.value = {};
  try {
    await authApi.requestPasswordReset(email.value);
    router.push({ name: 'password-reset-done' });
  } catch (err) {
    if (err.data) {
      errors.value = parseAllauthErrors(err.data);
    } else {
      errors.value = { non_field_errors: ['An unexpected error occurred.'] };
    }
    loading.value = false;
  }
}
</script>

<template>
  <AuthLayout>
    <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">Password Reset</h1>
    <p class="mt-2 text-center text-sm text-gray-500 dark:text-gray-400">
      Enter your e-mail address and we'll send you a link to reset your password.
    </p>
    <form class="mt-6 space-y-4" @submit.prevent="onSubmit">
      <FormErrors :errors="errors.non_field_errors || []" />
      <FormField v-model="email" type="email" placeholder="Email" autocomplete="email" :errors="errors.email || []" />
      <button
        type="submit"
        :disabled="loading"
        class="w-full cursor-pointer rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 dark:focus:ring-offset-gray-800"
      >
        {{ loading ? 'Sending...' : 'Reset My Password' }}
      </button>
    </form>
    <template #footer>
      <p class="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
        <RouterLink :to="{ name: 'login' }" class="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400">
          Back to Sign In
        </RouterLink>
      </p>
    </template>
  </AuthLayout>
</template>
