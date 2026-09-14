document.addEventListener('click', async (event) => {
  const btn = event.target.closest('.save-btn');
  if (!btn) return;

  const postId = btn.dataset.postId;
  const wasSaved = btn.classList.contains('saved');

  btn.classList.toggle('saved', !wasSaved);
  btn.setAttribute('aria-pressed', (!wasSaved).toString());

  try {
    const data = await apiPost(`/post/${postId}/save/`);
    btn.classList.toggle('saved', data.saved);
    btn.setAttribute('aria-pressed', data.saved.toString());
    btn.setAttribute('aria-label', data.saved ? 'Remove from saved' : 'Save this post');
  } catch (err) {
    btn.classList.toggle('saved', wasSaved);
    btn.setAttribute('aria-pressed', wasSaved.toString());
    console.error(err);
  }
});
