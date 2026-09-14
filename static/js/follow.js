document.addEventListener('click', async (event) => {
  const btn = event.target.closest('.follow-btn');
  if (!btn) return;

  const username = btn.dataset.username;
  const isIconOnly = btn.dataset.iconOnly === 'true';

  try {
    const data = await apiPost(`/social/users/${username}/follow/`);
    btn.classList.toggle('following', data.following);

    if (isIconOnly) {
      const use = btn.querySelector('use');
      if (use) use.setAttribute('href', data.following ? '#icon-check' : '#icon-plus');
      const label = data.following ? 'Unfollow' : 'Follow';
      btn.title = label;
      btn.setAttribute('aria-label', `${label} ${username}`);
    } else {
      btn.textContent = data.following ? 'Following' : 'Follow';
      btn.classList.toggle('btn-primary', !data.following);
    }

    const countEl = document.querySelector('[data-followers-count]');
    if (countEl) countEl.textContent = data.followers_count;
  } catch (err) {
    console.error(err);
  }
});
