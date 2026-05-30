<script setup>
import { ref, inject, onMounted } from 'vue';
import { useRoute, useRouter, RouterLink } from 'vue-router';
import AuthLayout from '@/layouts/AuthLayout.vue';
import FormField from '../components/FormField.vue';
import FormErrors from '../components/FormErrors.vue';
import { authApi, parseAllauthErrors } from '../api';
import { getPasskeyAssertion, isWebAuthnSupported } from '../../utils/webauthn';
import { safeNextUrl } from '../../utils/redirect';

const route = useRoute();
const router = useRouter();
const appStore = inject('appStore');

const email = ref('');
const password = ref('');
const errors = ref({});
const loading = ref(false);
const passkeyLoading = ref(false);
const passkeySupported = ref(false);
const passkeyInFlight = ref(false);

onMounted(() => {
  passkeySupported.value = isWebAuthnSupported();
  if (passkeySupported.value) {
    attemptPasskeyLogin(true);
  }
});

function getRedirectUrl() {
  return safeNextUrl(route.query.next);
}

function handleFlows(err) {
  // 401 + flows array means allauth is asking for another step
  const flows = err.data?.data?.flows || [];
  const pendingVerify = flows.some((f) => f.id === 'verify_email' && f.is_pending);
  const mfaRequired = flows.some((f) => f.id === 'mfa_authenticate');

  if (pendingVerify) {
    router.push({ name: 'verification-sent' });
    return true;
  }
  if (mfaRequired) {
    router.push({ name: 'two-factor', query: { next: safeNextUrl(route.query.next) } });
    return true;
  }
  return false;
}

async function onSubmit() {
  loading.value = true;
  errors.value = {};
  try {
    const data = await authApi.login(email.value, password.value);

    appStore.setUser(data.data?.user || null);
    await appStore.fetchContext();
    window.location.href = getRedirectUrl();
  } catch (err) {
    if (err.response?.status === 409) {
      window.location.href = getRedirectUrl();
      return;
    }
    if (handleFlows(err)) return;
    errors.value = err.data
      ? parseAllauthErrors(err.data)
      : { non_field_errors: ['An unexpected error occurred.'] };
    loading.value = false;
  }
}

async function attemptPasskeyLogin(isAuto = false) {
  if (passkeyInFlight.value) return;
  passkeyInFlight.value = true;

  if (!isAuto) {
    passkeyLoading.value = true;
  }
  errors.value = {};

  try {
    const optsResp = await authApi.beginPasskeyLogin();
    const options = optsResp.data?.request_options || optsResp.data;
    const credential = await getPasskeyAssertion(options);
    const data = await authApi.completePasskeyLogin(credential);

    appStore.setUser(data.data?.user || null);
    await appStore.fetchContext();
    window.location.href = getRedirectUrl();
  } catch (err) {
    if (err.name === 'NotAllowedError' || err.name === 'AbortError') {
      if (!isAuto) passkeyLoading.value = false;
      passkeyInFlight.value = false;
      return;
    }
    if (err.response?.status === 409) {
      window.location.href = getRedirectUrl();
      return;
    }
    if (!isAuto) {
      errors.value = err.data
        ? parseAllauthErrors(err.data)
        : { non_field_errors: [err.message || 'Passkey sign-in failed.'] };
      passkeyLoading.value = false;
    }
    passkeyInFlight.value = false;
  }
}

async function passkeyLogin() {
  attemptPasskeyLogin(false);
}
</script>

<template>
  <AuthLayout>
    <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">
      Sign In
    </h1>
    <p class="mt-2 text-center text-sm text-gray-500 dark:text-gray-400">
      Welcome back
    </p>
    <form
      class="mt-6 space-y-4"
      @submit.prevent="onSubmit"
    >
      <FormErrors :errors="errors.non_field_errors || []" />
      <FormField
        v-model="email"
        type="email"
        placeholder="Email"
        autocomplete="email"
        :errors="errors.email || []"
      />
      <FormField
        v-model="password"
        type="password"
        placeholder="Password"
        autocomplete="current-password"
        :errors="errors.password || []"
      />
      <div class="flex items-center justify-end">
        <RouterLink
          :to="{ name: 'password-reset' }"
          class="text-sm font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400"
        >
          Forgot password?
        </RouterLink>
      </div>
      <button
        type="submit"
        :disabled="loading"
        class="w-full cursor-pointer rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 dark:focus:ring-offset-gray-800"
      >
        {{ loading ? 'Signing in...' : 'Sign In' }}
      </button>
    </form>
    <div
      v-if="passkeySupported"
      class="mt-4"
    >
      <div class="relative my-3">
        <div class="absolute inset-0 flex items-center">
          <div class="w-full border-t border-gray-200 dark:border-gray-700" />
        </div>
        <div class="relative flex justify-center text-xs uppercase">
          <span class="bg-white px-2 text-gray-500 dark:bg-gray-800 dark:text-gray-400">or</span>
        </div>
      </div>
      <button
        type="button"
        :disabled="passkeyLoading"
        class="w-full cursor-pointer rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-semibold text-gray-700 shadow-sm transition hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700 disabled:opacity-50"
        @click="passkeyLogin"
      >
        {{ passkeyLoading ? 'Waiting for passkey…' : 'Sign in with a passkey' }}
      </button>
    </div>
    <template #footer>
      <p class="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
        Not a member?
        <RouterLink
          :to="{ name: 'signup' }"
          class="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400"
        >
          Create an account
        </RouterLink>
      </p>
    </template>
  </AuthLayout>
</template>
