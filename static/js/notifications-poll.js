(function () {
  const notifBadges = document.querySelectorAll('[data-notif-badge]');
  const msgBadges = document.querySelectorAll('[data-msg-badge]');
  if (!notifBadges.length && !msgBadges.length) return;

  function updateBadge(elements, count) {
    elements.forEach((el) => {
      el.textContent = count;
      el.hidden = count === 0;
    });
  }

  async function poll() {
    try {
      if (notifBadges.length) {
        const data = await apiGet('/social/notifications/unread-count/');
        updateBadge(notifBadges, data.count);
      }
      if (msgBadges.length) {
        const data = await apiGet('/messages/unread-count/');
        updateBadge(msgBadges, data.count);
      }
    } catch (err) {
      // Silently ignore transient polling failures.
    }
  }

  poll();
  setInterval(poll, 20000);
})();
