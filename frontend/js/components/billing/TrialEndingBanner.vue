<script setup>
import { computed, inject, ref, watchEffect } from 'vue';
import { RouterLink } from 'vue-router';
import { XMarkIcon } from '@heroicons/vue/20/solid';

const appStore = inject('appStore');
const dismissed = ref(false);

function storageKey(trialEnd) {
  return `trialBanner.dismissed.${trialEnd}`;
}

watchEffect(() => {
  const trialEnd = appStore.billing?.trial_end;
  if (!trialEnd) {
    dismissed.value = false;
    return;
  }
  dismissed.value = window.localStorage.getItem(storageKey(trialEnd)) === '1';
});

const daysLeft = computed(() => {
  if (!appStore.billing?.trial_end) return null;
  const ms = new Date(appStore.billing.trial_end).getTime() - Date.now();
  return Math.max(0, Math.ceil(ms / (1000 * 60 * 60 * 24)));
});

const visible = computed(() => {
  if (!appStore.billing?.enabled) return false;
  if (appStore.billing.status !== 'trialing') return false;
  if (!appStore.billing.trial_end) return false;
  if (daysLeft.value === null || daysLeft.value > 7) return false;
  return !dismissed.value;
});

function dismiss() {
  if (appStore.billing?.trial_end) {
    window.localStorage.setItem(storageKey(appStore.billing.trial_end), '1');
  }
  dismissed.value = true;
}
</script>

<template>
  <div
    v-if="visible"
    class="flex items-center justify-between gap-3 border-b border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-900 dark:border-blue-700/40 dark:bg-blue-900/20 dark:text-blue-200"
  >
    <p>
      Your trial ends in {{ daysLeft }} {{ daysLeft === 1 ? 'day' : 'days' }}.
      <RouterLink
        v-if="appStore.org?.slug && appStore.isOwner"
        :to="{ name: 'org-settings-billing', params: { slug: appStore.org.slug } }"
        class="ml-2 font-medium underline hover:no-underline"
      >
        Add a payment method
      </RouterLink>
    </p>
    <button
      type="button"
      class="cursor-pointer rounded p-1 hover:bg-blue-100 dark:hover:bg-blue-900/40"
      aria-label="Dismiss"
      @click="dismiss"
    >
      <XMarkIcon class="h-4 w-4" />
    </button>
  </div>
</template>
