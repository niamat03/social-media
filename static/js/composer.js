document.addEventListener('click', (event) => {
  const btn = event.target.closest('.add-location-btn');
  if (!btn) return;

  const form = btn.closest('form');
  const status = form.querySelector('.location-status');
  const latInput = form.querySelector('input[name="latitude"]');
  const lngInput = form.querySelector('input[name="longitude"]');
  const nameInput = form.querySelector('input[name="location_name"]');
  const nameField = form.querySelector('[data-location-name-field]');
  if (nameField) nameField.hidden = false;

  if (!navigator.geolocation) {
    status.textContent = 'Geolocation is not available on this device.';
    return;
  }

  status.textContent = 'Requesting location...';

  navigator.geolocation.getCurrentPosition(
    (position) => {
      latInput.value = position.coords.latitude;
      lngInput.value = position.coords.longitude;
      status.textContent = 'Location attached to this post.';
      if (nameInput && !nameInput.value) {
        nameInput.focus();
      }
    },
    () => {
      status.textContent = 'Location permission denied. Post will be saved without a location.';
    },
    { timeout: 8000 }
  );
});
