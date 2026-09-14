document.addEventListener('submit', async (event) => {
  const form = event.target.closest('.comment-form');
  if (!form) return;
  event.preventDefault();

  const postId = form.dataset.postId;
  const input = form.querySelector('input[name="content"]');
  const content = input.value.trim();
  if (!content) return;

  const list = document.querySelector(`.comment-list[data-post-id="${postId}"]`);

  try {
    const data = await apiPost(`/post/${postId}/comment/`, { content });

    const item = document.createElement('div');
    item.className = 'comment';
    item.dataset.commentId = data.id;
    item.innerHTML = `
      <span class="name">${escapeHtml(data.author)}</span>
      <span class="comment-time">${escapeHtml(data.created_at)}</span>
      <div class="comment-actions">
        <button type="button" class="comment-edit-btn" data-comment-id="${data.id}">Edit</button>
        <button type="button" class="comment-delete" data-comment-id="${data.id}" data-post-id="${postId}">Delete</button>
      </div>
      <p class="comment-content">${escapeHtml(data.content)}</p>
    `;
    if (list) list.appendChild(item);

    const countEl = document.querySelector(`[data-comment-count="${postId}"]`);
    if (countEl) countEl.textContent = data.comment_count;

    input.value = '';
  } catch (err) {
    console.error(err);
  }
});

document.addEventListener('click', async (event) => {
  const deleteBtn = event.target.closest('.comment-delete');
  if (deleteBtn) {
    try {
      await apiPost(`/comment/${deleteBtn.dataset.commentId}/delete/`);
      const commentEl = deleteBtn.closest('.comment');
      commentEl.remove();
      const countEl = document.querySelector(`[data-comment-count="${deleteBtn.dataset.postId}"]`);
      if (countEl) countEl.textContent = parseInt(countEl.textContent, 10) - 1;
    } catch (err) {
      console.error(err);
    }
    return;
  }

  const editBtn = event.target.closest('.comment-edit-btn');
  if (editBtn) {
    const commentEl = editBtn.closest('.comment');
    const contentEl = commentEl.querySelector('.comment-content');
    const currentText = contentEl.textContent;

    const editForm = document.createElement('form');
    editForm.className = 'comment-edit-form';
    editForm.dataset.originalText = currentText;

    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'content';
    input.value = currentText;
    input.maxLength = 500;
    input.required = true;

    const saveBtn = document.createElement('button');
    saveBtn.type = 'submit';
    saveBtn.className = 'btn btn-sm btn-primary';
    saveBtn.textContent = 'Save';

    const cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.className = 'btn btn-sm comment-cancel-edit';
    cancelBtn.textContent = 'Cancel';

    editForm.append(input, saveBtn, cancelBtn);
    contentEl.replaceWith(editForm);
    input.focus();
    return;
  }

  const cancelBtn = event.target.closest('.comment-cancel-edit');
  if (cancelBtn) {
    const editForm = cancelBtn.closest('.comment-edit-form');
    const p = document.createElement('p');
    p.className = 'comment-content';
    p.textContent = editForm.dataset.originalText;
    editForm.replaceWith(p);
  }
});

document.addEventListener('submit', async (event) => {
  const editForm = event.target.closest('.comment-edit-form');
  if (!editForm) return;
  event.preventDefault();

  const commentEl = editForm.closest('.comment');
  const commentId = commentEl.dataset.commentId;
  const input = editForm.querySelector('input[name="content"]');
  const content = input.value.trim();
  if (!content) return;

  try {
    const data = await apiPost(`/comment/${commentId}/edit/`, { content });
    const p = document.createElement('p');
    p.className = 'comment-content';
    p.textContent = data.content;
    editForm.replaceWith(p);
  } catch (err) {
    console.error(err);
  }
});
