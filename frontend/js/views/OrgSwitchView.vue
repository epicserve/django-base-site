<script setup>
import { ref, inject, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { get, post } from '@/utils/api';
import { showToast } from '@/composables/useToast';

const appStore = inject('appStore');
const router = useRouter();
const orgs = ref([]);
const loading = ref(true);

onMounted(async () => {
  orgs.value = await get('/api/organizations/switch-list/');
  loading.value = false;
});

async function selectOrg(slug) {
  await appStore.switchOrg(slug);
  router.push('/');
}

async function signOutOrg() {
  await appStore.signOutOrg();
  router.push('/');
}

async function setPrimary(slug) {
  const result = await post(`/api/organizations/${slug}/set-primary/`);
  showToast(result.is_primary ? 'Primary company updated.' : 'Primary company removed.');
  orgs.value = await get('/api/organizations/switch-list/');
}
</script>

<template>
  <div class="mx-auto max-w-md">
    <div class="border-b border-gray-200 dark:border-gray-700 pb-3 mb-4">
      <h2 class="text-2xl font-semibold text-gray-900 dark:text-white">Switch Company</h2>
    </div>
    <div v-if="loading" class="text-center py-8 text-gray-400">Loading...</div>
    <div
      v-else
      class="divide-y divide-gray-200 rounded-md border border-gray-200 dark:divide-gray-700 dark:border-gray-700"
    >
      <div class="relative">
        <button
          class="cursor-pointer block w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
          @click="signOutOrg"
        >
          Personal Space
        </button>
        <div v-if="!appStore.org || !appStore.org.slug" class="absolute right-3 top-1/2 -translate-y-1/2">
          <span
            class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 ring-1 ring-inset ring-gray-500/20 dark:bg-gray-700 dark:text-gray-300 dark:ring-gray-500/30"
            >Current</span
          >
        </div>
      </div>
      <div v-for="org in orgs" :key="org.id" class="relative">
        <button
          class="cursor-pointer block w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
          @click="selectOrg(org.slug)"
        >
          {{ org.name }}
        </button>
        <div class="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1.5">
          <span
            v-if="org.is_current"
            class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 ring-1 ring-inset ring-gray-500/20 dark:bg-gray-700 dark:text-gray-300 dark:ring-gray-500/30"
            >Current</span
          >
          <button
            v-if="org.is_primary"
            class="relative z-10 inline-flex cursor-pointer items-center rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700 ring-1 ring-inset ring-indigo-600/20 hover:bg-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-300 dark:ring-indigo-500/30 dark:hover:bg-indigo-900/50"
            title="Click to remove primary"
            @click.stop="setPrimary(org.slug)"
          >
            Primary
          </button>
          <button
            v-else
            class="relative z-10 cursor-pointer rounded-md px-2 py-0.5 text-xs text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-300"
            @click.stop="setPrimary(org.slug)"
          >
            Make primary
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
