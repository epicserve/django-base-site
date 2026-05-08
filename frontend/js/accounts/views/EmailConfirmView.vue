<script setup>
import { ref, onMounted, inject } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import AuthLayout from '@/layouts/AuthLayout.vue';
import { authApi } from '../api';

const route = useRoute();
const appStore = inject('appStore');

const status = ref('loading');
const errorMessage = ref('');

const VERIFIED_KEYS_STORAGE = 'verifiedEmailKeys';

function loadVerifiedKeys() {
  try {
    return new Set(JSON.parse(sessionStorage.getItem(VERIFIED_KEYS_STORAGE) || '[]'));
  } catch {
    return new Set();
  }
}

function rememberVerifiedKey(key) {
  const keys = loadVerifiedKeys();
  keys.add(key);
  try {
    sessionStorage.setItem(VERIFIED_KEYS_STORAGE, JSON.stringify([...keys]));
  } catch {
    // sessionStorage may be unavailable (private mode); fall through silently.
  }
}

onMounted(async () => {
  // The email link URL-encodes the key (allauth runs it through quote()),
  // so decode before POSTing or allauth rejects it as "invalid or expired".
  const key = decodeURIComponent(route.params.key);

  // If we've already verified this key in the current browser session, the
  // server will reject a second POST as "invalid or expired" — refreshing the
  // page after a successful confirmation should still look like success.
  if (loadVerifiedKeys().has(key)) {
    status.value = 'success';
    return;
  }

  try {
    await authApi.verifyEmail(key);
    rememberVerifiedKey(key);
    status.value = 'success';
  } catch (err) {
    // A successful verification for an unauthenticated user still comes back
    // as 401 with an auth/flow response (no `errors`). Treat responses with
    // no explicit errors array as success.
    if (err.data && !err.data.errors) {
      rememberVerifiedKey(key);
      status.value = 'success';
      return;
    }
    status.value = 'error';
    errorMessage.value = appStore.isAuthenticated
      ? 'This link has already been used. Your email is confirmed.'
      : 'This confirmation link has already been used or has expired.';
  }
});
</script>

<template>
  <AuthLayout>
    <template v-if="status === 'loading'">
      <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">Confirming Email</h1>
      <p class="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">Please wait...</p>
    </template>
    <template v-else-if="status === 'success'">
      <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">Email Confirmed</h1>
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
        Link No Longer Valid
      </h1>
      <p class="mt-4 text-center text-sm text-gray-600 dark:text-gray-300">
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
