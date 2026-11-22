<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink, RouterView, useRoute } from 'vue-router';
import { useAppStore } from '@/stores/app';
import { orgSettingsTabs } from '@/utils/orgSettings';

const appStore = useAppStore();
const route = useRoute();

const tabs = computed(() =>
  orgSettingsTabs(appStore).map((tab) => ({ ...tab, to: { name: tab.name, params: { slug: route.params.slug } } })),
);
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
      {{ appStore.org ? appStore.org.name : '' }} Settings
    </h1>
    <div class="border-b border-gray-200 dark:border-gray-700 mb-6">
      <nav class="flex flex-wrap gap-4 -mb-px">
        <RouterLink
          v-for="tab in tabs"
          :key="tab.name"
          :to="tab.to"
          :class="[
            'inline-block cursor-pointer pb-3 text-sm font-medium border-b-2',
            route.name === tab.name
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : [
                  'border-transparent text-gray-500',
                  'hover:text-gray-700 hover:border-gray-300',
                  'dark:text-gray-400 dark:hover:text-gray-300',
                ].join(' '),
          ]"
        >
          {{ tab.label }}
        </RouterLink>
      </nav>
    </div>
    <RouterView />
  </div>
</template>
