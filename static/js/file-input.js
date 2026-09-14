document.addEventListener('change', (event) => {
  const input = event.target.closest('.file-input-wrapper input[type="file"]');
  if (!input) return;

  const wrapper = input.closest('.composer-actions') || input.parentElement.parentElement;
  const nameEl = wrapper ? wrapper.querySelector('[data-file-name]') : null;
  if (nameEl) {
    nameEl.textContent = input.files.length ? input.files[0].name : '';
  }
});
