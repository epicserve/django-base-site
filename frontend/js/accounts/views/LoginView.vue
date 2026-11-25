<script setup lang="ts">
import { ref, onBeforeUnmount, onMounted } from 'vue';
import { useRoute, useRouter, RouterLink } from 'vue-router';
import AuthLayout from '@/layouts/AuthLayout.vue';
import FormField from '../components/FormField.vue';
import FormErrors from '../components/FormErrors.vue';
import { authApi, parseAllauthErrors, pendingFlows } from '../api';
import { ApiError } from '../../utils/api';
import { getPasskeyAssertion, isConditionalMediationAvailable, isWebAuthnSupported } from '../../utils/webauthn';
import { safeNextUrl } from '../../utils/redirect';

const route = useRoute();
const router = useRouter();

// app.ts sends someone here with `?session=expired` when an /api/ call finds their session has ended.
const sessionExpired = route.query.session === 'expired';
const email = ref('');
const password = ref('');
const errors = ref<Record<string, string[]>>({});
const loading = ref(false);
const passkeyLoading = ref(false);
const passkeySupported = ref(false);
let conditionalAvailable = false;
// Aborts the pending autofill (conditional) passkey request.
let conditionalRequest: AbortController | null = null;
// allauth keeps the passkey challenge in the session, so the options request can start an anonymous session. If its
// response lands after sign-in's, that session's cookie replaces the signed-in one, so sign-in waits for it.
let passkeyOptionsRequest: Promise<unknown> = Promise.resolve();

onMounted(async () => {
  passkeySupported.value = isWebAuthnSupported();
  // Offer passkeys in the email field's autofill list. A plain (modal) request here would open the
  // browser's passkey dialog on every visit, which blocks the page until it's dismissed.
  conditionalAvailable = await isConditionalMediationAvailable();
  if (conditionalAvailable) {
    attemptPasskeyLogin({ conditional: true });
  }
});

onBeforeUnmount(cancelConditionalRequest);

function cancelConditionalRequest() {
  conditionalRequest?.abort();
  conditionalRequest = null;
}

function getRedirectUrl() {
  return safeNextUrl(route.query.next);
}

function handleFlows(err: unknown) {
  // 401 + flows array means allauth is asking for another step
  const flows = err instanceof ApiError ? pendingFlows(err.data) : [];
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
    await passkeyOptionsRequest;
    await authApi.login(email.value, password.value);
    // A full page load, not a router push, so nothing from the signed-out session lingers. The new page loads the
    // signed-in user's app context.
    window.location.href = getRedirectUrl();
  } catch (err) {
    if (err instanceof ApiError && err.response.status === 409) {
      window.location.href = getRedirectUrl();
      return;
    }
    if (handleFlows(err)) return;
    errors.value =
      err instanceof ApiError && err.data
        ? parseAllauthErrors(err.data)
        : { non_field_errors: ['An unexpected error occurred.'] };
    loading.value = false;
  }
}

async function attemptPasskeyLogin({ conditional = false }: { conditional?: boolean } = {}) {
  // An autofill request started during a password sign-in could replace its session the same way.
  if (conditional && loading.value) return;
  // Only one WebAuthn request can be pending, so the button cancels the autofill one first.
  cancelConditionalRequest();
  const controller = new AbortController();

  if (conditional) {
    conditionalRequest = controller;
  } else {
    passkeyLoading.value = true;
    errors.value = {};
  }

  // The autofill request starts on its own, so it stays quiet until the user picks a passkey from it.
  let userChosePasskey = !conditional;

  try {
    // A second options request sent while the first is pending could start a second session, and the challenge would
    // then be in whichever session's cookie didn't win.
    await passkeyOptionsRequest;
    const optionsRequest = authApi.beginPasskeyLogin();
    passkeyOptionsRequest = optionsRequest.catch(() => {});
    const optsResp = await optionsRequest;
    const options = optsResp.data.request_options;
    const credential = await getPasskeyAssertion(options, {
      mediation: conditional ? 'conditional' : undefined,
      signal: controller.signal,
    });
    userChosePasskey = true;
    await authApi.completePasskeyLogin(credential);
    // A full page load, not a router push, so nothing from the signed-out session lingers. The new page loads the
    // signed-in user's app context.
    window.location.href = getRedirectUrl();
  } catch (err) {
    if (err instanceof ApiError && err.response.status === 409) {
      window.location.href = getRedirectUrl();
      return;
    }
    if (!userChosePasskey) return;
    // Cancelling the passkey dialog isn't an error worth showing.
    if (!(err instanceof Error && (err.name === 'NotAllowedError' || err.name === 'AbortError'))) {
      errors.value =
        err instanceof ApiError && err.data
          ? parseAllauthErrors(err.data)
          : { non_field_errors: [(err instanceof Error && err.message) || 'Passkey sign-in failed.'] };
    }
    resumeAutofill();
  }
}

// After a passkey attempt fails or is cancelled, offer passkeys in autofill again.
function resumeAutofill() {
  passkeyLoading.value = false;
  if (conditionalAvailable) attemptPasskeyLogin({ conditional: true });
}

async function passkeyLogin() {
  attemptPasskeyLogin();
}
</script>

<template>
  <AuthLayout>
    <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">Sign In</h1>
    <p class="mt-2 text-center text-sm text-gray-500 dark:text-gray-400">Welcome Back</p>
    <form class="mt-6 space-y-4" @submit.prevent="onSubmit">
      <p
        v-if="sessionExpired"
        role="status"
        class="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:bg-amber-900/20 dark:text-amber-300"
      >
        Your session has ended. Sign in again to pick up where you left off.
      </p>
      <FormErrors :errors="errors.non_field_errors || []" />
      <FormField
        v-model="email"
        type="email"
        placeholder="Email"
        autocomplete="username webauthn"
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
          Forgot Password?
        </RouterLink>
      </div>
      <button
        type="submit"
        :disabled="loading"
        class="w-full cursor-pointer rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 dark:focus:ring-offset-gray-800"
      >
        {{ loading ? 'Signing In...' : 'Sign In' }}
      </button>
    </form>
    <div v-if="passkeySupported" class="mt-4">
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
        {{ passkeyLoading ? 'Waiting for Passkey…' : 'Sign In with a Passkey' }}
      </button>
    </div>
    <template #footer>
      <p class="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
        Not a member?
        <RouterLink :to="{ name: 'signup' }" class="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400">
          Create an Account
        </RouterLink>
      </p>
    </template>
  </AuthLayout>
</template>
