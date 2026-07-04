document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initMegaMenu();
  initSearch();
  initMobileMenu();
});

function initTheme() {
  const saved = localStorage.getItem('terpvault-theme');
  const system = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  const theme = saved || 'system';

  function apply(t) {
    const resolved = t === 'system' ? system : t;
    document.documentElement.setAttribute('data-theme', resolved);
    const btns = document.querySelectorAll('[data-theme-btn]');
    btns.forEach(b => b.classList.toggle('active', b.dataset.themeValue === t));
  }

  apply(theme);

  document.querySelectorAll('[data-theme-btn]').forEach(btn => {
    btn.addEventListener('click', () => {
      const t = btn.dataset.themeValue;
      localStorage.setItem('terpvault-theme', t);
      apply(t);
    });
  });

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const current = localStorage.getItem('terpvault-theme') || 'system';
    if (current === 'system') {
      apply('system');
    }
  });
}

function initMegaMenu() {
  const triggers = document.querySelectorAll('[data-mega-trigger]');
  const panels = document.querySelectorAll('[data-mega-panel]');

  triggers.forEach(trigger => {
    trigger.addEventListener('mouseenter', () => {
      const id = trigger.dataset.megaTrigger;
      panels.forEach(p => p.classList.remove('open'));
      const panel = document.querySelector(`[data-mega-panel="${id}"]`);
      if (panel) panel.classList.add('open');
    });
    trigger.addEventListener('focusin', () => {
      const id = trigger.dataset.megaTrigger;
      panels.forEach(p => p.classList.remove('open'));
      const panel = document.querySelector(`[data-mega-panel="${id}"]`);
      if (panel) panel.classList.add('open');
    });
  });

  const nav = document.querySelector('.nav');
  if (nav) {
    nav.addEventListener('mouseleave', () => {
      panels.forEach(p => p.classList.remove('open'));
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      panels.forEach(p => p.classList.remove('open'));
    }
  });
}

function initSearch() {
  const searchInput = document.getElementById('search-input');
  const searchResults = document.getElementById('search-results');
  if (!searchInput) return;

  let searchIndex = null;
  let searchTimeout = null;

  const searchUrl = searchInput.getAttribute('data-search-url') || `/catalogs/${window.location.pathname.split('/')[2]}/search-data`;
  fetch(searchUrl)
    .then(r => r.json())
    .then(data => { searchIndex = data; })
    .catch(() => {});

  searchInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => performSearch(searchInput, searchResults, searchIndex), 150);
  });

  searchInput.addEventListener('focus', () => {
    if (searchInput.value.trim().length > 0 && searchResults) {
      searchResults.classList.add('open');
    }
  });

  document.addEventListener('click', (e) => {
    if (searchResults && !e.target.closest('.search-wrap')) {
      searchResults.classList.remove('open');
    }
  });

  searchInput.addEventListener('keydown', (e) => {
    const items = searchResults ? searchResults.querySelectorAll('.search-result-item') : [];
    if (!items.length) return;
    let idx = Array.from(items).findIndex(el => el === document.activeElement);
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      idx = Math.min(idx + 1, items.length - 1);
      items[idx].focus();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      idx = Math.max(idx - 1, 0);
      items[idx].focus();
    } else if (e.key === 'Escape') {
      searchResults.classList.remove('open');
      searchInput.blur();
    }
  });
}

function performSearch(input, resultsEl, index) {
  const q = input.value.trim().toLowerCase();
  if (!resultsEl) return;

  if (q.length < 1 || !index) {
    resultsEl.classList.remove('open');
    return;
  }

  const results = [];
  for (const entry of index.entries) {
    if (entry.searchable.toLowerCase().includes(q)) {
      results.push(entry);
    }
    if (results.length >= 20) break;
  }

  if (results.length === 0) {
    resultsEl.innerHTML = `<div class="search-empty">No results for "${input.value}"</div>`;
    resultsEl.classList.add('open');
    return;
  }

  let html = '<div class="search-results-list">';
  for (const r of results) {
    const name = highlightMatch(r.name, q);
    const brand = r.brand ? highlightMatch(r.brand, q) : '';
    const price = r.price ? `&pound;${r.price.toFixed(2)}` : '';
    html += `<a href="/terpenes-uk/product/${r.id}" class="search-result-item" tabindex="-1">
      <div class="sri-name">${name}</div>
      <div class="sri-meta">${brand ? `<span>${brand}</span>` : ''}${price ? `<span class="sri-price">${price}</span>` : ''}</div>
    </a>`;
  }
  html += '</div>';
  resultsEl.innerHTML = html;
  resultsEl.classList.add('open');
}

function highlightMatch(text, query) {
  if (!text) return '';
  const idx = text.toLowerCase().indexOf(query);
  if (idx === -1) return escapeHtml(text);
  return escapeHtml(text.slice(0, idx)) + '<mark>' + escapeHtml(text.slice(idx, idx + query.length)) + '</mark>' + escapeHtml(text.slice(idx + query.length));
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function initMobileMenu() {
  const toggle = document.getElementById('mobile-menu-toggle');
  const nav = document.querySelector('.nav-links');
  if (!toggle || !nav) return;

  toggle.addEventListener('click', () => {
    const expanded = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', String(!expanded));
    nav.classList.toggle('open');
    document.body.classList.toggle('nav-open');
  });
}
