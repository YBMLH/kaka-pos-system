/* Users, Settings, Activity log, Backup, and Sales history views. */
KAKA_VIEWS.users = {
  title: () => t('nav.users'),
  async render(root) {
    UI.clear(root);
    let active = 'users';
    const tabBar = UI.el('div', { class: 'tabs' }, [
      tab('users', 'Users'), tab('activity', 'Activity Log'), tab('backup', 'Backups')]);
    const body = UI.el('div', {});
    root.appendChild(tabBar); root.appendChild(body);
    function tab(id, label) {
      return UI.el('div', { class: 'tab' + (id === active ? ' active' : ''), text: label,
        onClick: e => { active = id; tabBar.querySelectorAll('.tab').forEach(x => x.classList.remove('active')); e.target.classList.add('active'); draw(); } });
    }
    draw();
    async function draw() { UI.clear(body); if (active === 'users') drawUsers(); else if (active === 'activity') drawActivity(); else drawBackup(); }

    let roles = [];
    async function drawUsers() {
      const [d, r] = await Promise.all([API.get('/api/users'), API.get('/api/users/roles')]);
      roles = r.roles;
      body.appendChild(UI.el('div', { class: 'toolbar' }, [UI.el('span', { class: 'spacer' }),
        UI.el('button', { class: 'btn btn-primary', text: '+ ' + t('common.add'), onClick: () => userModal(null) })]));
      body.appendChild(UI.table([
        { key: 'username', label: 'Username', render: u => `<strong>${UI.esc(u.username)}</strong>` },
        { key: 'full_name', label: 'Full Name' }, { key: 'role_label', label: 'Role', render: u => UI.badge(u.role_label, 'blue') },
        { key: 'last_login', label: 'Last Login', render: u => u.last_login || '—' },
        { key: 'is_active', label: 'Status', render: u => UI.badge(u.is_active ? 'Active' : 'Disabled', u.is_active ? 'green' : 'gray') },
        { key: 'act', label: '', num: true, render: u => UI.el('div', { class: 'flex', style: 'justify-content:flex-end' }, [
          iconAction('✏️', 'Edit', () => userModal(u)),
          iconAction('🗑', 'Delete', () => UI.confirm('Disable user?', async () => { await API.del('/api/users/' + u.id); draw(); }))]) },
      ], d.users, { empty: 'No users' }));
    }
    function userModal(u) {
      const form = UI.form([
        { name: 'username', label: 'Username', hidden: !!u },
        { name: 'full_name', label: 'Full Name' }, { name: 'email', label: 'Email' },
        { name: 'phone', label: 'Phone' },
        { name: 'role_id', label: 'Role', type: 'select', options: roles.map(r => ({ value: r.id, label: r.label })) },
        { name: 'password', label: u ? 'New Password (blank = keep)' : 'Password', type: 'password' },
      ], u ? { ...u, role_id: roles.find(r => r.name === u.role)?.id } : {});
      UI.modal(u ? 'Edit User' : 'New User', form.node, [
        { label: t('common.cancel'), class: 'btn-ghost' },
        { label: t('common.save'), class: 'btn-primary', onClick: async () => {
          const v = form.values();
          try { if (u) { delete v.username; if (!v.password) delete v.password; await API.put('/api/users/' + u.id, v); }
            else await API.post('/api/users', v);
            UI.toast('Saved', 'success'); draw(); } catch (e) { UI.toast(e.message, 'error'); return false; } } }]);
    }

    async function drawActivity() {
      const d = await API.get('/api/users/activity');
      body.appendChild(UI.el('div', { class: 'card' }, [UI.el('h3', { class: 'mb', text: 'Audit Trail (last 500)' }),
        UI.table([{ key: 'created_at', label: t('common.date') }, { key: 'username', label: 'User' },
          { key: 'action', label: 'Action', render: r => UI.badge(r.action, 'blue') },
          { key: 'entity', label: 'Entity' }, { key: 'detail', label: 'Detail' }, { key: 'ip', label: 'IP' }], d.logs, { empty: 'No activity' })]));
    }

    async function drawBackup() {
      const d = await API.get('/api/backup');
      body.appendChild(UI.el('div', { class: 'toolbar' }, [
        UI.el('p', { class: 'muted', text: 'Automatic daily & weekly backups run at login. Create manual snapshots anytime.' }),
        UI.el('span', { class: 'spacer' }),
        UI.el('button', { class: 'btn btn-primary', text: '💾 Create Backup', onClick: async () => { await API.post('/api/backup/create'); UI.toast('Backup created', 'success'); draw(); } })]));
      body.appendChild(UI.table([
        { key: 'created_at', label: t('common.date') }, { key: 'filename', label: 'File' },
        { key: 'kind', label: 'Type', render: r => UI.badge(r.kind, 'gray') },
        { key: 'size_bytes', label: 'Size', num: true, render: r => (r.size_bytes / 1024).toFixed(0) + ' KB' },
        { key: 'verified', label: 'Verified', render: r => UI.badge(r.verified ? '✓' : '?', r.verified ? 'green' : 'orange') },
        { key: 'act', label: '', num: true, render: r => UI.el('div', { class: 'flex', style: 'justify-content:flex-end' }, [
          iconAction('⬇', 'Download', () => API.download('/api/backup/download/' + r.id, r.filename)),
          iconAction('✓', 'Verify', async () => { const v = await API.post('/api/backup/verify/' + r.id); UI.toast(v.ok ? 'Verified OK' : 'Verification failed', v.ok ? 'success' : 'error'); draw(); }),
          can('*') ? iconAction('♻️', 'Restore', () => UI.confirm('Restore this backup? Current data will be snapshotted first, then replaced. Restart required.', async () => { const res = await API.post('/api/backup/restore/' + r.id); UI.toast(res.note, 'success'); })) : null]) },
      ], d.backups, { empty: 'No backups yet' }));
    }
  },
};

KAKA_VIEWS.settings = {
  title: () => t('nav.settings'),
  async render(root) {
    UI.clear(root);
    const d = await API.get('/api/settings');
    const s = d.settings;
    const form = UI.form([
      { name: 'store_name', label: 'Store Name' }, { name: 'store_phone', label: 'Phone' },
      { name: 'store_address', label: 'Address', full: true },
      { name: 'currency', label: 'Currency' },
      { name: 'tax_rate', label: 'Default Tax %', type: 'number', step: '0.01' },
      { name: 'zakat_rate', label: 'Zakat Rate %', type: 'number', step: '0.01' },
      { name: 'receipt_width', label: 'Receipt Width (mm)', type: 'select', options: [{ value: '58', label: '58 mm' }, { value: '80', label: '80 mm' }] },
      { name: 'receipt_footer', label: 'Receipt Footer', full: true },
      { name: 'auto_backup', label: 'Auto Backup', type: 'select', options: [{ value: '1', label: 'Enabled' }, { value: '0', label: 'Disabled' }] },
    ], s);
    const logoInput = UI.el('input', { type: 'file', accept: 'image/*' });
    root.appendChild(UI.el('div', { class: 'card', style: 'max-width:760px' }, [
      UI.el('h3', { class: 'mb', text: 'Store Settings' }),
      form.node,
      UI.el('div', { class: 'field mt' }, [UI.el('label', { text: 'Store Logo' }),
        s.store_logo ? UI.el('img', { src: s.store_logo, style: 'max-height:60px;margin-bottom:8px' }) : null, logoInput]),
      UI.el('button', { class: 'btn btn-primary mt', text: t('common.save'), onClick: async () => {
        if (logoInput.files[0]) { const fd = new FormData(); fd.append('logo', logoInput.files[0]); await API.postForm('/api/settings/logo', fd); }
        await API.put('/api/settings', form.values());
        Object.assign(KAKA_STATE.settings, form.values());
        UI.toast('Settings saved', 'success'); } })]));
  },
};

KAKA_VIEWS.history = {
  title: () => 'Sales History',
  async render(root) {
    UI.clear(root);
    const search = UI.el('input', { class: 'grow', placeholder: 'Search receipt number...' });
    const from = UI.el('input', { type: 'date' }); const to = UI.el('input', { type: 'date' });
    const holder = UI.el('div', {});
    root.appendChild(UI.el('div', { class: 'toolbar' }, [search, UI.el('label', { text: 'From' }), from, UI.el('label', { text: 'To' }), to,
      UI.el('button', { class: 'btn btn-primary btn-sm', text: '↻', onClick: load })]));
    root.appendChild(holder);
    let timer; search.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(load, 250); });
    load();
    async function load() {
      const p = new URLSearchParams({ q: search.value.trim() });
      if (from.value) p.set('date_from', from.value); if (to.value) p.set('date_to', to.value);
      const d = await API.get('/api/sales?' + p);
      UI.clear(holder);
      holder.appendChild(UI.table([
        { key: 'receipt_no', label: 'Receipt', render: r => `<strong>${UI.esc(r.receipt_no)}</strong>` },
        { key: 'created_at', label: 'Date' }, { key: 'cashier', label: 'Cashier' },
        { key: 'customer_name', label: 'Customer', render: r => r.customer_name || '—' },
        { key: 'total', label: 'Total', num: true, render: r => money(r.total) },
        { key: 'payment_method', label: 'Payment', render: r => UI.badge(r.payment_method, 'blue') },
        { key: 'status', label: 'Status', render: r => UI.badge(r.status, r.status === 'completed' ? 'green' : (r.status === 'refunded' ? 'red' : 'orange')) },
        { key: 'act', label: '', num: true, render: r => UI.el('div', { class: 'flex', style: 'justify-content:flex-end' }, [
          iconAction('🖨', 'Reprint', () => printReceipt(r.id)),
          can('refund') && r.status === 'completed' ? iconAction('↩️', 'Refund', () => refundModal(r)) : null]) },
      ], d.sales, { empty: 'No sales' }));
    }
    async function refundModal(r) {
      const d = await API.get('/api/sales/' + r.id);
      const inputs = {};
      const rows = d.sale.items.map(it => { const max = it.quantity - it.refunded_qty;
        const i = UI.el('input', { type: 'number', step: 'any', value: max, style: 'width:80px' }); inputs[it.id] = { i, max }; return { it, i, max }; });
      UI.modal('Refund · ' + r.receipt_no, UI.table([
        { key: 'name', label: 'Product', render: x => x.it.name },
        { key: 'q', label: 'Sold', num: true, render: x => num(x.it.quantity) },
        { key: 'r', label: 'Refund Qty', num: true, render: x => x.i }], rows), [
        { label: t('common.cancel'), class: 'btn-ghost' },
        { label: 'Process Refund', class: 'btn-danger', onClick: async () => {
          const items = Object.entries(inputs).map(([id, o]) => ({ sale_item_id: +id, quantity: Math.min(parseFloat(o.i.value) || 0, o.max) })).filter(x => x.quantity > 0);
          const res = await API.post(`/api/sales/${r.id}/refund`, { items });
          UI.toast('Refunded ' + money(res.refunded), 'success'); load(); } }], { large: true });
    }
  },
};
