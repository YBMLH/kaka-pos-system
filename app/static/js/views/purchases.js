/* Purchases view — orders, receiving, and automatic reordering. */
KAKA_VIEWS.purchases = {
  title: () => t('nav.purchases'),
  async render(root) {
    UI.clear(root);
    let active = 'orders';
    const tabBar = UI.el('div', { class: 'tabs' }, [
      tab('orders', 'Purchase Orders'), tab('reorder', '🔄 Auto Reorder')]);
    const body = UI.el('div', {});
    root.appendChild(tabBar); root.appendChild(body);
    function tab(id, label) {
      return UI.el('div', { class: 'tab' + (id === active ? ' active' : ''), text: label,
        onClick: e => { active = id; tabBar.querySelectorAll('.tab').forEach(x => x.classList.remove('active')); e.target.classList.add('active'); draw(); } });
    }
    draw();
    async function draw() { UI.clear(body); if (active === 'orders') drawOrders(); else drawReorder(); }

    async function drawOrders() {
      const [d, suppliers] = await Promise.all([API.get('/api/purchases'), API.get('/api/suppliers').then(x => x.suppliers)]);
      body.appendChild(UI.el('div', { class: 'toolbar' }, [UI.el('span', { class: 'spacer' }),
        can('purchases') ? UI.el('button', { class: 'btn btn-primary', text: '+ New Order', onClick: () => newOrder(suppliers) }) : null]));
      body.appendChild(UI.table([
        { key: 'reference', label: 'Reference' }, { key: 'supplier_name', label: 'Supplier', render: r => r.supplier_name || '—' },
        { key: 'total', label: 'Total', num: true, render: r => money(r.total) },
        { key: 'status', label: 'Status', render: r => UI.badge(r.status, statusColor(r.status)) },
        { key: 'created_at', label: 'Date' },
        { key: 'act', label: '', num: true, render: r => {
          const w = UI.el('div', { class: 'flex', style: 'justify-content:flex-end' });
          w.appendChild(iconAction('👁', 'View', () => viewOrder(r)));
          if (can('purchases') && !['received', 'cancelled'].includes(r.status))
            w.appendChild(UI.el('button', { class: 'btn btn-sm btn-success', text: 'Receive', onClick: () => receiveOrder(r) }));
          return w; } },
      ], d.purchases, { empty: 'No purchase orders' }));
    }
    async function viewOrder(r) {
      const d = await API.get('/api/purchases/' + r.id);
      UI.modal(d.purchase.reference, UI.table([
        { key: 'name', label: 'Product' }, { key: 'quantity', label: 'Ordered', num: true, render: x => num(x.quantity) },
        { key: 'received_qty', label: 'Received', num: true, render: x => num(x.received_qty) },
        { key: 'cost', label: 'Cost', num: true, render: x => money(x.cost) },
        { key: 'line_total', label: 'Total', num: true, render: x => money(x.line_total) }], d.purchase.items), null, { large: true });
    }
    async function receiveOrder(r) {
      const d = await API.get('/api/purchases/' + r.id);
      const inputs = {};
      const rows = d.purchase.items.map(it => { const outstanding = it.quantity - it.received_qty;
        const i = UI.el('input', { type: 'number', step: 'any', value: outstanding, style: 'width:90px' });
        inputs[it.id] = i; return { it, i }; });
      UI.modal('Receive · ' + r.reference, UI.table([
        { key: 'name', label: 'Product', render: x => x.it.name },
        { key: 'out', label: 'Outstanding', num: true, render: x => num(x.it.quantity - x.it.received_qty) },
        { key: 'recv', label: 'Receive Now', num: true, render: x => x.i }], rows), [
        { label: t('common.cancel'), class: 'btn-ghost' },
        { label: 'Confirm Receiving', class: 'btn-success', onClick: async () => {
          const items = Object.entries(inputs).map(([id, i]) => ({ purchase_item_id: +id, received: parseFloat(i.value) || 0 }));
          const res = await API.post(`/api/purchases/${r.id}/receive`, { items });
          UI.toast('Received (' + res.status + ')', 'success'); draw(); } }], { large: true });
    }
    function newOrder(suppliers) {
      const items = [];
      const supplierSel = UI.el('select', {}, [UI.el('option', { value: '' }, '— Supplier —')].concat(suppliers.map(s => UI.el('option', { value: s.id }, s.company_name))));
      const invoice = UI.el('input', { placeholder: 'Invoice number' });
      const itemsBox = UI.el('div', {});
      const search = UI.el('input', { placeholder: 'Search product to add...' });
      let timer;
      search.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(async () => {
        if (!search.value.trim()) return;
        const d = await API.get('/api/products/search?q=' + encodeURIComponent(search.value.trim()));
        if (d.products[0]) { addItem(d.products[0]); search.value = ''; } }, 250); });
      function addItem(p) {
        if (items.find(i => i.product_id === p.id)) return;
        items.push({ product_id: p.id, name: p.name_en || p.name_ar, quantity: 1, cost: p.purchase_price });
        renderItems();
      }
      function renderItems() {
        UI.clear(itemsBox);
        itemsBox.appendChild(UI.table([
          { key: 'name', label: 'Product' },
          { key: 'quantity', label: 'Qty', num: true, render: it => { const i = UI.el('input', { type: 'number', step: 'any', value: it.quantity, style: 'width:80px' }); i.addEventListener('change', () => it.quantity = parseFloat(i.value) || 0); return i; } },
          { key: 'cost', label: 'Cost', num: true, render: it => { const i = UI.el('input', { type: 'number', step: '0.01', value: it.cost, style: 'width:90px' }); i.addEventListener('change', () => it.cost = parseFloat(i.value) || 0); return i; } },
          { key: 'x', label: '', num: true, render: it => UI.el('button', { class: 'btn btn-sm btn-danger', text: '×', onClick: () => { items.splice(items.indexOf(it), 1); renderItems(); } }) },
        ], items, { empty: 'Add products above' }));
      }
      renderItems();
      UI.modal('New Purchase Order', UI.el('div', {}, [
        UI.el('div', { class: 'form-grid mb' }, [
          UI.el('div', { class: 'field' }, [UI.el('label', { text: 'Supplier' }), supplierSel]),
          UI.el('div', { class: 'field' }, [UI.el('label', { text: 'Invoice' }), invoice])]),
        UI.el('div', { class: 'field mb' }, [UI.el('label', { text: 'Add product' }), search]),
        itemsBox]), [
        { label: t('common.cancel'), class: 'btn-ghost' },
        { label: 'Save as Draft', class: 'btn-ghost', onClick: () => save('draft') },
        { label: 'Create Order', class: 'btn-primary', onClick: () => save('ordered') }], { large: true });
      async function save(status) {
        if (!items.length) { UI.toast('Add at least one product', 'error'); return false; }
        await API.post('/api/purchases', { supplier_id: supplierSel.value || null, invoice_number: invoice.value, status, items });
        UI.toast('Order created', 'success'); draw();
      }
    }

    async function drawReorder() {
      const d = await API.get('/api/purchases/reorder-suggestions');
      body.appendChild(UI.el('div', { class: 'toolbar' }, [
        UI.el('p', { class: 'muted', text: 'Products at or below minimum stock, grouped by supplier.' }),
        UI.el('span', { class: 'spacer' }),
        can('purchases') && d.groups.length ? UI.el('button', { class: 'btn btn-primary', text: '⚡ Generate Draft Orders', onClick: async () => {
          const r = await API.post('/api/purchases/generate-reorders'); UI.toast(`Created ${r.created.length} draft orders`, 'success'); active = 'orders'; draw(); } }) : null]));
      if (!d.groups.length) { body.appendChild(UI.el('div', { class: 'empty', text: '✅ Nothing needs reordering' })); return; }
      d.groups.forEach(g => {
        body.appendChild(UI.el('div', { class: 'card mb' }, [
          UI.el('div', { class: 'section-head' }, [
            UI.el('h3', { text: g.supplier_name }),
            UI.el('span', { class: 'muted', text: [g.phone, g.whatsapp && ('WhatsApp: ' + g.whatsapp), g.email].filter(Boolean).join(' · ') })]),
          UI.table([
            { key: 'name', label: 'Product' }, { key: 'barcode', label: t('prod.barcode') },
            { key: 'quantity', label: 'Current', num: true, render: r => num(r.quantity) },
            { key: 'min_stock', label: 'Min', num: true, render: r => num(r.min_stock) },
            { key: 'reorder_qty', label: 'Suggested Order', num: true, render: r => `<strong>${num(r.reorder_qty)}</strong>` },
          ], g.items)]));
      });
    }
  },
};
function statusColor(s) { return { received: 'green', partial: 'orange', draft: 'gray', ordered: 'blue', cancelled: 'red' }[s] || 'gray'; }
