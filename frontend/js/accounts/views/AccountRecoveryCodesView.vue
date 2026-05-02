<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import AccountLayout from '@/layouts/AccountLayout.vue';
import { authApi } from '../api';
import { showToast } from '../../composables/useToast';

const router = useRouter();
const codes = ref([]);
const unused = ref([]);
const total = ref(0);
const loading = ref(true);

async function load() {
  loading.value = true;
  try {
    const data = await authApi.listRecoveryCodes();
    const payload = data.data || {};

    codes.value = payload.unused_codes || payload.codes || [];
    unused.value = payload.unused_codes || [];
    total.value = payload.total_code_count || codes.value.length;
  } catch (err) {
    if (err.response?.status === 401) {
      router.push({ name: 'account-reauthenticate', query: { next: '/accounts/security/recovery-codes/' } });
    }
  } finally {
    loading.value = false;
  }
}

async function regenerate() {
  if (!confirm('Generate a new set of recovery codes? Your existing codes will stop working.')) return;
  loading.value = true;
  try {
    await authApi.regenerateRecoveryCodes();
    showToast('New recovery codes generated.');
    await load();
  } catch (err) {
    if (err.response?.status === 401) {
      router.push({ name: 'account-reauthenticate', query: { next: '/accounts/security/recovery-codes/' } });
    }
  } finally {
    loading.value = false;
  }
}

function copyAll() {
  navigator.clipboard.writeText(codes.value.join('\n'));
  showToast('Copied to clipboard.');
}

onMounted(load);
</script>

<template>
  <AccountLayout>
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
      Recovery codes
    </h2>
    <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
      Each code can be used once if you lose access to your authenticator app. Store them somewhere safe.
    </p>

    <div
      v-if="loading"
      class="text-sm text-gray-500 dark:text-gray-400"
    >
      Loading…
    </div>

    <div v-else>
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-4 grid grid-cols-2 gap-2 font-mono text-sm">
        <div
          v-for="c in codes"
          :key="c"
          class="text-gray-900 dark:text-white"
        >
          {{ c }}
        </div>
      </div>
      <p
        v-if="total"
        class="mt-2 text-xs text-gray-500 dark:text-gray-400"
      >
        {{ unused.length }} of {{ total }} unused.
      </p>

      <div class="mt-4 flex items-center gap-3">
        <button
          type="button"
          :disabled="!codes.length"
          class="cursor-pointer rounded-md border border-gray-300 bg-white px-3.5 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700 disabled:opacity-50"
          @click="copyAll"
        >
          Copy all
        </button>
        <button
          type="button"
          :disabled="loading"
          class="cursor-pointer rounded-md bg-blue-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          @click="regenerate"
        >
          Regenerate
        </button>
      </div>
    </div>
  </AccountLayout>
</template>
