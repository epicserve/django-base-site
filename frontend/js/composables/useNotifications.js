import { ref, computed } from 'vue';
import { get, post, patch, del } from '@/utils/api';
import { showToast } from './useToast';

const POLL_INTERVAL_MS = 20_000,
  unreadCount = ref(0),
  notifications = ref([]),
  loading = ref(false),
  currentFilter = ref('unread'), // 'unread' | 'all'
  dropdownOpen = ref(false),
  seenUnreadIds = new Set(),
  seeded = ref(false);

let pollHandle = null,
  visibilityHandler = null;

function toastForNew(results) {
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
    const data = await get('/api/notifications/', { is_read: 'false', page_size: 20 });
    unreadCount.value = data.count;
    if (currentFilter.value === 'unread') {
      notifications.value = data.results;
    } else if (dropdownOpen.value) {
      // Keep the "All" list fresh while the user is looking at it
      const all = await get('/api/notifications/', { page_size: 30 });
      notifications.value = all.results;
    }
    toastForNew(data.results);
  } catch {
    // swallow — polling recovers on next tick
  }
}

async function fetchList({ filter = currentFilter.value } = {}) {
  currentFilter.value = filter;
  loading.value = true;
  try {
    const params = { page_size: 30 };
    if (filter === 'unread') params.is_read = 'false';
    // eslint-disable-next-line one-var
    const data = await get('/api/notifications/', params);
    notifications.value = data.results;
    if (filter === 'unread') {
      unreadCount.value = data.count;
      toastForNew(data.results);
    }
  } finally {
    loading.value = false;
  }
}

async function markRead(id) {
  await patch(`/api/notifications/${id}/`, { is_read: true });
  applyLocalRead(id, true);
}

async function markUnread(id) {
  await patch(`/api/notifications/${id}/`, { is_read: false });
  applyLocalRead(id, false);
}

async function deleteOne(id) {
  await del(`/api/notifications/${id}/`);
  notifications.value = notifications.value.filter((n) => n.id !== id);
  seenUnreadIds.delete(id);
  await refreshUnread();
}

async function bulkAction(action, ids) {
  if (!ids.length) return;
  await post('/api/notifications/bulk/', { action, ids });
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
  await post('/api/notifications/bulk/', { action: 'mark_read', all_unread: true });
  notifications.value.forEach((n) => {
    n.is_read = true;
  });
  unreadCount.value = 0;
  if (currentFilter.value === 'unread') {
    notifications.value = [];
  }
}

function applyLocalRead(id, isRead) {
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

function setDropdownOpen(open) {
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
