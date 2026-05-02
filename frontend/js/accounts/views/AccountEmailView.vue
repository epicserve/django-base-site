<script setup>
import { ref, onMounted } from 'vue';
import AccountLayout from '@/layouts/AccountLayout.vue';
import { authApi, parseAllauthErrors } from '../api';
import { showToast } from '../../composables/useToast';

const emails = ref([]);
const selectedEmail = ref('');
const newEmail = ref('');
const addErrors = ref({});
const loading = ref(false);

function toastError(err, fallback = 'An error occurred.') {
  const parsed = err?.data ? parseAllauthErrors(err.data) : {};
  const messages = [
    ...(parsed.non_field_errors || []),
    ...Object.entries(parsed)
      .filter(([k]) => k !== 'non_field_errors')
      .flatMap(([, v]) => v),
  ];
  showToast(messages.length ? messages.join(' ') : fallback, 'error');
}

async function loadEmails() {
  try {
    const data = await authApi.listEmails();

    emails.value = data.data || [];
    const primary = emails.value.find((e) => e.primary);

    if (primary) selectedEmail.value = primary.email;
  } catch {
    // Silently fail
  }
}

onMounted(loadEmails);

async function makePrimary() {
  if (!selectedEmail.value) return;
  loading.value = true;
  try {
    await authApi.setPrimaryEmail(selectedEmail.value);
    showToast('Primary email updated.');
    await loadEmails();
  } catch (err) {
    toastError(err);
  } finally {
    loading.value = false;
  }
}

async function resendVerification() {
  if (!selectedEmail.value) return;
  loading.value = true;
  try {
    await authApi.resendVerification(selectedEmail.value);
    showToast('Verification email sent.');
  } catch (err) {
    if (err?.response?.status === 403) {
      showToast('A verification email was sent recently. Please wait a few minutes before trying again.', 'error');
    } else {
      toastError(err);
    }
  } finally {
    loading.value = false;
  }
}

async function removeEmail() {
  if (!selectedEmail.value) return;
  if (!confirm('Do you really want to remove the selected e-mail address?')) return;
  loading.value = true;
  try {
    await authApi.removeEmail(selectedEmail.value);
    showToast('Email removed.');
    await loadEmails();
  } catch (err) {
    toastError(err);
  } finally {
    loading.value = false;
  }
}

async function addEmail() {
  if (!newEmail.value) return;
  loading.value = true;
  addErrors.value = {};
  try {
    await authApi.addEmail(newEmail.value);
    newEmail.value = '';
    showToast('Email added. Check your inbox for a verification link.');
    await loadEmails();
  } catch (err) {
    const parsed = err?.data ? parseAllauthErrors(err.data) : {};
    addErrors.value = parsed;
    if (parsed.non_field_errors?.length || !err?.data) {
      showToast(parsed.non_field_errors?.join(' ') || 'An error occurred.', 'error');
    }
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <AccountLayout>
    <div
      v-if="emails.length"
      class="space-y-2"
    >
      <label
        v-for="(addr, idx) in emails"
        :key="addr.email"
        :for="`email_radio_${idx}`"
        class="cursor-pointer flex items-center justify-between rounded-lg border px-4 py-3 transition"
        :class="addr.primary
          ? 'border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/30'
          : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600'"
      >
        <div class="flex items-center gap-3">
          <input
            :id="`email_radio_${idx}`"
            v-model="selectedEmail"
            type="radio"
            :value="addr.email"
            class="text-blue-600 focus:ring-blue-500"
          >
          <div>
            <span
              class="text-sm text-gray-900 dark:text-white"
              :class="{ 'font-medium': addr.primary }"
            >
              {{ addr.email }}
            </span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span
            v-if="addr.primary"
            class="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
          >
            Primary
          </span>
          <span
            v-if="addr.verified"
            class="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400"
          >
            <svg
              class="h-3.5 w-3.5 text-green-500"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <!-- eslint-disable max-len -->
              <path
                fill-rule="evenodd"
                d="M16.704 4.153a.75.75 0 0 1 .143 1.052l-8 10.5a.75.75 0 0 1-1.127.075l-4.5-4.5a.75.75 0 0 1 1.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 0 1 1.05-.143Z"
                clip-rule="evenodd"
              />
              <!-- eslint-enable max-len -->
            </svg>
            Verified
          </span>
          <span
            v-else
            class="inline-flex items-center rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300"
          >
            Unverified
          </span>
        </div>
      </label>
    </div>
    <p
      v-else
      class="text-gray-700 dark:text-gray-300"
    >
      <strong>Warning:</strong> You currently do not have any e-mail address set up.
      You should really add an e-mail address so you can receive notifications, reset your password, etc.
    </p>

    <div
      v-if="emails.length"
      class="mt-4 flex items-center gap-3"
    >
      <button
        type="button"
        :disabled="loading"
        class="cursor-pointer rounded-md bg-blue-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-blue-700 transition disabled:opacity-50"
        @click="makePrimary"
      >
        Make Primary
      </button>
      <button
        type="button"
        :disabled="loading"
        class="cursor-pointer rounded-md border border-gray-300 bg-white px-3.5 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 transition disabled:opacity-50"
        @click="resendVerification"
      >
        Re-send Verification
      </button>
      <button
        type="button"
        :disabled="loading"
        class="cursor-pointer rounded-md px-3.5 py-2 text-sm font-medium text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30 transition disabled:opacity-50"
        @click="removeEmail"
      >
        Remove
      </button>
    </div>

    <div class="mt-8 border-t border-gray-200 dark:border-gray-700 pt-6">
      <h2 class="text-sm font-medium text-gray-900 dark:text-white mb-3">
        Add E-mail Address
      </h2>
      <form
        class="flex items-end gap-3"
        @submit.prevent="addEmail"
      >
        <div class="flex-1">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            E-mail
          </label>
          <input
            v-model="newEmail"
            type="email"
            placeholder="New email address"
            class="block w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm shadow-sm placeholder:text-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder:text-gray-500"
          >
          <p
            v-for="err in (addErrors.email || [])"
            :key="err"
            class="mt-1 text-sm text-red-600 dark:text-red-400"
          >
            {{ err }}
          </p>
        </div>
        <div class="mb-0.5">
          <button
            type="submit"
            :disabled="loading"
            class="cursor-pointer rounded-md bg-blue-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-blue-700 transition disabled:opacity-50"
          >
            Add
          </button>
        </div>
      </form>
    </div>
  </AccountLayout>
</template>
