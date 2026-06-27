<script setup>
import { ref, inject, watch } from 'vue';
import { useRouter } from 'vue-router';
import { post, parseErrors } from '@/utils/api';
import { showToast } from '@/composables/useToast';

const appStore = inject('appStore');
const router = useRouter();

const name = ref('');
const slug = ref('');
const slugManuallyEdited = ref(false);
const errors = ref({});
const submitting = ref(false);

watch(name, (val) => {
  if (slugManuallyEdited.value) return;
  slug.value = val
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40);
});

async function submit() {
  submitting.value = true;
  errors.value = {};
  try {
    const org = await post('/api/organizations/', { name: name.value, slug: slug.value });
    await appStore.fetchContext();
    showToast(`${org.name} created successfully.`);
    router.push({ name: 'org-settings-general', params: { slug: org.slug } });
  } catch (err) {
    errors.value = parseErrors(err);
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="flex min-h-[60vh] items-center justify-center px-4">
    <div class="w-full max-w-sm">
      <div
        class="rounded-xl border border-gray-200 bg-white px-8 py-10 shadow-sm dark:border-gray-700 dark:bg-gray-800"
      >
        <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">
          Create Organization
        </h1>
        <p class="mt-2 text-center text-sm text-gray-500 dark:text-gray-400">Set up a new organization for your team</p>
        <form class="mt-6 space-y-4" @submit.prevent="submit">
          <div>
            <label for="org-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Name</label>
            <input
              id="org-name"
              v-model="name"
              type="text"
              class="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
            />
            <p v-if="errors.name" class="mt-1 text-sm text-red-600">
              {{ errors.name[0] }}
            </p>
          </div>
          <div>
            <label for="org-slug" class="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >Account Name</label
            >
            <input
              id="org-slug"
              v-model="slug"
              type="text"
              class="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
              @input="slugManuallyEdited = true"
            />
            <p v-if="errors.slug" class="mt-1 text-sm text-red-600">
              {{ errors.slug[0] }}
            </p>
          </div>
          <div
            v-if="errors.non_field_errors"
            class="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-300"
          >
            {{ errors.non_field_errors[0] }}
          </div>
          <button
            type="submit"
            :disabled="submitting"
            class="w-full cursor-pointer rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:opacity-50"
          >
            Create
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
