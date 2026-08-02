/* Dashboard & Business Health views. */
KAKA_VIEWS.dashboard = {
  title: () => t('nav.dashboard'),
  async render(root) {
    root.innerHTML = '<p class="muted">' + t('common.loading') + '</p>';
    const [sum, comp, chart, top, health] = await Promise.all([
      API.get('/api/dashboard/summary'),
      API.get('/api/dashboard/comparisons'),
      API.get('/api/dashboard/chart?range=30d'),
      API.get('/api/dashboard/top'),
      API.get('/api/dashboard/health'),
    ]);
    UI.clear(root);

    const today = sum.today, month = sum.month;
    const stats = UI.el('div', { class: 'grid stats-grid' }, [
      stat(t('dash.today_revenue'), money(today.revenue), `${today.orders} orders`, 'blue'),
      stat(t('dash.today_profit'), money(today.gross_profit), 'Gross', 'green'),
      stat(t('dash.month_revenue'), money(month.revenue), `${month.orders} orders`, 'blue'),
      stat(t('dash.net_profit'), money(month.net_profit), 'This month', 'green'),
      stat(t('dash.inventory_value'), money(sum.inventory.cost_value), 'At cost', 'orange'),
      stat(t('dash.expenses'), money(month.expenses), 'This month', 'red'),
    ]);
    root.appendChild(stats);

    // Period income breakdown
    const periods = ['today', 'week', 'month', 'quarter', 'half', 'year'];
    const plabels = { today: 'Today', week: 'This Week', month: 'This Month',
      quarter: 'This Quarter', half: 'Half Year', year: 'This Year' };
    const periodRows = periods.map(p => ({
      period: plabels[p], revenue: sum[p].revenue, profit: sum[p].gross_profit,
      expenses: sum[p].expenses, net: sum[p].net_profit,
    }));
    const periodCard = UI.el('div', { class: 'card mt' }, [
      UI.el('div', { class: 'section-head' }, UI.el('h3', { text: 'Income by Period' })),
      UI.table([
        { key: 'period', label: 'Period' },
        { key: 'revenue', label: 'Revenue', num: true, render: r => money(r.revenue) },
        { key: 'profit', label: 'Gross Profit', num: true, render: r => money(r.profit) },
        { key: 'expenses', label: 'Expenses', num: true, render: r => money(r.expenses) },
        { key: 'net', label: 'Net Profit', num: true, render: r =>
          `<strong class="${r.net >= 0 ? 'up' : 'down'}">${money(r.net)}</strong>` },
      ], periodRows),
    ]);
    root.appendChild(periodCard);

    // Chart
    const chartCard = UI.el('div', { class: 'card mt' }, [
      UI.el('div', { class: 'section-head' }, [
        UI.el('h3', { text: 'Revenue (last 30 days)' }),
        UI.el('div', { class: 'flex' }, [
          rangeBtn('7d', chartCard_render), rangeBtn('30d', chartCard_render, true),
          rangeBtn('12m', chartCard_render),
        ]),
      ]),
      UI.el('div', { id: 'dash-chart' }),
    ]);
    root.appendChild(chartCard);
    drawChart(chart.series);
    function chartCard_render(range, btn) {
      chartCard.querySelectorAll('button').forEach(b => b.classList.remove('btn-primary'));
      btn.classList.add('btn-primary');
      API.get('/api/dashboard/chart?range=' + range).then(d => drawChart(d.series));
    }
    function drawChart(series) {
      const holder = document.getElementById('dash-chart');
      UI.clear(holder);
      if (!series.length) { holder.innerHTML = '<p class="empty">No sales yet</p>'; return; }
      holder.appendChild(UI.barChart(series.map(s => ({
        label: s.label.slice(5), value: s.revenue, value2: s.profit }))));
    }

    // Comparisons + top lists + health
    const bottom = UI.el('div', { class: 'grid mt', style: 'grid-template-columns:1fr 1fr' }, [
      comparisonCard(comp), healthCard(health),
    ]);
    root.appendChild(bottom);

    const topCard = UI.el('div', { class: 'grid mt', style: 'grid-template-columns:1fr 1fr' }, [
      UI.el('div', { class: 'card' }, [
        UI.el('h3', { class: 'mb', text: 'Top Products (30d)' }),
        UI.table([
          { key: 'name', label: 'Product' },
          { key: 'qty', label: 'Qty', num: true, render: r => num(r.qty) },
          { key: 'revenue', label: 'Revenue', num: true, render: r => money(r.revenue) },
        ], top.top_products, { empty: 'No sales' }),
      ]),
      UI.el('div', { class: 'card' }, [
        UI.el('h3', { class: 'mb', text: 'Top Categories (30d)' }),
        UI.table([
          { key: 'name', label: 'Category' },
          { key: 'revenue', label: 'Revenue', num: true, render: r => money(r.revenue) },
        ], top.top_categories, { empty: 'No sales' }),
      ]),
    ]);
    root.appendChild(topCard);
  },
};

function stat(label, value, sub, accent) {
  return UI.el('div', { class: 'stat stat-accent-' + accent }, [
    UI.el('div', { class: 'stat-label', text: label }),
    UI.el('div', { class: 'stat-value', text: value }),
    UI.el('div', { class: 'stat-sub', text: sub }),
  ]);
}
function rangeBtn(range, cb, active) {
  const b = UI.el('button', { class: 'btn btn-sm ' + (active ? 'btn-primary' : ''), text: range });
  b.addEventListener('click', () => cb(range, b));
  return b;
}
function comparisonCard(comp) {
  const rows = [
    ['Today vs Yesterday', comp.day], ['This Week vs Last', comp.week],
    ['This Month vs Last', comp.month], ['This Year vs Last', comp.year],
  ];
  return UI.el('div', { class: 'card' }, [
    UI.el('h3', { class: 'mb', text: 'Comparisons' }),
    UI.table([
      { key: 'label', label: 'Period' },
      { key: 'rev', label: 'Revenue', num: true, render: r => money(r.d.current.revenue) },
      { key: 'growth', label: 'Growth', num: true, render: r => {
        const g = r.d.revenue_growth;
        return `<span class="${g >= 0 ? 'up' : 'down'}">${g >= 0 ? '▲' : '▼'} ${Math.abs(g)}%</span>`;
      } },
      { key: 'diff', label: 'Difference', num: true, render: r =>
        `<span class="${r.d.revenue_diff >= 0 ? 'up' : 'down'}">${money(r.d.revenue_diff)}</span>` },
    ], rows.map(([label, d]) => ({ label, d }))),
  ]);
}
function healthCard(health) {
  const items = Object.entries(health.indicators).map(([, v]) =>
    UI.el('div', { class: 'flex', style: 'justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border)' }, [
      UI.el('div', { class: 'flex' }, [
        UI.el('span', { class: 'health-dot health-' + v.status }),
        UI.el('span', { text: v.label }),
      ]),
      UI.el('strong', { text: typeof v.value === 'number' ? num(v.value, 2) : v.value }),
    ]));
  return UI.el('div', { class: 'card' }, [
    UI.el('div', { class: 'section-head' }, [
      UI.el('h3', { text: t('nav.health') }),
      UI.el('span', { class: 'badge badge-' + healthColor(health.overall),
        text: health.overall.toUpperCase() }),
    ]),
    ...items,
    UI.el('div', { class: 'flex mt', style: 'justify-content:space-between' }, [
      UI.el('span', { class: 'muted', text: 'Net worth estimate' }),
      UI.el('strong', { text: money(health.net_worth_estimate) }),
    ]),
  ]);
}
function healthColor(s) { return s === 'green' ? 'green' : (s === 'orange' ? 'orange' : 'red'); }
