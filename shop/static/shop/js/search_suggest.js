(() => {
  const input = document.getElementById('searchInput');
  const dropdown = document.getElementById('searchDropdown');
  if (!input || !dropdown) return;

  let timer = null;
  let lastQ = '';

  const esc = (s) => (s || '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));

  const close = () => {
    dropdown.classList.add('hidden');
    dropdown.innerHTML = '';
  };

  const open = () => {
    dropdown.classList.remove('hidden');
  };

  const render = (items) => {
    if (!items || !items.length) {
      close();
      return;
    }
    const rows = items.map((it) => {
      const img = it.image ? `<img src="${esc(it.image)}" class="w-10 h-10 rounded-lg object-cover bg-slate-100" alt="">` :
        `<div class="w-10 h-10 rounded-lg bg-slate-100"></div>`;
      return `
        <a href="${esc(it.url)}" class="flex items-center gap-3 p-3 hover:bg-slate-50">
          ${img}
          <div class="min-w-0">
            <div class="text-sm font-medium text-slate-900 truncate">${esc(it.name)}</div>
            <div class="text-xs text-slate-500 truncate">${esc(it.brand || '')}${it.brand && it.category ? ' • ' : ''}${esc(it.category || '')}${it.sku ? ' • ' + esc(it.sku) : ''}</div>
          </div>
          <div class="ml-auto text-sm font-semibold text-blue-700 whitespace-nowrap">${esc(it.price)} ₽</div>
        </a>
      `;
    }).join('');

    dropdown.innerHTML = `
      <div class="max-h-96 overflow-auto">
        ${rows}
      </div>
      <div class="border-t p-3 text-sm">
        <button type="button" class="text-blue-700 hover:underline" id="searchSeeAll">Показать все результаты →</button>
      </div>
    `;

    const seeAll = document.getElementById('searchSeeAll');
    if (seeAll) {
      seeAll.addEventListener('click', () => {
        const q = (input.value || '').trim();
        if (!q) return;
        window.location.href = `/catalog/?q=${encodeURIComponent(q)}`;
      });
    }

    open();
  };

  const fetchSuggest = async (q) => {
    const url = `/api/search/?q=${encodeURIComponent(q)}`;
    const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (!res.ok) return [];
    const data = await res.json();
    return (data && data.results) ? data.results : [];
  };

  input.addEventListener('input', () => {
    const q = (input.value || '').trim();
    lastQ = q;
    if (timer) clearTimeout(timer);

    if (q.length < 2) {
      close();
      return;
    }

    timer = setTimeout(async () => {
      try {
        const current = lastQ;
        const items = await fetchSuggest(current);
        // input мог измениться пока мы ждали ответ
        if (current !== lastQ) return;
        render(items);
      } catch (e) {
        close();
      }
    }, 180);
  });

  input.addEventListener('focus', () => {
    if (dropdown.innerHTML.trim()) open();
  });

  document.addEventListener('click', (e) => {
    const t = e.target;
    if (!t) return;
    if (dropdown.contains(t) || input.contains(t)) return;
    close();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close();
  });
})();
