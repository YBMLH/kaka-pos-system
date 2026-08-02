/* Reports view — sales, inventory, suppliers, customers, financial, employees. */
KAKA_VIEWS.reports = {
  title: () => t('nav.reports'),
  async render(root) {
    UI.clear(root);
    const reports = {
      sales: 'Sales', inventory: 'Inventory', financial: 'Financial',
      suppliers: 'Suppliers', customers: 'Customers', employees: 'Employees',
    };
    let active = 'sales';
    const tabBar = UI.el('div', { class: 'tabs' }, Object.entries(reports).map(([id, label]) =>
      UI.el('div', { class: 'tab' + (id === active ? ' active' : ''), text: label,
        onClick: e => { active = id; tabBar.querySelectorAll('.tab').forEach(x => x.classList.remove('active')); e.target.classList.add('active'); draw(); } })));
    const controls = UI.el('div', { class: 'toolbar' });
    const from = UI.el('input', { type: 'date' });
    const to = UI.el('input', { type: 'date' });
    const groupSel = UI.el('select', {}, ['day', 'week', 'month', 'quarter', 'year'].map(g => UI.el('option', { value: g }, g)));
    groupSel.value = 'day';
    const body = UI.el('div', {});
    root.appendChild(tabBar); root.appendChild(controls); root.appendChild(body);
    draw();

    function buildQuery(extra) {
      const p = new URLSearchParams(extra || {});
      if (from.value) p.set('date_from', from.value);
      if (to.value) p.set('date_to', to.value);
      return p.toString();
    }
    function draw() {
      UI.clear(controls);
      controls.appendChild(UI.el('label', { text: 'From' })); controls.appendChild(from);
      controls.appendChild(UI.el('label', { text: 'To' })); controls.appendChild(to);
      if (active === 'sales') { controls.appendChild(UI.el('label', { text: 'Group' })); controls.appendChild(groupSel); }
      controls.appendChild(UI.el('button', { class: 'btn btn-primary btn-sm', text: '↻ ' + t('common.search'), onClick: run }));
      controls.appendChild(UI.el('span', { class: 'spacer' }));
      ['excel', 'csv', 'pdf'].forEach(fmt => controls.appendChild(
        UI.el('button', { class: 'btn btn-ghost btn-sm', text: fmt.toUpperCase(),
          onClick: () => API.download(url(fmt), `${active}_report.${fmt === 'excel' ? 'xlsx' : fmt}`) })));
      run();
    }
    function url(fmt) {
      const extra = { format: fmt || 'json' };
      if (active === 'sales') extra.group = groupSel.value;
      return `/api/reports/${active}?` + buildQuery(extra);
    }
    async function run() {
      UI.clear(body);
      const d = await API.get(url());
      if (active === 'sales') return renderRows(d.rows, [
        { key: 'period', label: 'Period' }, { key: 'orders', label: 'Orders', num: true },
        { key: 'revenue', label: 'Revenue', num: true, render: r => money(r.revenue) },
        { key: 'profit', label: 'Profit', num: true, render: r => money(r.profit) },
        { key: 'tax', label: 'Tax', num: true, render: r => money(r.tax) }], d.totals);
      if (active === 'inventory') { const kindSel = UI.el('select', {}, ['stock', 'low', 'out', 'expiry'].map(k => UI.el('option', { value: k }, k)));
        return renderInventory(d, kindSel); }
      if (active === 'financial') return renderFinancial(d);
      if (active === 'suppliers') return renderRows(d.rows, [
        { key: 'name', label: 'Supplier' }, { key: 'phone1', label: 'Phone' },
        { key: 'orders', label: 'Orders', num: true }, { key: 'purchased', label: 'Purchased', num: true, render: r => money(r.purchased) },
        { key: 'balance', label: 'Balance', num: true, render: r => money(r.balance) }]);
      if (active === 'customers') return renderRows(d.rows, [
        { key: 'name', label: 'Customer' }, { key: 'phone', label: 'Phone' },
        { key: 'orders', label: 'Orders', num: true }, { key: 'spent', label: 'Spent', num: true, render: r => money(r.spent) },
        { key: 'credit', label: 'Credit', num: true, render: r => money(r.credit) }]);
      if (active === 'employees') return renderRows(d.rows, [
        { key: 'username', label: 'User' }, { key: 'full_name', label: 'Name' },
        { key: 'transactions', label: 'Transactions', num: true },
        { key: 'revenue', label: 'Revenue', num: true, render: r => money(r.revenue) },
        { key: 'profit', label: 'Profit', num: true, render: r => money(r.profit) }]);
    }
    function renderRows(rows, cols, totals) {
      if (totals) body.appendChild(UI.el('div', { class: 'grid stats-grid mb' }, [
        stat('Orders', num(totals.orders), '', 'blue'), stat('Revenue', money(totals.revenue), '', 'green'),
        stat('Profit', money(totals.profit), '', 'orange')]));
      body.appendChild(UI.table(cols, rows, { empty: 'No data' }));
    }
    function renderInventory(d, kindSel) {
      kindSel.addEventListener('change', async () => { const dd = await API.get(`/api/reports/inventory?kind=${kindSel.value}`);
        UI.clear(tableHolder); tableHolder.appendChild(buildInvTable(dd)); });
      body.appendChild(UI.el('div', { class: 'toolbar' }, [UI.el('label', { text: 'View' }), kindSel]));
      const tableHolder = UI.el('div', {}); body.appendChild(tableHolder);
      tableHolder.appendChild(buildInvTable(d));
    }
    function buildInvTable(d) {
      return UI.el('div', {}, [
        UI.el('div', { class: 'stat stat-accent-blue mb' }, [UI.el('div', { class: 'stat-label', text: 'Total Stock Value' }), UI.el('div', { class: 'stat-value', text: money(d.total_value) })]),
        UI.table([{ key: 'name', label: 'Product' }, { key: 'barcode', label: 'Barcode' },
          { key: 'quantity', label: 'Qty', num: true, render: r => num(r.quantity, 2) },
          { key: 'selling_price', label: 'Price', num: true, render: r => money(r.selling_price) },
          { key: 'expiry_date', label: 'Expiry', render: r => r.expiry_date || '—' },
          { key: 'stock_value', label: 'Value', num: true, render: r => money(r.stock_value) }], d.rows, { empty: 'No data' })]);
    }
    function renderFinancial(d) {
      body.appendChild(UI.el('div', { class: 'grid stats-grid' }, [
        stat('Revenue', money(d.revenue), '', 'blue'), stat('Cost of Goods', money(d.cost_of_goods), '', 'orange'),
        stat('Gross Profit', money(d.gross_profit), '', 'green'), stat('Expenses', money(d.expenses), '', 'red'),
        stat('Tax Collected', money(d.tax_collected), '', 'blue'), stat('Net Profit', money(d.net_profit), '', 'green')]));
      body.appendChild(UI.el('div', { class: 'card mt' }, [UI.el('h3', { class: 'mb', text: 'Expenses by Category' }),
        UI.table([{ key: 'category', label: 'Category' }, { key: 'total', label: 'Total', num: true, render: r => money(r.total) }], d.expenses_by_category, { empty: 'No expenses' })]));
    }
  },
};
