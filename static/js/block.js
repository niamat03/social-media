document.addEventListener('click', async (event) => {
  const btn = event.target.closest('.block-toggle-btn');
  if (!btn) return;

  const username = btn.dataset.username;
  if (!confirm(`Block @${username}? They won't be able to follow or message you, and you won't see each other's posts.`)) {
    return;
  }

  try {
    const data = await apiPost(`/social/users/${username}/block/`);

    document.querySelectorAll(`.block-toggle-btn[data-username="${username}"]`).forEach((b) => {
      const label = b.querySelector('.block-toggle-label');
      if (label) {
        label.textContent = label.textContent.includes('@')
          ? `${data.blocked ? 'Unblock' : 'Block'} @${username}`
          : (data.blocked ? 'Unblock' : 'Block');
      } else {
        b.textContent = data.blocked ? 'Unblock' : 'Block';
      }
    });

    if (data.blocked) {
      document.querySelectorAll(`.post-card[data-author-username="${username}"]`).forEach((card) => card.remove());
    }

    document.querySelectorAll('.post-menu-dropdown').forEach((d) => { d.hidden = true; });
  } catch (err) {
    console.error(err);
  }
});
