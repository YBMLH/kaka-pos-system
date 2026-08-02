/* Expenses, Cash Register, and Zakat views. */
KAKA_VIEWS.expenses = {
  title: () => t('nav.expenses'),
  async render(root) {
    UI.clear(root);
    const cats = (await API.get('/api/expenses/categories')).categories;
    const filter = UI.el('select', {}, [UI.el('option', { value: '' }, t('common.all'))].concat(cats.map(c => UI.el('option', { value: c }, c))));
    const holder = UI.el('div', {});
    root.appendChild(UI.el('div', { class: 'toolbar' }, [filter, UI.el('span', { class: 'spacer' }),
      UI.el('button', { class: 'btn btn-ghost btn-sm', text: '⬇ Excel', onClick: () => API.download('/api/reports/financial?format=excel', 'financial.xlsx') }),
      can('expenses') ? UI.el('button', { class: 'btn btn-primary', text: '+ ' + t('common.add'), onClick: () => editModal(null) }) : null]));
    root.appendChild(holder);
    filter.addEventListener('change', load);
    load();
    async function load() {
      const d = await API.get('/api/expenses?category=' + filter.value);
      UI.clear(holder);
      holder.appendChild(UI.el('div', { class: 'stat stat-accent-red mb' }, [
        UI.el('div', { class: 'stat-label', text: 'Total Expenses' }), UI.el('div', { class: 'stat-value', text: money(d.total) })]));
      holder.appendChild(UI.table([
        { key: 'spent_on', label: t('common.date') }, { key: 'category', label: 'Category', render: r => UI.badge(r.category, 'orange') },
        { key: 'amount', label: 'Amount', num: true, render: r => money(r.amount) }, { key: 'note', label: 'Note' },
        { key: 'username', label: 'By' },
        { key: 'act', label: '', num: true, render: r => can('expenses') ? UI.el('div', { class: 'flex', style: 'justify-content:flex-end' }, [
          iconAction('✏️', 'Edit', () => editModal(r)), iconAction('🗑', 'Delete', () => UI.confirm('Delete expense?', async () => { await API.del('/api/expenses/' + r.id); load(); }))]) : '' },
      ], d.expenses, { empty: 'No expenses' }));
    }
    function editModal(r) {
      const form = UI.form([
        { name: 'category', label: 'Category', type: 'select', options: cats.map(c => ({ value: c, label: c })) },
        { name: 'amount', label: 'Amount', type: 'number', step: '0.01' },
        { name: 'spent_on', label: t('common.date'), type: 'date' },
        { name: 'note', label: 'Note', type: 'textarea', full: true }], r || {});
      UI.modal(r ? t('common.edit') : t('common.add'), form.node, [
        { label: t('common.cancel'), class: 'btn-ghost' },
        { label: t('common.save'), class: 'btn-primary', onClick: async () => {
          const v = form.values(); if (r) await API.put('/api/expenses/' + r.id, v); else await API.post('/api/expenses', v);
          UI.toast('Saved', 'success'); load(); } }]);
    }
  },
};

KAKA_VIEWS.register = {
  title: () => t('nav.register'),
  async render(root) {
    UI.clear(root);
    const d = await API.get('/api/registers/current');
    if (!d.register) {
      const opening = UI.el('input', { type: 'number', step: '0.01', value: 0 });
      root.appendChild(UI.el('div', { class: 'card', style: 'max-width:420px;margin:auto' }, [
        UI.el('h3', { class: 'mb', text: 'Open Cash Register' }),
        UI.el('div', { class: 'field mb' }, [UI.el('label', { text: 'Opening Cash' }), opening]),
        UI.el('button', { class: 'btn btn-primary btn-block', text: 'Open Register', onClick: async () => {
          await API.post('/api/registers/open', { opening_cash: parseFloat(opening.value) || 0 });
          UI.toast('Register opened', 'success'); KAKA_VIEWS.register.render(root); } })]));
    } else {
      const r = d.register;
      const counted = UI.el('input', { type: 'number', step: '0.01', value: r.expected_cash });
      const diffEl = UI.el('strong', { text: money(0) });
      counted.addEventListener('input', () => { const diff = (parseFloat(counted.value) || 0) - r.expected_cash;
        diffEl.textContent = money(diff); diffEl.className = diff === 0 ? '' : (diff > 0 ? 'up' : 'down'); });
      root.appendChild(UI.el('div', { class: 'grid stats-grid mb' }, [
        stat('Opening Cash', money(r.opening_cash), '', 'blue'),
        stat('Cash Sales', money(r.cash_sales), '', 'green'),
        stat('Expected in Drawer', money(r.expected_cash), '', 'orange')]));
      root.appendChild(UI.el('div', { class: 'card', style: 'max-width:460px' }, [
        UI.el('h3', { class: 'mb', text: 'Close Register (Cash Count)' }),
        UI.el('div', { class: 'field mb' }, [UI.el('label', { text: 'Counted Cash' }), counted]),
        UI.el('div', { class: 'flex mb', style: 'justify-content:space-between' }, [UI.el('span', { text: 'Difference' }), diffEl]),
        UI.el('button', { class: 'btn btn-danger btn-block', text: 'Close Register', onClick: async () => {
          const res = await API.post('/api/registers/close', { counted_cash: parseFloat(counted.value) || 0 });
          UI.toast(`Closed. Difference: ${money(res.difference)}`, res.difference === 0 ? 'success' : 'error');
          KAKA_VIEWS.register.render(root); } })]));
    }
    const hist = await API.get('/api/registers/history');
    root.appendChild(UI.el('div', { class: 'card mt' }, [UI.el('h3', { class: 'mb', text: 'Register History' }),
      UI.table([{ key: 'opened_at', label: 'Opened' }, { key: 'closed_at', label: 'Closed' }, { key: 'username', label: 'By' },
        { key: 'opening_cash', label: 'Opening', num: true, render: x => money(x.opening_cash) },
        { key: 'counted_cash', label: 'Counted', num: true, render: x => x.counted_cash != null ? money(x.counted_cash) : '—' },
        { key: 'difference', label: 'Difference', num: true, render: x => x.difference != null ? `<span class="${x.difference == 0 ? '' : (x.difference > 0 ? 'up' : 'down')}">${money(x.difference)}</span>` : '—' },
        { key: 'status', label: 'Status', render: x => UI.badge(x.status, x.status === 'open' ? 'green' : 'gray') }], hist.registers, { empty: 'No history' })]));
  },
};

KAKA_VIEWS.zakat = {
  title: () => t('nav.zakat'),
  async render(root) {
    UI.clear(root);
    const d = await API.get('/api/zakat/defaults');
    const fields = ['cash_on_hand', 'bank_balance', 'inventory_value', 'receivables', 'debts'];
    const labels = { cash_on_hand: 'Cash on Hand', bank_balance: 'Bank Balance', inventory_value: 'Inventory Value', receivables: 'Receivables', debts: 'Debts (subtract)' };
    const inputs = {};
    const rateInput = UI.el('input', { type: 'number', step: '0.01', value: d.rate, style: 'width:100px' });
    const form = UI.el('div', { class: 'form-grid' }, fields.map(f => {
      const i = UI.el('input', { type: 'number', step: '0.01', value: d.inputs[f] });
      i.addEventListener('input', recalc); inputs[f] = i;
      return UI.el('div', { class: 'field' }, [UI.el('label', { text: labels[f] }), i]);
    }));
    rateInput.addEventListener('input', recalc);
    const results = UI.el('div', { class: 'grid stats-grid mt' });
    root.appendChild(UI.el('div', { class: 'card' }, [
      UI.el('h3', { class: 'mb', text: '🕌 Zakat Calculator (2.5% on net zakatable wealth)' }),
      form,
      UI.el('div', { class: 'field mt', style: 'max-width:200px' }, [UI.el('label', { text: 'Zakat Rate %' }), rateInput]),
      results,
      UI.el('button', { class: 'btn btn-primary mt', text: '⬇ Download PDF Report', onClick: downloadReport })]));
    recalc();
    async function recalc() {
      const payload = { rate: parseFloat(rateInput.value) || 2.5 };
      fields.forEach(f => payload[f] = parseFloat(inputs[f].value) || 0);
      const res = await API.post('/api/zakat/calculate', payload);
      UI.clear(results);
      results.appendChild(stat('Net Zakatable Wealth', money(res.net_zakatable), '', 'blue'));
      results.appendChild(stat('Zakat Due (Yearly)', money(res.zakat_due), `${res.rate}%`, 'green'));
      results.appendChild(stat('Quarterly Estimate', money(res.quarterly_estimate), '', 'orange'));
      results.appendChild(stat('Monthly Estimate', money(res.monthly_estimate), '', 'orange'));
    }
    async function downloadReport() {
      const payload = { rate: parseFloat(rateInput.value) || 2.5 };
      fields.forEach(f => payload[f] = parseFloat(inputs[f].value) || 0);
      const res = await fetch('/api/zakat/report', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const blob = await res.blob(); const a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = 'zakat_report.pdf'; a.click();
    }
  },
};
