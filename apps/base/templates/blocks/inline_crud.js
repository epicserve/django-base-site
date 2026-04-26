// Shared inline CRUD utilities
function getCsrf() {
  const m = document.cookie.match(/csrftoken=([^;]+)/);
  return m ? m[1] : '';
}

async function apiRequest(url, method, body) {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw await res.json().catch(() => ({}));
  return res.status === 204 ? null : res.json();
}

function resetDeleteBtn(row) {
  const confirmBtn = row.querySelector('.btn-confirm-delete');
  const xBtn = row.querySelector('.btn-x-delete');
  if (!confirmBtn) return;
  confirmBtn.style.maxWidth = '0';
  confirmBtn.style.opacity = '0';
  confirmBtn.style.paddingLeft = '0';
  confirmBtn.style.paddingRight = '0';
  confirmBtn.style.marginLeft = '0';
  xBtn.style.opacity = '1';
  setTimeout(() => confirmBtn.remove(), 250);
}

function wireDeleteBtn(xBtn, onConfirm) {
  xBtn.addEventListener('click', function () {
    const row = xBtn.closest('tr') || xBtn.closest('li');
    if (row.querySelector('.btn-confirm-delete')) { resetDeleteBtn(row); return; }

    const confirmBtn = document.createElement('button');
    confirmBtn.className = 'btn btn-sm btn-danger btn-confirm-delete ms-2';
    confirmBtn.textContent = 'Delete';
    confirmBtn.style.cssText = 'max-width:0;opacity:0;padding-left:0;padding-right:0;overflow:hidden;transition:max-width 0.2s ease,opacity 0.2s ease,padding 0.2s ease;white-space:nowrap';
    xBtn.insertAdjacentElement('afterend', confirmBtn);

    requestAnimationFrame(() => requestAnimationFrame(() => {
      confirmBtn.style.maxWidth = '80px';
      confirmBtn.style.opacity = '1';
      confirmBtn.style.paddingLeft = '';
      confirmBtn.style.paddingRight = '';
      xBtn.style.transition = 'opacity 0.15s';
      xBtn.style.opacity = '0';
    }));

    function onOutside(ev) {
      if (!row.contains(ev.target)) {
        resetDeleteBtn(row);
        document.removeEventListener('click', onOutside);
      }
    }
    setTimeout(() => document.addEventListener('click', onOutside), 0);

    confirmBtn.addEventListener('click', async function (ev) {
      ev.stopPropagation();
      document.removeEventListener('click', onOutside);
      try {
        await onConfirm();
        row.style.transition = 'opacity 0.15s';
        row.style.opacity = '0';
        setTimeout(() => row.remove(), 150);
      } catch {
        resetDeleteBtn(row);
      }
    });
  });
}
