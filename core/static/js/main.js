// Theme toggle — persists to localStorage
(function () {
  const html = document.documentElement;
  const toggle = document.getElementById('themeToggle');
  const stored = localStorage.getItem('theme') || 'dark';

  html.setAttribute('data-theme', stored);
  if (toggle) toggle.checked = (stored === 'light');

  if (toggle) {
    toggle.addEventListener('change', () => {
      const next = toggle.checked ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    });
  }
})();