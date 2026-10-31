import { getCSRFToken } from '@/utils/api';

// django-hijack's acquire and release views expect a regular form POST and answer with a redirect,
// so build and submit a form instead of calling them with fetch().
function submitHijackForm(action, fields) {
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = action;
  const values = { csrfmiddlewaretoken: getCSRFToken() || '', next: '/', ...fields };
  Object.entries(values).forEach(([name, value]) => {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = String(value);
    form.appendChild(input);
  });
  document.body.appendChild(form);
  form.submit();
}

export function startImpersonating(userId) {
  submitHijackForm('/hijack/acquire/', { user_pk: userId });
}

export function stopImpersonating() {
  submitHijackForm('/hijack/release/');
}
