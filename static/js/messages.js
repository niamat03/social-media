document.addEventListener('submit', async (event) => {
  const form = event.target.closest('.message-form');
  if (!form) return;
  event.preventDefault();

  const username = form.dataset.username;
  const input = form.querySelector('input[name="content"]');
  const content = input.value.trim();
  if (!content) return;

  const list = document.querySelector('.message-list');

  try {
    const data = await apiPost(`/messages/${username}/send/`, { content });

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble message-bubble-mine';
    bubble.innerHTML = `<p>${escapeHtml(data.content)}</p><span class="message-time">${escapeHtml(data.created_at)}</span>`;
    if (list) {
      list.appendChild(bubble);
      list.scrollTop = list.scrollHeight;
    }

    input.value = '';
    input.focus();
  } catch (err) {
    console.error(err);
  }
});

document.addEventListener('click', async (event) => {
  const acceptBtn = event.target.closest('.request-accept-btn');
  const declineBtn = event.target.closest('.request-decline-btn');
  const btn = acceptBtn || declineBtn;
  if (!btn) return;

  const username = btn.dataset.username;
  const action = acceptBtn ? 'accept' : 'decline';

  try {
    await apiPost(`/messages/${username}/${action}/`);
    if (action === 'decline') {
      window.location.href = '/messages/';
    } else {
      const banner = btn.closest('.report-form');
      if (banner) banner.remove();
    }
  } catch (err) {
    console.error(err);
  }
});

document.addEventListener('DOMContentLoaded', () => {
  const list = document.querySelector('.message-list');
  if (!list) return;
  list.scrollTop = list.scrollHeight;

  const username = list.dataset.username;
  let lastId = parseInt(list.dataset.lastId || '0', 10);

  async function poll() {
    try {
      const data = await apiGet(`/messages/${username}/poll/?after=${lastId}`);
      data.messages.forEach((message) => {
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble message-bubble-theirs';
        bubble.innerHTML = `<p>${escapeHtml(message.content)}</p><span class="message-time">${escapeHtml(message.created_at)}</span>`;
        list.appendChild(bubble);
        lastId = Math.max(lastId, message.id);
      });
      if (data.messages.length) {
        list.scrollTop = list.scrollHeight;
      }
    } catch (err) {
      // Ignore transient polling failures.
    }
  }

  setInterval(poll, 4000);
});
