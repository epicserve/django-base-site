<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useRouter, RouterLink } from 'vue-router';
import {
  TrashIcon,
  CheckIcon,
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  InformationCircleIcon,
} from '@heroicons/vue/24/outline';
import { get, patch, post, del } from '@/utils/api';
import { useNotifications } from '@/composables/useNotifications';
import { showToast } from '@/composables/useToast';
import { relativeTime, userFullName } from '@/utils/format';
import AppModal from '@/components/AppModal.vue';
import UserAvatar from '@/components/UserAvatar.vue';

const router = useRouter();
const { unreadCount, markAllRead: composableMarkAllRead } = useNotifications();

const PAGE_SIZE = 25;

const filterTab = ref('all');
const page = ref(1);
const items = ref([]);
const totalCount = ref(0);
const numPages = ref(1);
const loading = ref(false);

const selectMode = ref(false);
const selectedIds = ref(new Set());
const detailNotification = ref(null);

const hasUnread = computed(() => unreadCount.value > 0);
const allSelected = computed(() => items.value.length > 0 && selectedIds.value.size === items.value.length);
const rangeLabel = computed(() => {
  if (totalCount.value === 0) return '0';
  const start = (page.value - 1) * PAGE_SIZE + 1;
  const end = Math.min(page.value * PAGE_SIZE, totalCount.value);
  return `${start}–${end} of ${totalCount.value}`;
});

async function load() {
  loading.value = true;
  try {
    const params = { page: page.value, page_size: PAGE_SIZE };
    if (filterTab.value === 'unread') params.is_read = 'false';
    const data = await get('/api/notifications/', params);
    items.value = data.results;
    totalCount.value = data.count;
    numPages.value = data.num_pages;
  } catch {
    showToast('Failed to load notifications.', 'error');
  } finally {
    loading.value = false;
  }
}

function exitSelectMode() {
  selectMode.value = false;
  selectedIds.value = new Set();
}

function switchTab(tab) {
  if (filterTab.value === tab) return;
  filterTab.value = tab;
  page.value = 1;
  exitSelectMode();
  load();
}

function gotoPage(target) {
  if (target < 1 || target > numPages.value || target === page.value) return;
  page.value = target;
  exitSelectMode();
  load();
}

function toggleSelect(id) {
  const next = new Set(selectedIds.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  selectedIds.value = next;
}

function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value = new Set();
  } else {
    selectedIds.value = new Set(items.value.map((n) => n.id));
  }
}

function hasNavigableUrl(notification) {
  const url = notification.url;
  return Boolean(url) && url !== '/';
}

async function applyLocalRead(id, isRead) {
  const n = items.value.find((item) => item.id === id);
  if (n) n.is_read = isRead;
}

async function markRead(id) {
  await patch(`/api/notifications/${id}/`, { is_read: true });
  applyLocalRead(id, true);
}

async function handleRowClick(notification) {
  if (selectMode.value) {
    toggleSelect(notification.id);
    return;
  }
  if (!notification.is_read) {
    markRead(notification.id).catch(() => {});
  }
  if (hasNavigableUrl(notification)) {
    router.push(notification.url);
  } else {
    detailNotification.value = { ...notification, is_read: true };
  }
}

async function handleDelete(id) {
  await del(`/api/notifications/${id}/`);
  await load();
}

async function handleBulk(action) {
  const ids = Array.from(selectedIds.value);
  if (!ids.length) return;
  await post('/api/notifications/bulk/', { action, ids });
  exitSelectMode();
  await load();
}

async function handleMarkAllRead() {
  await composableMarkAllRead();
  await load();
}

watch(items, (list) => {
  if (!selectMode.value) return;
  const live = new Set(list.map((n) => n.id));
  const next = new Set();
  selectedIds.value.forEach((id) => {
    if (live.has(id)) next.add(id);
  });
  selectedIds.value = next;
});

onMounted(load);
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <header class="mb-6 flex items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900 dark:text-white">Notifications</h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Your full notification history.</p>
      </div>
      <RouterLink
        :to="{ name: 'account-notifications' }"
        class="text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
      >
        Preferences →
      </RouterLink>
    </header>

    <div class="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
      <!-- Tabs / actions -->
      <div
        class="flex flex-wrap items-center justify-between gap-2 border-b border-gray-200 bg-gray-50 px-3 py-2 dark:border-gray-700 dark:bg-gray-800"
      >
        <div class="flex items-center gap-1">
          <button
            type="button"
            class="cursor-pointer rounded px-2 py-1 text-sm font-medium"
            :class="
              filterTab === 'all'
                ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-white'
                : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200'
            "
            @click="switchTab('all')"
          >
            All
          </button>
          <button
            type="button"
            class="cursor-pointer rounded px-2 py-1 text-sm font-medium"
            :class="
              filterTab === 'unread'
                ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-white'
                : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200'
            "
            @click="switchTab('unread')"
          >
            Unread
            <span v-if="hasUnread" class="ml-1 rounded-full bg-blue-500 px-1.5 text-[10px] font-semibold text-white">
              {{ unreadCount }}
            </span>
          </button>
        </div>

        <div class="flex items-center gap-1">
          <button
            v-if="!selectMode && items.length > 0"
            type="button"
            class="cursor-pointer rounded px-2 py-1 text-xs font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
            @click="selectMode = true"
          >
            Select
          </button>
          <button
            v-if="!selectMode && hasUnread"
            type="button"
            class="cursor-pointer rounded px-2 py-1 text-xs font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
            @click="handleMarkAllRead"
          >
            Mark all read
          </button>
        </div>
      </div>

      <!-- Bulk action bar -->
      <div
        v-if="selectMode"
        class="flex flex-wrap items-center justify-between gap-2 border-b border-gray-200 bg-blue-50 px-3 py-2 text-xs dark:border-gray-700 dark:bg-blue-900/20"
      >
        <button
          type="button"
          class="cursor-pointer font-medium text-gray-700 hover:text-gray-900 dark:text-gray-200"
          @click="toggleSelectAll"
        >
          {{ allSelected ? 'Clear' : 'Select all' }} ({{ selectedIds.size }})
        </button>
        <div class="flex items-center gap-1">
          <button
            type="button"
            class="cursor-pointer rounded px-2 py-1 font-medium text-gray-700 hover:bg-white disabled:cursor-not-allowed disabled:opacity-50 dark:text-gray-200 dark:hover:bg-gray-700"
            :disabled="selectedIds.size === 0"
            @click="handleBulk('mark_read')"
          >
            Mark read
          </button>
          <button
            type="button"
            class="cursor-pointer rounded px-2 py-1 font-medium text-gray-700 hover:bg-white disabled:cursor-not-allowed disabled:opacity-50 dark:text-gray-200 dark:hover:bg-gray-700"
            :disabled="selectedIds.size === 0"
            @click="handleBulk('mark_unread')"
          >
            Mark unread
          </button>
          <button
            type="button"
            class="cursor-pointer rounded px-2 py-1 font-medium text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50 dark:text-red-400 dark:hover:bg-red-900/30"
            :disabled="selectedIds.size === 0"
            @click="handleBulk('delete')"
          >
            Delete
          </button>
          <button
            type="button"
            class="cursor-pointer rounded p-1 text-gray-500 hover:bg-white dark:hover:bg-gray-700"
            aria-label="Cancel selection"
            @click="exitSelectMode"
          >
            <XMarkIcon class="h-4 w-4" />
          </button>
        </div>
      </div>

      <!-- List -->
      <div v-if="loading && items.length === 0" class="px-4 py-12 text-center text-sm text-gray-500 dark:text-gray-400">
        Loading&hellip;
      </div>
      <div v-else-if="items.length === 0" class="px-4 py-12 text-center text-sm text-gray-500 dark:text-gray-400">
        <CheckIcon class="mx-auto mb-2 h-6 w-6 text-gray-400 dark:text-gray-500" />
        <template v-if="filterTab === 'unread'"> You're all caught up. </template>
        <template v-else> No notifications yet. </template>
      </div>
      <ul v-else class="divide-y divide-gray-100 dark:divide-gray-700">
        <li
          v-for="n in items"
          :key="n.id"
          tabindex="0"
          role="button"
          :aria-label="`${n.is_read ? '' : 'Unread, '}${n.title}${n.actor ? ` from ${userFullName(n.actor)}` : ''}`"
          class="group cursor-pointer px-4 py-3 hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-inset dark:hover:bg-gray-800/60"
          :class="!n.is_read ? 'bg-blue-50/40 dark:bg-blue-900/10' : ''"
          @click="handleRowClick(n)"
          @keydown.enter.prevent="handleRowClick(n)"
          @keydown.space.prevent="handleRowClick(n)"
        >
          <div class="flex items-start gap-3">
            <input
              v-if="selectMode"
              type="checkbox"
              class="mt-1 cursor-pointer rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              :checked="selectedIds.has(n.id)"
              @click.stop="toggleSelect(n.id)"
            />
            <UserAvatar v-else-if="n.actor" :src="n.actor.avatar_url || ''" :name="userFullName(n.actor)" size="md" />
            <span
              v-else
              class="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-300"
              aria-hidden="true"
            >
              <InformationCircleIcon class="h-4 w-4" />
            </span>
            <div class="min-w-0 flex-1">
              <div class="flex items-start justify-between gap-2">
                <p
                  class="text-sm"
                  :class="
                    n.is_read ? 'text-gray-700 dark:text-gray-300' : 'font-semibold text-gray-900 dark:text-white'
                  "
                >
                  {{ n.title }}
                </p>
                <span v-if="!n.is_read" class="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-blue-500" aria-hidden="true" />
              </div>
              <p v-if="n.body" class="mt-0.5 line-clamp-2 text-xs text-gray-500 dark:text-gray-400">
                {{ n.body }}
              </p>
              <p class="mt-1 text-[11px] text-gray-400 dark:text-gray-500">
                {{ relativeTime(n.created) }}
              </p>
            </div>
            <button
              v-if="!selectMode"
              type="button"
              class="cursor-pointer shrink-0 rounded p-1 text-gray-400 opacity-0 transition group-hover:opacity-100 group-focus-within:opacity-100 hover:bg-gray-200 hover:text-gray-700 dark:hover:bg-gray-600 dark:hover:text-gray-200"
              aria-label="Delete notification"
              @click.stop="handleDelete(n.id)"
            >
              <TrashIcon class="h-4 w-4" />
            </button>
          </div>
        </li>
      </ul>

      <!-- Pagination -->
      <div
        v-if="items.length > 0"
        class="flex items-center justify-between gap-2 border-t border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400"
      >
        <span>{{ rangeLabel }}</span>
        <div class="flex items-center gap-1">
          <button
            type="button"
            class="cursor-pointer rounded p-1 hover:bg-white disabled:cursor-not-allowed disabled:opacity-40 dark:hover:bg-gray-700"
            :disabled="page <= 1"
            aria-label="Previous page"
            @click="gotoPage(page - 1)"
          >
            <ChevronLeftIcon class="h-4 w-4" />
          </button>
          <span class="px-1">Page {{ page }} of {{ numPages }}</span>
          <button
            type="button"
            class="cursor-pointer rounded p-1 hover:bg-white disabled:cursor-not-allowed disabled:opacity-40 dark:hover:bg-gray-700"
            :disabled="page >= numPages"
            aria-label="Next page"
            @click="gotoPage(page + 1)"
          >
            <ChevronRightIcon class="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>

    <AppModal
      :open="!!detailNotification"
      :title="detailNotification?.title || ''"
      size="lg"
      @close="detailNotification = null"
    >
      <div v-if="detailNotification" class="space-y-4">
        <div v-if="detailNotification.actor" class="flex items-center gap-3">
          <UserAvatar
            :src="detailNotification.actor.avatar_url || ''"
            :name="userFullName(detailNotification.actor)"
            size="md"
          />
          <div class="text-sm">
            <p class="font-medium text-gray-900 dark:text-white">
              {{ userFullName(detailNotification.actor) }}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              {{ relativeTime(detailNotification.created) }}
              · {{ new Date(detailNotification.created).toLocaleString() }}
            </p>
          </div>
        </div>
        <p v-else class="text-xs text-gray-500 dark:text-gray-400">
          {{ relativeTime(detailNotification.created) }}
          · {{ new Date(detailNotification.created).toLocaleString() }}
        </p>
        <div v-if="detailNotification.body" class="whitespace-pre-line text-sm text-gray-700 dark:text-gray-200">
          {{ detailNotification.body }}
        </div>
        <p v-else class="text-sm italic text-gray-500 dark:text-gray-400">No additional details.</p>
      </div>
    </AppModal>
  </div>
</template>
