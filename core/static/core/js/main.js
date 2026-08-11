// Theme toggle — persists to localStorage
(function () {
  const html = document.documentElement;
  const toggle = document.getElementById('themeToggle');
  const stored = localStorage.getItem('theme') || 'dark';

  html.setAttribute('data-theme', stored);
  if (toggle) toggle.checked = (stored === 'dark');

  if (toggle) {
    toggle.addEventListener('change', () => {
      const next = toggle.checked ? 'dark' : 'light';
      html.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    });
  }
})();

// Mobile nav — hamburger opens/closes the dropdown of links
(function () {
  const btn = document.getElementById('navToggle');
  const links = document.getElementById('navLinks');
  if (!btn || !links) return;

  const close = () => {
    links.classList.remove('open');
    btn.setAttribute('aria-expanded', 'false');
  };

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const open = links.classList.toggle('open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  });

  // Tapping a link, clicking outside, or pressing Escape closes the menu.
  links.querySelectorAll('a').forEach((a) => a.addEventListener('click', close));
  document.addEventListener('click', (e) => {
    if (!links.contains(e.target) && !btn.contains(e.target)) close();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close();
  });
})();