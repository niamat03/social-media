document.addEventListener('click', (event) => {
  const toggle = event.target.closest('.post-menu-toggle');

  document.querySelectorAll('.post-menu-dropdown').forEach((dropdown) => {
    if (!toggle || dropdown !== toggle.nextElementSibling) {
      dropdown.hidden = true;
      const btn = dropdown.previousElementSibling;
      if (btn) btn.setAttribute('aria-expanded', 'false');
    }
  });

  if (toggle) {
    const dropdown = toggle.nextElementSibling;
    const isHidden = dropdown.hidden;
    dropdown.hidden = !isHidden;
    toggle.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
  }
});

document.addEventListener('click', (event) => {
  const openBtn = event.target.closest('.report-open-btn');
  if (!openBtn) return;

  document.querySelectorAll('.post-menu-dropdown').forEach((d) => { d.hidden = true; });

  const article = openBtn.closest('.post-card');
  const form = article.querySelector('.report-form');
  if (form) form.hidden = false;
});

document.addEventListener('click', (event) => {
  const cancelBtn = event.target.closest('.report-cancel-btn');
  if (!cancelBtn) return;
  cancelBtn.closest('.report-form').hidden = true;
});

document.addEventListener('submit', async (event) => {
  const form = event.target.closest('.report-form');
  if (!form) return;
  event.preventDefault();

  const postId = form.dataset.postId;
  const reason = form.querySelector('select[name="reason"]').value;
  const details = form.querySelector('textarea[name="details"]').value;

  try {
    await apiPost(`/post/${postId}/report/`, { reason, details });
    form.innerHTML = '<p style="margin:0; color:var(--text-muted); font-size:0.85rem;">Thanks, we received your report.</p>';
    setTimeout(() => { form.hidden = true; }, 2500);
  } catch (err) {
    console.error(err);
  }
});
