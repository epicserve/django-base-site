<script setup>
import { ref, onMounted } from 'vue';
import { get, patch } from '@/utils/api';
import { showToast } from '@/composables/useToast';
import AppToast from '@/components/AppToast.vue';

const SETTINGS_URL = '/api/organization-settings/';

const billingEmail = ref('');
const billingEmailError = ref('');
const loading = ref(true);

async function loadSettings() {
  try {
    const data = await get(SETTINGS_URL);
    billingEmail.value = data.billing_email || '';
  } catch {
    showToast('Failed to load settings.', 'error');
  } finally {
    loading.value = false;
  }
}

async function saveBillingEmail() {
  billingEmailError.value = '';
  try {
    await patch(`${SETTINGS_URL}update_settings/`, { billing_email: billingEmail.value || null });
    showToast('Billing email updated.');
  } catch {
    billingEmailError.value = 'Failed to update billing email.';
  }
}

onMounted(loadSettings);
</script>

<template>
  <div class="max-w-lg">
    <div
      v-if="loading"
      class="text-sm text-gray-400"
    >
      Loading...
    </div>
    <div v-else>
      <label
        for="billing-email"
        class="block text-sm font-medium text-gray-700 dark:text-gray-300"
      >Billing Email</label>
      <div class="flex items-center gap-2 mt-1 max-w-sm">
        <input
          id="billing-email"
          v-model="billingEmail"
          type="email"
          placeholder="billing@example.com"
          class="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
          @keyup.enter="saveBillingEmail"
        >
        <button
          type="button"
          class="cursor-pointer rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
          @click="saveBillingEmail"
        >
          Save
        </button>
      </div>
      <p
        v-if="billingEmailError"
        class="mt-1 text-sm text-red-600"
      >
        {{ billingEmailError }}
      </p>
      <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
        The email address that organization receipts and invoices will be sent to.
      </p>
    </div>
    <AppToast />
  </div>
</template>
