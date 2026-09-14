function setLikeState(btn, liked) {
  btn.classList.toggle('liked', liked);
  btn.setAttribute('aria-pressed', liked ? 'true' : 'false');
  btn.setAttribute('aria-label', liked ? 'Unlike this post' : 'Like this post');
}

document.addEventListener('click', async (event) => {
  const btn = event.target.closest('.like-btn');
  if (!btn) return;

  const postId = btn.dataset.postId;
  const originalLiked = btn.classList.contains('liked');
  const countEl = btn.querySelector('.like-count');
  const originalCount = parseInt(countEl.textContent, 10);

  setLikeState(btn, !originalLiked);
  countEl.textContent = originalLiked ? originalCount - 1 : originalCount + 1;

  try {
    const data = await apiPost(`/post/${postId}/like/`);
    countEl.textContent = data.like_count;
    setLikeState(btn, data.liked);
  } catch (err) {
    setLikeState(btn, originalLiked);
    countEl.textContent = originalCount;
    console.error(err);
  }
});
