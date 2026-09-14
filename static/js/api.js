function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

// Escapes user-controlled text before it is interpolated into innerHTML,
// since content/display names come back from the API unescaped.
function escapeHtml(value) {
  const div = document.createElement('div');
  div.textContent = value == null ? '' : String(value);
  return div.innerHTML;
}

async function apiPost(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCsrfToken(),
      ...(body instanceof FormData ? {} : { 'Content-Type': 'application/x-www-form-urlencoded' }),
    },
    body: body instanceof FormData ? body : new URLSearchParams(body || {}),
  });

  if (!response.ok) {
    let detail = '';
    try {
      detail = JSON.stringify(await response.json());
    } catch (err) {
      detail = response.statusText;
    }
    throw new Error(`Request failed (${response.status}): ${detail}`);
  }

  return response.json();
}

async function apiGet(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }
  return response.json();
}
