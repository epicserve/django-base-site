<script setup>
import { ref, onMounted } from 'vue';
import AccountLayout from '@/layouts/AccountLayout.vue';
import FormField from '../components/FormField.vue';
import FormErrors from '../components/FormErrors.vue';
import { authApi, parseAllauthErrors } from '../api';
import { showToast } from '../../composables/useToast';

const isActive = ref(false);
const secret = ref('');
const totpUrl = ref('');
const code = ref('');
const errors = ref({});
const loading = ref(true);

const needsReauth = ref(false);
const reauthPassword = ref('');
const reauthErrors = ref({});
const reauthLoading = ref(false);
let pendingAction = null;

async function load() {
  loading.value = true;
  errors.value = {};
  try {
    const data = await authApi.getTotpStatus();

    isActive.value = true;
    secret.value = data.data?.secret || '';
  } catch (err) {
    if (err.response?.status === 404) {
      isActive.value = false;
      const setupData = err.data?.meta || err.data?.data || {};

      secret.value = setupData.secret || '';
      totpUrl.value = setupData.totp_url || '';
    }
  } finally {
    loading.value = false;
  }
}

function isReauthRequired(err) {
  if (err.response?.status !== 401) return false;
  const flows = err.data?.data?.flows || [];

  return flows.some((f) => f.id === 'reauthenticate' || f.id === 'mfa_reauthenticate');
}

async function activate() {
  errors.value = {};
  loading.value = true;
  try {
    await authApi.activateTotp(code.value);
    showToast('Authenticator app enabled.');
    code.value = '';
    await load();
  } catch (err) {
    if (isReauthRequired(err)) {
      // Stash the activate action so we can retry it without regenerating the
      // TOTP secret on the page (a fresh GET would mint a new one and break
      // the QR the user already scanned).
      pendingAction = activate;
      needsReauth.value = true;
      loading.value = false;
      return;
    }
    errors.value = err.data ? parseAllauthErrors(err.data) : {};
  } finally {
    loading.value = false;
  }
}

async function deactivate() {
  if (!confirm('Disable the authenticator app for this account?')) return;
  loading.value = true;
  try {
    await authApi.deactivateTotp();
    showToast('Authenticator app disabled.');
    isActive.value = false;
    await load();
  } catch (err) {
    if (isReauthRequired(err)) {
      pendingAction = deactivate;
      needsReauth.value = true;
      loading.value = false;
      return;
    }
    errors.value = err.data ? parseAllauthErrors(err.data) : {};
  } finally {
    loading.value = false;
  }
}

async function submitReauth() {
  reauthErrors.value = {};
  reauthLoading.value = true;
  try {
    await authApi.reauthenticate(reauthPassword.value);
    needsReauth.value = false;
    reauthPassword.value = '';
    if (pendingAction) {
      const action = pendingAction;

      pendingAction = null;
      await action();
    }
  } catch (err) {
    reauthErrors.value = err.data ? parseAllauthErrors(err.data) : { non_field_errors: ['Could not verify password.'] };
  } finally {
    reauthLoading.value = false;
  }
}

function cancelReauth() {
  needsReauth.value = false;
  reauthPassword.value = '';
  reauthErrors.value = {};
  pendingAction = null;
}

onMounted(load);
</script>

<template>
  <AccountLayout>
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Authenticator app (TOTP)</h2>

    <div v-if="loading" class="text-sm text-gray-500 dark:text-gray-400">Loading…</div>

    <div v-else-if="isActive" class="space-y-4">
      <p class="text-sm text-gray-700 dark:text-gray-300">An authenticator app is currently enabled on this account.</p>
      <button
        type="button"
        :disabled="loading"
        class="cursor-pointer rounded-md px-3.5 py-2 text-sm font-medium text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30 disabled:opacity-50"
        @click="deactivate"
      >
        Disable authenticator app
      </button>
    </div>

    <div v-else class="space-y-4">
      <p class="text-sm text-gray-700 dark:text-gray-300">
        Scan the code below with your authenticator app, then enter the 6-digit code it generates to confirm.
      </p>
      <div v-if="totpUrl" class="rounded-md border border-gray-200 bg-white dark:border-gray-700 p-4 inline-block">
        <img
          :src="`/qr/?data=${encodeURIComponent(totpUrl)}`"
          alt="TOTP QR code"
          class="block"
          width="180"
          height="180"
        />
      </div>
      <p v-if="secret" class="text-xs text-gray-500 dark:text-gray-400">
        Or enter this key manually: <code class="font-mono">{{ secret }}</code>
      </p>

      <form class="space-y-4 max-w-xs" @submit.prevent="activate">
        <FormErrors :errors="errors.non_field_errors || []" />
        <FormField
          v-model="code"
          label="6-digit code"
          autocomplete="one-time-code"
          inputmode="numeric"
          :errors="errors.code || []"
        />
        <button
          type="submit"
          :disabled="loading || !code"
          class="cursor-pointer rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {{ loading ? 'Verifying…' : 'Enable' }}
        </button>
      </form>
    </div>

    <div v-if="needsReauth" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div class="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white">Confirm your password</h3>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Re-enter your password to continue.</p>
        <form class="mt-4 space-y-3" @submit.prevent="submitReauth">
          <FormErrors :errors="reauthErrors.non_field_errors || []" />
          <FormField
            v-model="reauthPassword"
            type="password"
            label="Password"
            autocomplete="current-password"
            :errors="reauthErrors.password || []"
          />
          <div class="flex items-center justify-end gap-2">
            <button
              type="button"
              class="cursor-pointer rounded-md border border-gray-300 bg-white px-3.5 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
              @click="cancelReauth"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="reauthLoading || !reauthPassword"
              class="cursor-pointer rounded-md bg-blue-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {{ reauthLoading ? 'Verifying…' : 'Continue' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </AccountLayout>
</template>
