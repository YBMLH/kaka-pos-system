/* Suppliers and Customers views. */
KAKA_VIEWS.suppliers = {
  title: () => t('nav.suppliers'),
  async render(root) {
    UI.clear(root);
    const search = UI.el('input', { class: 'grow', placeholder: t('common.search') });
    const holder = UI.el('div', {});
    root.appendChild(UI.el('div', { class: 'toolbar' }, [search, UI.el('span', { class: 'spacer' }),
      can('suppliers') ? UI.el('button', { class: 'btn btn-primary', text: '+ ' + t('common.add'), onClick: () => editModal(null) }) : null]));
    root.appendChild(holder);
    let timer;
    search.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(load, 200); });
    load();
    async function load() {
      const d = await API.get('/api/suppliers?q=' + encodeURIComponent(search.value.trim()));
      UI.clear(holder);
      holder.appendChild(UI.table([
        { key: 'company_name', label: 'Company', render: r => `<strong>${UI.esc(r.company_name)}</strong><br><span class="muted">${UI.esc(r.contact_person || '')}</span>` },
        { key: 'phone1', label: t('common.phone') },
        { key: 'category', label: 'Category' },
        { key: 'balance', label: 'We Owe', num: true, render: r => `<span class="${r.balance > 0 ? 'down' : ''}">${money(r.balance)}</span>` },
        { key: 'act', label: '', num: true, render: r => {
          const w = UI.el('div', { class: 'flex', style: 'justify-content:flex-end' });
          w.appendChild(iconAction('👁', 'View', () => viewModal(r)));
          if (can('suppliers')) { w.appendChild(iconAction('✏️', 'Edit', () => editModal(r)));
            w.appendChild(iconAction('💵', 'Pay', () => payModal(r)));
            w.appendChild(iconAction('🗑', 'Delete', () => UI.confirm('Delete supplier?', async () => { await API.del('/api/suppliers/' + r.id); load(); }))); }
          return w; } },
      ], d.suppliers, { empty: 'No suppliers' }));
    }
    async function viewModal(r) {
      const d = await API.get('/api/suppliers/' + r.id);
      const s = d.supplier;
      const body = UI.el('div', {}, [
        UI.el('div', { class: 'grid', style: 'grid-template-columns:1fr 1fr' }, [
          info('Contact', s.contact_person), info('Phone 1', s.phone1), info('Phone 2', s.phone2),
          info('WhatsApp', s.whatsapp), info('Email', s.email), info('City', s.city),
          info('Country', s.country), info('Tax No.', s.tax_number)]),
        UI.el('h4', { class: 'mt mb', text: 'Purchases' }),
        UI.table([{ key: 'reference', label: 'Ref' }, { key: 'total', label: 'Total', num: true, render: x => money(x.total) },
          { key: 'status', label: 'Status', render: x => UI.badge(x.status, 'blue') }, { key: 'created_at', label: 'Date' }], d.purchases, { empty: 'None' }),
        UI.el('h4', { class: 'mt mb', text: 'Payments' }),
        UI.table([{ key: 'created_at', label: 'Date' }, { key: 'amount', label: 'Amount', num: true, render: x => money(x.amount) }, { key: 'method', label: 'Method' }], d.payments, { empty: 'None' }),
      ]);
      UI.modal(s.company_name, body, null, { large: true });
    }
    function payModal(r) {
      const amount = UI.el('input', { type: 'number', step: '0.01', placeholder: 'Amount' });
      const method = UI.el('select', {}, ['cash', 'card', 'transfer'].map(m => UI.el('option', { value: m }, m)));
      UI.modal('Record Payment · ' + r.company_name, UI.el('div', {}, [
        UI.el('p', { class: 'mb', text: 'Outstanding: ' + money(r.balance) }),
        UI.el('div', { class: 'field' }, [UI.el('label', { text: 'Amount' }), amount]),
        UI.el('div', { class: 'field mt' }, [UI.el('label', { text: 'Method' }), method])]), [
        { label: t('common.cancel'), class: 'btn-ghost' },
        { label: 'Save', class: 'btn-primary', onClick: async () => {
          await API.post(`/api/suppliers/${r.id}/payment`, { amount: parseFloat(amount.value) || 0, method: method.value });
          UI.toast('Payment recorded', 'success'); load(); } }]);
    }
    function editModal(r) {
      const form = UI.form([
        { name: 'company_name', label: 'Company Name', full: true },
        { name: 'contact_person', label: 'Contact Person' },
        { name: 'category', label: 'Category', type: 'select', options: ['Beverages','Dairy','Frozen Foods','Bakery','Meat','Vegetables','Fruits','Cleaning Products','Cosmetics','Electronics','Packaging','Miscellaneous'].map(c => ({ value: c, label: c })) },
        { name: 'phone1', label: 'Phone 1' }, { name: 'phone2', label: 'Phone 2' },
        { name: 'whatsapp', label: 'WhatsApp' }, { name: 'email', label: 'Email' },
        { name: 'website', label: 'Website' }, { name: 'tax_number', label: 'Tax Number' },
        { name: 'address', label: 'Address', full: true }, { name: 'city', label: 'City' },
        { name: 'country', label: 'Country' }, { name: 'notes', label: 'Notes', type: 'textarea', full: true },
      ], r || {});
      UI.modal(r ? t('common.edit') : t('common.add'), form.node, [
        { label: t('common.cancel'), class: 'btn-ghost' },
        { label: t('common.save'), class: 'btn-primary', onClick: async () => {
          const v = form.values();
          if (r) await API.put('/api/suppliers/' + r.id, v); else await API.post('/api/suppliers', v);
          UI.toast('Saved', 'success'); load(); } }], { large: true });
    }
  },
};

KAKA_VIEWS.customers = {
  title: () => t('nav.customers'),
  async render(root) {
    UI.clear(root);
    const search = UI.el('input', { class: 'grow', placeholder: t('common.search') });
    const holder = UI.el('div', {});
    root.appendChild(UI.el('div', { class: 'toolbar' }, [search, UI.el('span', { class: 'spacer' }),
      UI.el('button', { class: 'btn btn-primary', text: '+ ' + t('common.add'), onClick: () => editModal(null) })]));
    root.appendChild(holder);
    let timer; search.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(load, 200); });
    load();
    async function load() {
      const d = await API.get('/api/customers?q=' + encodeURIComponent(search.value.trim()));
      UI.clear(holder);
      holder.appendChild(UI.table([
        { key: 'name', label: t('common.name'), render: r => `<strong>${UI.esc(r.name)}</strong>` },
        { key: 'phone', label: t('common.phone') }, { key: 'city', label: 'City' },
        { key: 'loyalty_pts', label: 'Loyalty', num: true, render: r => num(r.loyalty_pts) },
        { key: 'credit', label: 'Credit', num: true, render: r => `<span class="${r.credit > 0 ? 'down' : ''}">${money(r.credit)}</span>` },
        { key: 'act', label: '', num: true, render: r => {
          const w = UI.el('div', { class: 'flex', style: 'justify-content:flex-end' });
          w.appendChild(iconAction('👁', 'View', () => viewModal(r)));
          w.appendChild(iconAction('✏️', 'Edit', () => editModal(r)));
          if (r.credit > 0) w.appendChild(iconAction('💵', 'Settle', () => settleModal(r)));
          return w; } },
      ], d.customers, { empty: 'No customers' }));
    }
    async function viewModal(r) {
      const d = await API.get('/api/customers/' + r.id);
      UI.modal(r.name, UI.el('div', {}, [
        UI.el('div', { class: 'grid stats-grid mb' }, [
          stat('Orders', num(d.stats.orders), '', 'blue'), stat('Total Spent', money(d.stats.spent), '', 'green'),
          stat('Loyalty', num(d.customer.loyalty_pts), 'points', 'orange')]),
        UI.table([{ key: 'receipt_no', label: 'Receipt' }, { key: 'total', label: 'Total', num: true, render: x => money(x.total) },
          { key: 'payment_method', label: 'Method' }, { key: 'created_at', label: 'Date' }], d.sales, { empty: 'No purchases' })]), null, { large: true });
    }
    function settleModal(r) {
      const amount = UI.el('input', { type: 'number', step: '0.01', value: r.credit });
      UI.modal('Settle Credit · ' + r.name, UI.el('div', { class: 'field' }, [UI.el('label', { text: 'Amount' }), amount]), [
        { label: t('common.cancel'), class: 'btn-ghost' },
        { label: 'Settle', class: 'btn-primary', onClick: async () => { await API.post(`/api/customers/${r.id}/settle`, { amount: parseFloat(amount.value) || 0 }); UI.toast('Settled', 'success'); load(); } }]);
    }
    function editModal(r) {
      const form = UI.form([
        { name: 'name', label: t('common.name'), full: true }, { name: 'phone', label: t('common.phone') },
        { name: 'city', label: 'City' }, { name: 'address', label: 'Address', full: true },
        { name: 'notes', label: 'Notes', type: 'textarea', full: true }], r || {});
      UI.modal(r ? t('common.edit') : t('common.add'), form.node, [
        { label: t('common.cancel'), class: 'btn-ghost' },
        { label: t('common.save'), class: 'btn-primary', onClick: async () => {
          const v = form.values(); if (r) await API.put('/api/customers/' + r.id, v); else await API.post('/api/customers', v);
          UI.toast('Saved', 'success'); load(); } }], { large: true });
    }
  },
};

function info(label, value) {
  return UI.el('div', { class: 'field' }, [UI.el('label', { text: label }), UI.el('div', { text: value || '—' })]);
}
