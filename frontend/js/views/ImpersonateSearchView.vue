<script setup>
import { nextTick, ref, watch } from 'vue';
import { get } from '@/utils/api';
import UserAvatar from '@/components/UserAvatar.vue';

const query = ref('');
const results = ref([]);
const loading = ref(false);
const selectedIndex = ref(-1);
const rowRefs = ref([]);
let debounceTimer = null;

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(^|;\\s*)${name}=([^;]+)`));
  return match ? decodeURIComponent(match[2]) : null;
}

watch(query, (q) => {
  clearTimeout(debounceTimer);
  if (q.trim().length < 2) {
    results.value = [];
    selectedIndex.value = -1;
    return;
  }
  debounceTimer = setTimeout(async () => {
    loading.value = true;
    try {
      rowRefs.value = [];
      results.value = await get('/api/users/impersonate-search/', { q: q.trim() });
      selectedIndex.value = results.value.length ? 0 : -1;
    } finally {
      loading.value = false;
    }
  }, 250);
});

function setRowRef(el, index) {
  if (el) {
    rowRefs.value[index] = el;
  }
}

async function focusRow(index) {
  selectedIndex.value = index;
  await nextTick();
  rowRefs.value[index]?.focus();
}

function onSearchKeydown(e) {
  if (!results.value.length) return;
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    focusRow(0);
  } else if (e.key === 'Enter' && selectedIndex.value >= 0) {
    e.preventDefault();
    impersonate(results.value[selectedIndex.value].id);
  }
}

function onRowKeydown(e, index) {
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    if (index < results.value.length - 1) {
      focusRow(index + 1);
    }
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    if (index === 0) {
      selectedIndex.value = -1;
      document.getElementById('search')?.focus();
    } else {
      focusRow(index - 1);
    }
  } else if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    impersonate(results.value[index].id);
  }
}

function impersonate(userId) {
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/hijack/acquire/';

  const csrf = document.createElement('input');
  csrf.type = 'hidden';
  csrf.name = 'csrfmiddlewaretoken';
  csrf.value = getCookie('csrftoken') || '';
  form.appendChild(csrf);

  const pk = document.createElement('input');
  pk.type = 'hidden';
  pk.name = 'user_pk';
  pk.value = String(userId);
  form.appendChild(pk);

  const next = document.createElement('input');
  next.type = 'hidden';
  next.name = 'next';
  next.value = '/';
  form.appendChild(next);

  document.body.appendChild(form);
  form.submit();
}
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <div class="mb-6">
      <h1 class="text-2xl font-semibold text-gray-900 dark:text-white">
        Impersonate User
      </h1>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Search for the user you want to impersonate
      </p>
    </div>
    <div class="rounded-xl border border-gray-200 bg-white px-8 py-8 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <label
        class="sr-only"
        for="search"
      >Search</label>
      <input
        id="search"
        v-model="query"
        type="search"
        class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm shadow-sm placeholder:text-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
        placeholder="Search by name, username, or email..."
        autofocus
        @keydown="onSearchKeydown"
      >
    </div>

    <div
      v-if="results.length"
      class="mt-6 rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
    >
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead>
            <tr class="border-b border-gray-200 dark:border-gray-700">
              <th class="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Name
              </th>
              <th class="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Email
              </th>
              <th class="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Username
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <tr
              v-for="(user, index) in results"
              :key="user.id"
              :ref="(el) => setRowRef(el, index)"
              tabindex="0"
              class="cursor-pointer transition hover:bg-gray-50 focus:bg-blue-50 focus:outline-none dark:hover:bg-gray-700/50 dark:focus:bg-blue-900/30"
              :class="{ 'bg-blue-50 dark:bg-blue-900/30': selectedIndex === index }"
              @click="impersonate(user.id)"
              @focus="selectedIndex = index"
              @keydown="onRowKeydown($event, index)"
            >
              <td class="px-6 py-3">
                <span class="inline-flex items-center gap-2 font-medium text-blue-600 dark:text-blue-400">
                  <UserAvatar
                    :src="user.avatar_url || ''"
                    :name="user.full_name || user.username || ''"
                    size="md"
                  />
                  {{ user.full_name || user.username }}
                </span>
              </td>
              <td class="px-6 py-3 text-gray-700 dark:text-gray-300">
                {{ user.email }}
              </td>
              <td class="px-6 py-3 text-gray-700 dark:text-gray-300">
                {{ user.username }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div
      v-else-if="query.trim().length >= 2 && !loading"
      class="mt-6 rounded-xl border border-gray-200 bg-white px-8 py-10 text-center shadow-sm dark:border-gray-700 dark:bg-gray-800"
    >
      <p class="text-gray-500 dark:text-gray-400">
        No users found matching "{{ query }}"
      </p>
    </div>
  </div>
</template>
