/**
 * API utility module using fetch() with CSRF token handling for Django.
 */

function getCookie(name) {
  let cookieValue = null;

  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');

    for (let i = 0; i < cookies.length; i += 1) {
      const cookie = cookies[i].trim();

      if (cookie.substring(0, name.length + 1) === `${name}=`) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }

  return cookieValue;
}

function getCSRFToken() {
  return getCookie('csrftoken');
}

export async function request(url, options = {}) {
  const defaults = {
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken(),
      },
    },
    config = { ...defaults, ...options, headers: { ...defaults.headers, ...(options.headers || {}) } },
    response = await fetch(url, config);

  if (!response.ok) {
    const error = new Error(`HTTP ${response.status}`);

    error.response = response;
    try {
      error.data = await response.json();
    } catch {
      error.data = null;
    }
    throw error;
  }

  if (response.status === 204) return null;
  return response.json();
}

export function get(url, params = {}) {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((v) => searchParams.append(key, v));
    } else if (value !== null && value !== undefined && value !== '') {
      searchParams.append(key, value);
    }
  });
  // eslint-disable-next-line one-var
  const qs = searchParams.toString(),
    fullUrl = qs ? `${url}?${qs}` : url;

  return request(fullUrl, { method: 'GET' });
}

export function post(url, data) {
  return request(url, { method: 'POST', body: JSON.stringify(data) });
}

export function patch(url, data) {
  return request(url, { method: 'PATCH', body: JSON.stringify(data) });
}

export function put(url, data) {
  return request(url, { method: 'PUT', body: JSON.stringify(data) });
}

export function del(url) {
  return request(url, { method: 'DELETE' });
}

export function postFormData(url, formData) {
  return fetch(url, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCSRFToken() },
    body: formData,
  }).then(async (response) => {
    if (!response.ok) {
      const error = new Error(`HTTP ${response.status}`);

      error.response = response;
      try {
        error.data = await response.json();
      } catch {
        error.data = null;
      }
      throw error;
    }
    if (response.status === 204) return null;
    return response.json();
  });
}

export function deleteRequest(url) {
  return request(url, { method: 'DELETE' });
}

export function parseErrors(error) {
  if (error.data && typeof error.data === 'object') {
    const errors = {};

    Object.entries(error.data).forEach(([key, value]) => {
      errors[key] = Array.isArray(value) ? value : [value];
    });
    return errors;
  }
  return { non_field_errors: ['An unexpected error occurred.'] };
}

export async function getAllResults(url, params = {}, results = []) {
  const data = await get(url, params);

  results.push(...data.results);
  if (data.next) {
    const nextUrl = new URL(data.next),
      nextParams = { ...params, page: nextUrl.searchParams.get('page') };

    return getAllResults(url, nextParams, results);
  }
  return results;
}
