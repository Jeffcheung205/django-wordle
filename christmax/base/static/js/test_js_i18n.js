/* global gettext, interpolate */

document.addEventListener('DOMContentLoaded', () => {
  const banner = document.getElementById('welcome-banner');
  if (!banner || typeof gettext !== 'function') {
    return;
  }

  const template = gettext('Welcome to learn new things');
  banner.textContent = interpolate(template, {}, true);
});
