<script setup>
import { computed, inject } from 'vue';
import { RouterLink } from 'vue-router';

const appStore = inject('appStore');

const visible = computed(() => {
  if (!appStore.billing?.enabled) return false;
  return appStore.billing.status === 'past_due' || appStore.billing.status === 'unpaid';
});
</script>

<template>
  <div
    v-if="visible"
    class="border-b border-red-200 bg-red-50 px-4 py-2 text-sm text-red-900 dark:border-red-700/40 dark:bg-red-900/20 dark:text-red-200"
  >
    <p>
      <strong>Payment failed.</strong>
      Update your payment method to keep your subscription active.
      <RouterLink
        v-if="appStore.org?.slug && appStore.isOwner"
        :to="{ name: 'org-settings-billing', params: { slug: appStore.org.slug } }"
        class="ml-2 font-medium underline hover:no-underline"
      >
        Update billing →
      </RouterLink>
    </p>
  </div>
</template>
