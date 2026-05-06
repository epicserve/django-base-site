<script setup>
import { ref, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { BellIcon, TrashIcon, CheckIcon, XMarkIcon } from '@heroicons/vue/24/outline';
import { BellAlertIcon } from '@heroicons/vue/24/solid';
import { useNotifications } from '../composables/useNotifications';
import { relativeTime, userFullName } from '../utils/format';
import UserAvatar from './UserAvatar.vue';

const router = useRouter();
const {
  unreadCount,
  notifications,
  loading,
  fetchList,
  markRead,
  deleteOne,
  bulkAction,
  markAllRead,
  setDropdownOpen,
} = useNotifications();

const isOpen = ref(false);
const selectMode = ref(false);
const selectedIds = ref(new Set());

const filterTab = ref('unread');
const hasUnread = computed(() => unreadCount.value > 0);
const badgeLabel = computed(() => (unreadCount.value > 99 ? '99+' : String(unreadCount.value)));
const allSelected = computed(() => (
  notifications.value.length > 0 && selectedIds.value.size === notifications.value.length
));

function toggleDropdown() {
  isOpen.value = !isOpen.value;
  if (isOpen.value) {
    filterTab.value = hasUnread.value ? 'unread' : 'all';
    fetchList({ filter: filterTab.value });
  } else {
    exitSelectMode();
  }
}

function switchTab(tab) {
  if (filterTab.value === tab) return;
  filterTab.value = tab;
  exitSelectMode();
  fetchList({ filter: tab });
}

function exitSelectMode() {
  selectMode.value = false;
  selectedIds.value = new Set();
}

function toggleSelectMode() {
  if (selectMode.value) {
    exitSelectMode();
  } else {
    selectMode.value = true;
  }
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
    selectedIds.value = new Set(notifications.value.map((n) => n.id));
  }
}

async function handleRowClick(notification) {
  if (selectMode.value) {
    toggleSelect(notification.id);
    return;
  }
  if (!notification.is_read) {
    markRead(notification.id).catch(() => {});
  }
  isOpen.value = false;
  if (notification.url) {
    router.push(notification.url);
  }
}

async function handleDelete(id) {
  await deleteOne(id);
}

async function handleBulk(action) {
  const ids = Array.from(selectedIds.value);
  if (!ids.length) return;
  await bulkAction(action, ids);
  exitSelectMode();
}

// keep select mode in sync when list changes beneath us
watch(notifications, (list) => {
  if (!selectMode.value) return;
  const live = new Set(list.map((n) => n.id));
  const next = new Set();
  selectedIds.value.forEach((id) => {
    if (live.has(id)) next.add(id);
  });
  selectedIds.value = next;
});

function handleOutside(e) {
  if (!e.target.closest('[data-dropdown="notifications"]')) {
    isOpen.value = false;
    exitSelectMode();
  }
}

watch(isOpen, (open) => {
  setDropdownOpen(open);
  if (open) {
    document.addEventListener('click', handleOutside);
  } else {
    document.removeEventListener('click', handleOutside);
  }
});
</script>

<template>
  <div
    class="relative"
    data-dropdown="notifications"
  >
    <button
      type="button"
      class="cursor-pointer relative flex items-center rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200"
      :aria-label="hasUnread ? `Notifications, ${unreadCount} unread` : 'Notifications'"
      @click.stop="toggleDropdown"
    >
      <component
        :is="hasUnread ? BellAlertIcon : BellIcon"
        class="h-5 w-5"
      />
      <span
        v-if="hasUnread"
        class="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-blue-500 px-1 text-[10px] font-semibold leading-none text-white"
      >
        {{ badgeLabel }}
      </span>
    </button>

    <div
      v-show="isOpen"
      class="absolute right-0 top-full z-50 mt-1 w-96 max-w-[calc(100vw-2rem)] rounded-md border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800"
      @click.stop
    >
      <!-- Header -->
      <div class="flex items-center justify-between gap-2 border-b border-gray-200 px-3 py-2 dark:border-gray-700">
        <div class="flex items-center gap-1">
          <button
            type="button"
            class="cursor-pointer rounded px-2 py-1 text-xs font-medium"
            :class="filterTab === 'unread'
              ? 'bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-white'
              : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200'"
            @click="switchTab('unread')"
          >
            Unread
            <span
              v-if="hasUnread"
              class="ml-1 rounded-full bg-blue-500 px-1.5 text-[10px] font-semibold text-white"
            >
              {{ badgeLabel }}
            </span>
          </button>
          <button
            type="button"
            class="cursor-pointer rounded px-2 py-1 text-xs font-medium"
            :class="filterTab === 'all'
              ? 'bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-white'
              : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200'"
            @click="switchTab('all')"
          >
            All
          </button>
        </div>

        <div class="flex items-center gap-1">
          <button
            v-if="!selectMode && notifications.length > 0"
            type="button"
            class="cursor-pointer rounded px-2 py-1 text-xs font-medium text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
            @click="toggleSelectMode"
          >
            Select
          </button>
          <button
            v-if="!selectMode && filterTab === 'unread' && hasUnread"
            type="button"
            class="cursor-pointer rounded px-2 py-1 text-xs font-medium text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
            @click="markAllRead"
          >
            Mark all read
          </button>
        </div>
      </div>

      <!-- Bulk action bar -->
      <div
        v-if="selectMode"
        class="flex items-center justify-between gap-2 border-b border-gray-200 bg-gray-50 px-3 py-2 text-xs dark:border-gray-700 dark:bg-gray-900"
      >
        <button
          type="button"
          class="cursor-pointer font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
          @click="toggleSelectAll"
        >
          {{ allSelected ? 'Clear' : 'Select all' }} ({{ selectedIds.size }})
        </button>
        <div class="flex items-center gap-1">
          <button
            type="button"
            class="cursor-pointer rounded px-2 py-1 font-medium text-gray-600 hover:bg-gray-200 disabled:cursor-not-allowed disabled:opacity-50 dark:text-gray-300 dark:hover:bg-gray-700"
            :disabled="selectedIds.size === 0"
            @click="handleBulk('mark_read')"
          >
            Mark read
          </button>
          <button
            type="button"
            class="cursor-pointer rounded px-2 py-1 font-medium text-gray-600 hover:bg-gray-200 disabled:cursor-not-allowed disabled:opacity-50 dark:text-gray-300 dark:hover:bg-gray-700"
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
            class="cursor-pointer rounded p-1 text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700"
            aria-label="Cancel selection"
            @click="exitSelectMode"
          >
            <XMarkIcon class="h-4 w-4" />
          </button>
        </div>
      </div>

      <!-- List -->
      <div class="max-h-[32rem] overflow-y-auto">
        <div
          v-if="loading && notifications.length === 0"
          class="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400"
        >
          Loading&hellip;
        </div>
        <div
          v-else-if="notifications.length === 0"
          class="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400"
        >
          <CheckIcon class="mx-auto mb-2 h-6 w-6 text-gray-400 dark:text-gray-500" />
          <template v-if="filterTab === 'unread'">
            You're all caught up.
          </template>
          <template v-else>
            No notifications yet.
          </template>
        </div>
        <ul
          v-else
          class="divide-y divide-gray-100 dark:divide-gray-700"
        >
          <li
            v-for="n in notifications"
            :key="n.id"
            class="group cursor-pointer px-3 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/50"
            :class="!n.is_read ? 'bg-blue-50/40 dark:bg-blue-900/10' : ''"
            @click="handleRowClick(n)"
          >
            <div class="flex items-start gap-3">
              <input
                v-if="selectMode"
                type="checkbox"
                class="mt-1 cursor-pointer rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                :checked="selectedIds.has(n.id)"
                @click.stop="toggleSelect(n.id)"
              >
              <UserAvatar
                v-else
                :src="n.actor ? n.actor.avatar_url : ''"
                :name="n.actor ? userFullName(n.actor) : ''"
                size="md"
              />
              <div class="min-w-0 flex-1">
                <div class="flex items-start justify-between gap-2">
                  <p
                    class="text-sm"
                    :class="n.is_read
                      ? 'text-gray-700 dark:text-gray-300'
                      : 'font-semibold text-gray-900 dark:text-white'"
                  >
                    {{ n.title }}
                  </p>
                  <span
                    v-if="!n.is_read"
                    class="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-blue-500"
                    aria-hidden="true"
                  />
                </div>
                <p
                  v-if="n.body"
                  class="mt-0.5 line-clamp-2 text-xs text-gray-500 dark:text-gray-400"
                >
                  {{ n.body }}
                </p>
                <p class="mt-1 text-[11px] text-gray-400 dark:text-gray-500">
                  {{ relativeTime(n.created) }}
                </p>
              </div>
              <button
                v-if="!selectMode"
                type="button"
                class="cursor-pointer shrink-0 rounded p-1 text-gray-400 opacity-0 transition group-hover:opacity-100 hover:bg-gray-200 hover:text-gray-700 dark:hover:bg-gray-600 dark:hover:text-gray-200"
                aria-label="Delete notification"
                @click.stop="handleDelete(n.id)"
              >
                <TrashIcon class="h-4 w-4" />
              </button>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
