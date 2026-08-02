/* Inventory view — value, alerts, adjustments, movements, count sessions. */
KAKA_VIEWS.inventory = {
  title: () => t('nav.inventory'),
  async render(root) {
    UI.clear(root);
    const tabs = ['alerts', 'adjust', 'movements', 'count'];
    const labels = { alerts: 'Alerts', adjust: 'Adjust Stock', movements: 'Movements', count: 'Count Session' };
    let active = 'alerts';
    const tabBar = UI.el('div', { class: 'tabs' }, tabs.map(tb =>
      UI.el('div', { class: 'tab' + (tb === active ? ' active' : ''), text: labels[tb],
        onClick: () => { active = tb; document.querySelectorAll('.tab').forEach(x => x.classList.remove('active')); event.target.classList.add('active'); draw(); } })));
    const body = UI.el('div', {});
    root.appendChild(tabBar); root.appendChild(body);

    const val = await API.get('/api/inventory/value');
    root.insertBefore(UI.el('div', { class: 'grid stats-grid mb' }, [
      stat('Inventory (cost)', money(val.cost_value), val.products + ' products', 'blue'),
      stat('Inventory (retail)', money(val.retail_value), num(val.total_units) + ' units', 'green'),
      stat('Potential profit', money(val.retail_value - val.cost_value), '', 'orange'),
    ]), tabBar);

    draw();
    async function draw() {
      UI.clear(body);
      if (active === 'alerts') return drawAlerts();
      if (active === 'adjust') return drawAdjust();
      if (active === 'movements') return drawMovements();
      if (active === 'count') return drawCount();
    }

    async function drawAlerts() {
      const d = await API.get('/api/inventory/alerts');
      body.appendChild(UI.el('div', { class: 'card mb' }, [
        UI.el('h3', { class: 'mb', text: '⚠ Low Stock (' + d.low_stock.length + ')' }),
        UI.table([
          { key: 'name_en', label: t('common.name') },
          { key: 'barcode', label: t('prod.barcode') },
          { key: 'quantity', label: t('prod.stock'), num: true, render: r => num(r.quantity) },
          { key: 'min_stock', label: 'Min', num: true, render: r => num(r.min_stock) },
        ], d.low_stock, { empty: 'All good' })]));
      body.appendChild(UI.el('div', { class: 'card mb' }, [
        UI.el('h3', { class: 'mb', text: '⛔ Out of Stock (' + d.out_of_stock.length + ')' }),
        UI.table([{ key: 'name_en', label: t('common.name') }, { key: 'barcode', label: t('prod.barcode') }], d.out_of_stock, { empty: 'None' })]));
      body.appendChild(UI.el('div', { class: 'card' }, [
        UI.el('h3', { class: 'mb', text: '📅 Expiring within 30 days (' + d.expiring.length + ')' }),
        UI.table([{ key: 'name_en', label: t('common.name') }, { key: 'expiry_date', label: 'Expiry' },
          { key: 'quantity', label: t('prod.stock'), num: true, render: r => num(r.quantity) }], d.expiring, { empty: 'None' })]));
    }

    async function drawAdjust() {
      const search = UI.el('input', { class: 'grow', placeholder: 'Search product to adjust...' });
      const results = UI.el('div', {});
      body.appendChild(UI.el('div', { class: 'card' }, [
        UI.el('div', { class: 'toolbar' }, [search]), results]));
      let timer;
      search.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(async () => {
        if (!search.value.trim()) { UI.clear(results); return; }
        const d = await API.get('/api/products/search?q=' + encodeURIComponent(search.value.trim()));
        UI.clear(results);
        results.appendChild(UI.table([
          { key: 'name_en', label: t('common.name') },
          { key: 'quantity', label: t('prod.stock'), num: true, render: r => num(r.quantity) },
          { key: 'act', label: '', num: true, render: r => UI.el('button', { class: 'btn btn-sm btn-primary', text: 'Adjust', onClick: () => adjustModal(r) }) },
        ], d.products, { empty: 'No match' }));
      }, 200); });
    }
    function adjustModal(p) {
      const reason = UI.el('select', {}, ['adjustment', 'damage', 'loss', 'expired', 'transfer'].map(r => UI.el('option', { value: r }, r)));
      const mode = UI.el('select', {}, [UI.el('option', { value: 'change' }, 'Add / Remove (±)'), UI.el('option', { value: 'set' }, 'Set exact quantity')]);
      const qty = UI.el('input', { type: 'number', step: 'any', value: 0 });
      const note = UI.el('input', { placeholder: 'Note (optional)' });
      const body2 = UI.el('div', {}, [
        UI.el('p', { class: 'mb', html: `<strong>${UI.esc(p.name_en)}</strong> — current: ${num(p.quantity)}` }),
        UI.el('div', { class: 'field' }, [UI.el('label', { text: 'Reason' }), reason]),
        UI.el('div', { class: 'field mt' }, [UI.el('label', { text: 'Mode' }), mode]),
        UI.el('div', { class: 'field mt' }, [UI.el('label', { text: 'Quantity' }), qty]),
        UI.el('div', { class: 'field mt' }, [UI.el('label', { text: 'Note' }), note]),
      ]);
      UI.modal('Adjust Stock', body2, [
        { label: t('common.cancel'), class: 'btn-ghost' },
        { label: t('common.save'), class: 'btn-primary', onClick: async () => {
          await API.post('/api/inventory/adjust', { product_id: p.id, reason: reason.value,
            mode: mode.value, change: parseFloat(qty.value) || 0, quantity: parseFloat(qty.value) || 0, note: note.value });
          UI.toast('Adjusted', 'success'); draw();
        } }]);
    }

    async function drawMovements() {
      const d = await API.get('/api/inventory/movements');
      body.appendChild(UI.el('div', { class: 'card' }, [
        UI.el('h3', { class: 'mb', text: 'Recent Movements' }),
        UI.table([
          { key: 'created_at', label: t('common.date') },
          { key: 'product_name', label: t('common.name') },
          { key: 'reason', label: 'Reason', render: r => UI.badge(r.reason, 'blue') },
          { key: 'change_qty', label: 'Change', num: true, render: r => (r.change_qty > 0 ? '+' : '') + num(r.change_qty, 2) },
          { key: 'balance', label: 'Balance', num: true, render: r => num(r.balance, 2) },
          { key: 'username', label: 'By' },
        ], d.movements, { empty: 'No movements' })]));
    }

    async function drawCount() {
      const d = await API.get('/api/products?per_page=200');
      const counts = {};
      const rows = d.products.map(p => ({ p, input: (() => {
        const i = UI.el('input', { type: 'number', step: 'any', value: p.quantity, style: 'width:90px' });
        i.addEventListener('change', () => { counts[p.id] = parseFloat(i.value) || 0; });
        counts[p.id] = p.quantity; return i; })() }));
      body.appendChild(UI.el('div', { class: 'card' }, [
        UI.el('div', { class: 'section-head' }, [UI.el('h3', { text: 'Physical Count' }),
          UI.el('button', { class: 'btn btn-primary', text: 'Reconcile', onClick: async () => {
            const payload = Object.entries(counts).map(([id, c]) => ({ product_id: +id, counted: c }));
            const r = await API.post('/api/inventory/count-session', { counts: payload });
            UI.toast(`Reconciled ${r.adjusted} products`, 'success'); draw();
          } })]),
        UI.table([
          { key: 'name', label: t('common.name'), render: r => r.p.name_en },
          { key: 'system', label: 'System Qty', num: true, render: r => num(r.p.quantity) },
          { key: 'counted', label: 'Counted', num: true, render: r => r.input },
        ], rows)]));
    }
  },
};
