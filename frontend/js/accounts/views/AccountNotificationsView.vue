<script setup lang="ts">
import { ref, onMounted } from 'vue';
import type { components } from '@/api/schema';
import AccountLayout from '@/layouts/AccountLayout.vue';
import { api, unwrap } from '@/utils/api';
import { showToast } from '@/composables/useToast';

type Preference = components['schemas']['NotificationPreferenceOut'];

const categories = ref<Preference[]>([]);
const loading = ref(true);
const saving = ref<Record<string, boolean>>({});

async function load() {
  loading.value = true;
  try {
    categories.value = await unwrap(api.GET('/api/notifications/preferences/'));
  } catch {
    showToast('Failed to load notification preferences.', 'error');
  } finally {
    loading.value = false;
  }
}

async function toggle(category: Preference, channel: 'in_app' | 'email') {
  const key = `${category.key}:${channel}`;
  saving.value = { ...saving.value, [key]: true };
  const next = !category[channel];
  try {
    const updated = await unwrap(
      api.PATCH('/api/notifications/preferences/{category}/', {
        params: { path: { category: category.key } },
        body: channel === 'in_app' ? { in_app: next } : { email: next },
      }),
    );
    Object.assign(category, updated);
  } catch {
    showToast('Failed to update preference.', 'error');
  } finally {
    saving.value = { ...saving.value, [key]: false };
  }
}

onMounted(load);
</script>

<template>
  <AccountLayout>
    <div class="mb-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Notification Preferences</h2>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Choose how you want to be notified about each type of activity.
      </p>
    </div>

    <div v-if="loading" class="text-sm text-gray-500 dark:text-gray-400">Loading…</div>
    <div
      v-else-if="categories.length === 0"
      class="rounded-lg border border-dashed border-gray-300 bg-gray-50 px-4 py-8 text-center text-sm text-gray-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400"
    >
      No notification preferences are configured yet.
      <br />
      As features are added that send notifications, their categories will appear here.
    </div>
    <div v-else class="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
      <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead class="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th
              scope="col"
              class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400"
            >
              Category
            </th>
            <th
              scope="col"
              class="px-4 py-2 text-center text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400"
            >
              In-App
            </th>
            <th
              scope="col"
              class="px-4 py-2 text-center text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400"
            >
              Email
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
          <tr v-for="cat in categories" :key="cat.key">
            <td class="px-4 py-3 align-top">
              <div class="text-sm font-medium text-gray-900 dark:text-white">
                {{ cat.label }}
              </div>
              <div v-if="cat.description" class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                {{ cat.description }}
              </div>
            </td>
            <td class="px-4 py-3 text-center">
              <input
                type="checkbox"
                class="h-4 w-4 cursor-pointer rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                :checked="cat.in_app"
                :disabled="saving[`${cat.key}:in_app`]"
                @change="toggle(cat, 'in_app')"
              />
            </td>
            <td class="px-4 py-3 text-center">
              <input
                type="checkbox"
                class="h-4 w-4 cursor-pointer rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                :checked="cat.email"
                :disabled="saving[`${cat.key}:email`]"
                @change="toggle(cat, 'email')"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </AccountLayout>
</template>
