import { ref, computed } from 'vue';
import type { components } from '@/api/schema';
import { api, unwrap } from '@/utils/api';
import { showToast } from './useToast';

export type Notification = components['schemas']['NotificationOut'];
export type NotificationFilter = 'unread' | 'all';
export type BulkAction = components['schemas']['BulkActionIn']['action'];

const POLL_INTERVAL_MS = 20_000,
  unreadCount = ref(0),
  notifications = ref<Notification[]>([]),
  loading = ref(false),
  currentFilter = ref<NotificationFilter>('unread'),
  dropdownOpen = ref(false),
  seenUnreadIds = new Set<number>(),
  seeded = ref(false);

let pollHandle: ReturnType<typeof setInterval> | null = null,
  visibilityHandler: (() => void) | null = null;

function listNotifications(query: { is_read?: string; page_size: number }) {
  return unwrap(api.GET('/api/notifications/', { params: { query } }));
}

function toastForNew(results: Notification[]) {
  if (!seeded.value) {
    results.forEach((n) => seenUnreadIds.add(n.id));
    seeded.value = true;
    return;
  }
  results.forEach((n) => {
    if (!seenUnreadIds.has(n.id)) {
      seenUnreadIds.add(n.id);
      showToast(n.title, 'success', 5000);
    }
  });
}

async function refreshUnread() {
  try {
    const data = await listNotifications({ is_read: 'false', page_size: 20 });
    unreadCount.value = data.count;
    if (currentFilter.value === 'unread') {
      notifications.value = data.results;
    } else if (dropdownOpen.value) {
      // Keep the "All" list fresh while the user is looking at it
      const all = await listNotifications({ page_size: 30 });
      notifications.value = all.results;
    }
    toastForNew(data.results);
  } catch {
    // swallow — polling recovers on next tick
  }
}

async function fetchList({ filter = currentFilter.value }: { filter?: NotificationFilter } = {}) {
  currentFilter.value = filter;
  loading.value = true;
  try {
    const data = await listNotifications(filter === 'unread' ? { is_read: 'false', page_size: 30 } : { page_size: 30 });
    notifications.value = data.results;
    if (filter === 'unread') {
      unreadCount.value = data.count;
      toastForNew(data.results);
    }
  } finally {
    loading.value = false;
  }
}

async function markRead(id: number) {
  await unwrap(
    api.PATCH('/api/notifications/{notification_id}/', {
      params: { path: { notification_id: id } },
      body: { is_read: true },
    }),
  );
  applyLocalRead(id, true);
}

async function markUnread(id: number) {
  await unwrap(
    api.PATCH('/api/notifications/{notification_id}/', {
      params: { path: { notification_id: id } },
      body: { is_read: false },
    }),
  );
  applyLocalRead(id, false);
}

async function deleteOne(id: number) {
  await unwrap(api.DELETE('/api/notifications/{notification_id}/', { params: { path: { notification_id: id } } }));
  notifications.value = notifications.value.filter((n) => n.id !== id);
  seenUnreadIds.delete(id);
  await refreshUnread();
}

async function bulkAction(action: BulkAction, ids: number[]) {
  if (!ids.length) return;
  await unwrap(api.POST('/api/notifications/bulk/', { body: { action, ids } }));
  if (action === 'delete') {
    notifications.value = notifications.value.filter((n) => !ids.includes(n.id));
    ids.forEach((id) => seenUnreadIds.delete(id));
  } else {
    const isRead = action === 'mark_read';
    ids.forEach((id) => applyLocalRead(id, isRead));
  }
  await refreshUnread();
  if (currentFilter.value === 'unread' && action !== 'mark_unread') {
    await fetchList({ filter: 'unread' });
  }
}

async function markAllRead() {
  await unwrap(api.POST('/api/notifications/bulk/', { body: { action: 'mark_read', all_unread: true } }));
  notifications.value.forEach((n) => {
    n.is_read = true;
  });
  unreadCount.value = 0;
  if (currentFilter.value === 'unread') {
    notifications.value = [];
  }
}

function applyLocalRead(id: number, isRead: boolean) {
  const n = notifications.value.find((item) => item.id === id);
  if (n) n.is_read = isRead;
  if (isRead) unreadCount.value = Math.max(0, unreadCount.value - 1);
  else unreadCount.value += 1;
}

function startPolling() {
  if (pollHandle) return;
  refreshUnread();
  pollHandle = setInterval(() => {
    if (!document.hidden) refreshUnread();
  }, POLL_INTERVAL_MS);

  visibilityHandler = () => {
    if (!document.hidden) refreshUnread();
  };
  document.addEventListener('visibilitychange', visibilityHandler);
}

function stopPolling() {
  if (pollHandle) {
    clearInterval(pollHandle);
    pollHandle = null;
  }
  if (visibilityHandler) {
    document.removeEventListener('visibilitychange', visibilityHandler);
    visibilityHandler = null;
  }
  unreadCount.value = 0;
  notifications.value = [];
  seenUnreadIds.clear();
  seeded.value = false;
}

function setDropdownOpen(open: boolean) {
  dropdownOpen.value = open;
}

export function useNotifications() {
  return {
    unreadCount: computed(() => unreadCount.value),
    notifications,
    loading: computed(() => loading.value),
    currentFilter: computed(() => currentFilter.value),
    startPolling,
    stopPolling,
    fetchList,
    markRead,
    markUnread,
    deleteOne,
    bulkAction,
    markAllRead,
    setDropdownOpen,
  };
}
