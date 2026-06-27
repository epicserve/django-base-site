<script setup>
import { computed, onMounted, ref } from 'vue';
import { get, post } from '@/utils/api';
import { showToast } from '@/composables/useToast';
import SearchableSelect from '@/components/SearchableSelect.vue';

const users = ref([]);
const selectedUserId = ref('');
const sendEmail = ref(true);
const sendInApp = ref(true);
const loading = ref(false);
const sending = ref(false);

const userOptions = computed(() =>
  users.value.map((u) => ({
    value: String(u.id),
    label: `${u.full_name} (${u.email})`,
  })),
);

const canSubmit = computed(() => Boolean(selectedUserId.value) && (sendEmail.value || sendInApp.value));

onMounted(async () => {
  loading.value = true;
  try {
    users.value = await get('/api/test-notifications/staff-users/');
    if (users.value.length) {
      selectedUserId.value = String(users.value[0].id);
    }
  } catch (err) {
    showToast(err?.data?.detail || 'Failed to load staff users.', 'error');
  } finally {
    loading.value = false;
  }
});

async function submit() {
  if (!canSubmit.value) return;
  sending.value = true;
  try {
    const data = await post('/api/test-notifications/', {
      user_id: Number(selectedUserId.value),
      send_email: sendEmail.value,
      send_in_app: sendInApp.value,
    });
    showToast(data.message || 'Test notification sent.', 'success');
  } catch (err) {
    showToast(err?.data?.detail || 'Failed to send test notification.', 'error');
  } finally {
    sending.value = false;
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <div class="mb-6">
      <h1 class="text-2xl font-semibold text-gray-900 dark:text-white">Test Notifications</h1>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Send a test notification to a staff user to verify email and in-app notification delivery.
      </p>
    </div>
    <form
      class="rounded-xl border border-gray-200 bg-white px-8 py-8 shadow-sm dark:border-gray-700 dark:bg-gray-800"
      @submit.prevent="submit"
    >
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300"> Recipient </label>
      <div class="mt-1">
        <SearchableSelect
          v-model="selectedUserId"
          :options="userOptions"
          :placeholder="loading ? 'Loading…' : 'Select a staff user...'"
        />
      </div>

      <label class="mt-4 flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
        <input
          v-model="sendEmail"
          type="checkbox"
          class="h-4 w-4 cursor-pointer rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
        />
        Send email notification
      </label>

      <label class="mt-2 flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
        <input
          v-model="sendInApp"
          type="checkbox"
          class="h-4 w-4 cursor-pointer rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
        />
        Send in app notification
      </label>

      <div class="mt-6 flex justify-end">
        <button
          type="submit"
          :disabled="sending || loading || !canSubmit"
          class="cursor-pointer rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {{ sending ? 'Sending…' : 'Send' }}
        </button>
      </div>
    </form>
  </div>
</template>
