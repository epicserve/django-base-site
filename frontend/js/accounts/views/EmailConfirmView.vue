<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import AuthLayout from '@/layouts/AuthLayout.vue';
import { authApi } from '../api';

const route = useRoute();

const status = ref('loading');
const errorMessage = ref('');

onMounted(async () => {
  try {
    // The email link URL-encodes the key (allauth runs it through quote()),
    // so decode before POSTing or allauth rejects it as "invalid or expired".
    await authApi.verifyEmail(decodeURIComponent(route.params.key));
    status.value = 'success';
  } catch (err) {
    // A successful verification for an unauthenticated user still comes back
    // as 401 with an auth/flow response (no `errors`). Treat responses with
    // no explicit errors array as success.
    if (err.data && !err.data.errors) {
      status.value = 'success';
      return;
    }
    status.value = 'error';
    if (err.data?.errors?.[0]?.message) {
      errorMessage.value = err.data.errors[0].message;
    } else {
      errorMessage.value = 'This confirmation link is invalid or has expired.';
    }
  }
});
</script>

<template>
  <AuthLayout>
    <template v-if="status === 'loading'">
      <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">
        Confirming Email
      </h1>
      <p class="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
        Please wait...
      </p>
    </template>
    <template v-else-if="status === 'success'">
      <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">
        Email Confirmed
      </h1>
      <p class="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
        Your email address has been confirmed. You can now sign in.
      </p>
      <div class="mt-6">
        <RouterLink
          :to="{ name: 'login' }"
          class="block w-full cursor-pointer rounded-lg bg-blue-600 px-4 py-2.5 text-center text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
        >
          Sign In
        </RouterLink>
      </div>
    </template>
    <template v-else>
      <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">
        Confirmation Failed
      </h1>
      <p class="mt-4 text-center text-sm text-red-600 dark:text-red-400">
        {{ errorMessage }}
      </p>
      <div class="mt-6">
        <RouterLink
          :to="{ name: 'login' }"
          class="block w-full cursor-pointer rounded-lg bg-blue-600 px-4 py-2.5 text-center text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
        >
          Back to Sign In
        </RouterLink>
      </div>
    </template>
  </AuthLayout>
</template>
