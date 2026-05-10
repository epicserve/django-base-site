<script setup>
import { inject } from 'vue';
import { RouterLink } from 'vue-router';
import ManageTeamsApp from '@/apps/ManageTeamsApp.vue';
import FeatureGate from '@/components/FeatureGate.vue';

const appStore = inject('appStore');
</script>

<template>
  <FeatureGate feature="teams">
    <ManageTeamsApp
      team-list-url="/api/teams/"
      organization-member-list-url="/api/organization-members/"
    />
    <template #fallback>
      <div class="rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center dark:border-gray-700 dark:bg-gray-800">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
          Teams aren't included on your current plan
        </h2>
        <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
          Upgrade to unlock teams and team-based access controls.
        </p>
        <RouterLink
          v-if="appStore.isOwner"
          :to="{ name: 'org-settings-billing', params: { slug: appStore.org.slug } }"
          class="mt-4 inline-flex cursor-pointer rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Upgrade plan
        </RouterLink>
        <p
          v-else
          class="mt-4 text-sm text-gray-500 dark:text-gray-400"
        >
          Contact your org owner to upgrade.
        </p>
      </div>
    </template>
  </FeatureGate>
</template>
