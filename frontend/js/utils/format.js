/**
 * Formatting utility functions.
 */

export function userFullName(user) {
  if (!user) return '';
  const name = `${user.first_name || ''} ${user.last_name || ''}`.trim();

  return name || user.username || '';
}

export function humanDateTime(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);

  return d.toLocaleString('en-US', {
    month: '2-digit',
    day: '2-digit',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export function relativeTime(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString),
    diffMs = Date.now() - d.getTime(),
    sec = Math.round(diffMs / 1000),
    min = Math.round(sec / 60),
    hr = Math.round(min / 60),
    day = Math.round(hr / 24),
    now = new Date(),
    sameYear = d.getFullYear() === now.getFullYear();
  if (sec < 45) return 'just now';
  if (min < 60) return `${min}m ago`;
  if (hr < 24) return `${hr}h ago`;
  if (day < 7) return `${day}d ago`;
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    ...(sameYear ? {} : { year: 'numeric' }),
  });
}

export function fullDateTime(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  return d.toLocaleString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export function friendlyDate(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);

  return d.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
  });
}

export function humanDate(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);

  return d.toLocaleDateString('en-US', {
    month: '2-digit',
    day: '2-digit',
    year: 'numeric',
  });
}

export function humanTime(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);

  return d.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export function humanDuration(seconds) {
  if (!seconds && seconds !== 0) return '';
  const h = Math.floor(seconds / 3600),
    m = Math.floor((seconds % 3600) / 60);

  if (h === 0) return `${m} min`;
  if (m === 0) return `${h} h`;
  return `${h} h ${m} min`;
}

export function groupBy(array, keyFn) {
  return array.reduce((acc, item) => {
    const key = keyFn(item);

    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {});
}

export function toApiDateTime(date) {
  const yyyy = date.getFullYear(),
    mm = String(date.getMonth() + 1).padStart(2, '0'),
    dd = String(date.getDate()).padStart(2, '0'),
    hh = String(date.getHours()).padStart(2, '0'),
    min = String(date.getMinutes()).padStart(2, '0'),
    ss = String(date.getSeconds()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}T${hh}:${min}:${ss}`;
}

export function escapeHtml(text) {
  const div = document.createElement('div');

  div.textContent = text;
  return div.innerHTML;
}
