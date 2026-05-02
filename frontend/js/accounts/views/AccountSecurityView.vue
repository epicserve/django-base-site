<script setup>
import { ref, computed, onMounted } from 'vue';
import { RouterLink } from 'vue-router';
import AccountLayout from '@/layouts/AccountLayout.vue';
import { authApi } from '../api';

const authenticators = ref([]);
const loading = ref(true);

const totp = computed(() => authenticators.value.find((a) => a.type === 'totp'));
const recoveryCodes = computed(() => authenticators.value.find((a) => a.type === 'recovery_codes'));
const passkeys = computed(() => authenticators.value.filter((a) => a.type === 'webauthn'));

async function load() {
  loading.value = true;
  try {
    const data = await authApi.listAuthenticators();

    authenticators.value = data.data || [];
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <AccountLayout>
    <div
      v-if="loading"
      class="text-sm text-gray-500 dark:text-gray-400"
    >
      Loading…
    </div>
    <div
      v-else
      class="space-y-6"
    >
      <section class="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
              Authenticator app (TOTP)
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              <span v-if="totp">Enabled. Use your authenticator app to generate codes when signing in.</span>
              <span v-else>Use Google Authenticator, 1Password, Authy, or similar to add a second factor.</span>
            </p>
          </div>
          <RouterLink
            :to="{ name: 'account-totp' }"
            class="cursor-pointer rounded-md bg-blue-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {{ totp ? 'Manage' : 'Set up' }}
          </RouterLink>
        </div>
      </section>

      <section class="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
              Recovery codes
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              <span v-if="recoveryCodes">
                {{ recoveryCodes.unused_code_count }} of {{ recoveryCodes.total_code_count }} unused.
              </span>
              <span v-else>Generated when you enable an authenticator app. Save them somewhere safe.</span>
            </p>
          </div>
          <RouterLink
            v-if="recoveryCodes"
            :to="{ name: 'account-recovery-codes' }"
            class="cursor-pointer rounded-md border border-gray-300 bg-white px-3.5 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
          >
            View
          </RouterLink>
        </div>
      </section>

      <section class="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div class="flex items-center justify-between mb-3">
          <div>
            <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
              Passkeys
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Sign in with Touch ID, Windows Hello, your phone, or a hardware security key — no password needed.
            </p>
          </div>
          <RouterLink
            :to="{ name: 'account-passkeys' }"
            class="cursor-pointer rounded-md bg-blue-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {{ passkeys.length ? 'Manage' : 'Add' }}
          </RouterLink>
        </div>
        <p
          v-if="passkeys.length"
          class="text-xs text-gray-500 dark:text-gray-400"
        >
          {{ passkeys.length }} passkey{{ passkeys.length === 1 ? '' : 's' }} registered.
        </p>
      </section>
    </div>
  </AccountLayout>
</template>
