/* Products view — CRUD, search/filter/sort, import/export, archive, history, labels. */
KAKA_VIEWS.products = {
  title: () => t('nav.products'),
  async render(root) {
    const state = { page: 1, q: '', category_id: '', archived: '0', low_stock: '',
      sort: 'name_en', order: 'asc', cats: [], brands: [], suppliers: [] };
    UI.clear(root);

    [state.cats, state.brands, state.suppliers] = await Promise.all([
      API.get('/api/catalog/categories').then(d => d.categories),
      API.get('/api/catalog/brands').then(d => d.brands),
      API.get('/api/suppliers').then(d => d.suppliers),
    ]);

    const search = UI.el('input', { class: 'grow', placeholder: t('common.search') + ' (name / barcode / SKU)' });
    const catFilter = UI.el('select', {}, [UI.el('option', { value: '' }, t('common.all') + ' ' + t('prod.category'))]
      .concat(state.cats.map(c => UI.el('option', { value: c.id }, c.name))));
    const archFilter = UI.el('select', {}, [
      UI.el('option', { value: '0' }, 'Active'), UI.el('option', { value: '1' }, 'Archived')]);

    const toolbar = UI.el('div', { class: 'toolbar' }, [
      search, catFilter, archFilter,
      UI.el('button', { class: 'btn btn-ghost btn-sm', text: '⚠ Low stock',
        onClick: () => { state.low_stock = state.low_stock ? '' : '1'; load(); } }),
      UI.el('span', { class: 'spacer' }),
      can('products.edit') ? UI.el('button', { class: 'btn btn-ghost btn-sm', text: '🏷 Categories', onClick: manageCategories }) : null,
      can('products.edit') ? UI.el('button', { class: 'btn btn-ghost btn-sm', text: '⬇ Export', onClick: () => API.download('/api/products/export', 'products.xlsx') }) : null,
      can('products.edit') ? UI.el('button', { class: 'btn btn-ghost btn-sm', text: '⬆ Import', onClick: importModal }) : null,
      can('products.edit') ? UI.el('button', { class: 'btn btn-primary', text: '+ ' + t('common.add'), onClick: () => editModal(null) }) : null,
    ]);
    root.appendChild(toolbar);
    const listHolder = UI.el('div', {});
    root.appendChild(listHolder);

    let timer;
    search.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(() => { state.q = search.value.trim(); state.page = 1; load(); }, 200); });
    catFilter.addEventListener('change', () => { state.category_id = catFilter.value; state.page = 1; load(); });
    archFilter.addEventListener('change', () => { state.archived = archFilter.value; state.page = 1; load(); });

    load();
    async function load() {
      const qs = new URLSearchParams({ page: state.page, per_page: 50, q: state.q,
        category_id: state.category_id, archived: state.archived, low_stock: state.low_stock,
        sort: state.sort, order: state.order });
      const d = await API.get('/api/products?' + qs);
      UI.clear(listHolder);
      listHolder.appendChild(UI.table([
        { key: 'name', label: t('common.name'), render: r => `<strong>${UI.esc(r.name_en || r.name_ar)}</strong><br><span class="muted" style="font-size:12px">${UI.esc(r.barcode || '')}${r.sku ? ' · ' + UI.esc(r.sku) : ''}</span>` },
        { key: 'category_name', label: t('prod.category'), render: r => r.category_name || '—' },
        { key: 'purchase_price', label: t('prod.cost'), num: true, render: r => money(r.purchase_price) },
        { key: 'selling_price', label: t('prod.price'), num: true, render: r => money(r.selling_price) },
        { key: 'profit_margin', label: 'Margin', num: true, render: r => `${r.profit_margin}%` },
        { key: 'quantity', label: t('prod.stock'), num: true, render: r =>
          `<span class="${r.low_stock ? 'down' : ''}">${num(r.quantity)} ${UI.esc(r.unit)}</span>` },
        { key: 'actions', label: '', num: true, render: r => actionMenu(r) },
      ], d.products, { empty: 'No products' }));
      listHolder.appendChild(pager(d, p => { state.page = p; load(); }));
    }

    function actionMenu(r) {
      const wrap = UI.el('div', { class: 'flex', style: 'justify-content:flex-end' });
      if (can('products.edit')) {
        wrap.appendChild(iconAction('✏️', 'Edit', () => editModal(r)));
        wrap.appendChild(iconAction('📋', 'Duplicate', async () => { await API.post(`/api/products/${r.id}/duplicate`); UI.toast('Duplicated', 'success'); load(); }));
        wrap.appendChild(iconAction('🏷', 'Label', () => API.download(`/api/barcode/label/${r.id}?count=1`, 'label.pdf')));
        wrap.appendChild(iconAction('📜', 'History', () => historyModal(r)));
        if (r.is_archived) wrap.appendChild(iconAction('♻️', 'Restore', async () => { await API.post(`/api/products/${r.id}/restore`); load(); }));
        else wrap.appendChild(iconAction('🗑', 'Archive/Delete', () => UI.confirm('Delete/archive "' + (r.name_en || r.name_ar) + '"?', async () => { await API.del('/api/products/' + r.id); UI.toast('Removed', 'success'); load(); })));
      }
      return wrap;
    }

    function editModal(r) {
      const form = UI.form([
        { name: 'name_en', label: 'Name (English)' },
        { name: 'name_fr', label: 'Nom (Français)' },
        { name: 'name_ar', label: 'الاسم (العربية)' },
        { name: 'barcode', label: t('prod.barcode') },
        { name: 'sku', label: 'SKU' },
        { name: 'category_id', label: t('prod.category'), type: 'select',
          options: [{ value: '', label: '—' }].concat(state.cats.map(c => ({ value: c.id, label: c.name }))) },
        { name: 'brand_id', label: 'Brand', type: 'select',
          options: [{ value: '', label: '—' }].concat(state.brands.map(b => ({ value: b.id, label: b.name }))) },
        { name: 'supplier_id', label: 'Supplier', type: 'select',
          options: [{ value: '', label: '—' }].concat(state.suppliers.map(s => ({ value: s.id, label: s.company_name }))) },
        { name: 'purchase_price', label: t('prod.cost'), type: 'number', step: '0.01' },
        { name: 'selling_price', label: t('prod.price'), type: 'number', step: '0.01' },
        { name: 'tax_rate', label: 'Tax %', type: 'number', step: '0.01' },
        { name: 'quantity', label: 'Quantity', type: 'number', step: 'any' },
        { name: 'min_stock', label: 'Min Stock', type: 'number', step: 'any' },
        { name: 'unit', label: 'Unit', default: 'pcs' },
        { name: 'expiry_date', label: 'Expiry Date', type: 'date' },
        { name: 'batch_number', label: 'Batch Number' },
        { name: 'notes', label: 'Notes', type: 'textarea', full: true },
      ], r || {});
      UI.modal(r ? t('common.edit') : t('common.add'), form.node, [
        { label: t('common.cancel'), class: 'btn-ghost' },
        { label: t('common.save'), class: 'btn-primary', onClick: async () => {
          const v = form.values();
          try {
            if (r) await API.put('/api/products/' + r.id, v);
            else await API.post('/api/products', v);
            UI.toast(t('common.save'), 'success'); load();
          } catch (e) { UI.toast(e.message, 'error'); return false; }
        } },
      ], { large: true });
    }

    async function historyModal(r) {
      const d = await API.get(`/api/products/${r.id}/history`);
      UI.modal('History · ' + (r.name_en || r.name_ar), UI.table([
        { key: 'created_at', label: t('common.date') },
        { key: 'reason', label: 'Reason' },
        { key: 'change_qty', label: 'Change', num: true, render: x => (x.change_qty > 0 ? '+' : '') + num(x.change_qty, 2) },
        { key: 'balance', label: 'Balance', num: true, render: x => num(x.balance, 2) },
        { key: 'note', label: 'Note' },
      ], d.movements, { empty: 'No movements' }), null, { large: true });
    }

    function importModal() {
      const fileInput = UI.el('input', { type: 'file', accept: '.xlsx' });
      const body = UI.el('div', {}, [
        UI.el('p', { class: 'mb muted', text: 'Upload an Excel file. Download the template for the correct columns.' }),
        UI.el('button', { class: 'btn btn-ghost btn-sm mb', text: '⬇ Download Template',
          onClick: () => API.download('/api/products/import-template', 'template.xlsx') }),
        UI.el('div', { class: 'field' }, [UI.el('label', { text: 'Excel file' }), fileInput]),
      ]);
      UI.modal('Import Products', body, [
        { label: t('common.cancel'), class: 'btn-ghost' },
        { label: 'Import', class: 'btn-primary', onClick: async () => {
          if (!fileInput.files[0]) { UI.toast('Choose a file', 'error'); return false; }
          const fd = new FormData(); fd.append('file', fileInput.files[0]);
          try {
            const d = await API.postForm('/api/products/import', fd);
            UI.toast(`Imported: ${d.created} new, ${d.updated} updated, ${d.skipped} skipped`, 'success');
            load();
          } catch (e) { UI.toast(e.message, 'error'); return false; }
        } },
      ]);
    }

    async function manageCategories() {
      const d = await API.get('/api/catalog/categories');
      const list = UI.el('div', {});
      const refresh = async () => { const dd = await API.get('/api/catalog/categories'); state.cats = dd.categories; UI.clear(list); dd.categories.forEach(renderCat); };
      function renderCat(c) {
        list.appendChild(UI.el('div', { class: 'flex', style: 'justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border)' }, [
          UI.el('span', { text: `${c.name} (${c.product_count})` }),
          UI.el('button', { class: 'btn btn-sm btn-danger', text: '×', onClick: () => UI.confirm('Delete category?', async () => { await API.del('/api/catalog/categories/' + c.id); refresh(); }) }),
        ]));
      }
      d.categories.forEach(renderCat);
      const name = UI.el('input', { placeholder: 'New category name' });
      const body = UI.el('div', {}, [list, UI.el('div', { class: 'flex mt' }, [name,
        UI.el('button', { class: 'btn btn-primary', text: t('common.add'), onClick: async () => {
          if (!name.value.trim()) return; await API.post('/api/catalog/categories', { name: name.value.trim() }); name.value = ''; refresh(); } })])]);
      UI.modal('Categories', body);
    }
  },
};

/* Shared helpers used by several list views. */
function iconAction(icon, title, fn) {
  return UI.el('button', { class: 'icon-btn btn-sm', style: 'width:32px;height:32px;font-size:14px', title, html: icon, onClick: fn });
}
function pager(d, go) {
  if (!d.pages || d.pages <= 1) return UI.el('div');
  const wrap = UI.el('div', { class: 'flex mt', style: 'justify-content:center' });
  wrap.appendChild(UI.el('button', { class: 'btn btn-sm btn-ghost', text: '‹', onClick: () => d.page > 1 && go(d.page - 1) }));
  wrap.appendChild(UI.el('span', { style: 'padding:0 12px', text: `${d.page} / ${d.pages}` }));
  wrap.appendChild(UI.el('button', { class: 'btn btn-sm btn-ghost', text: '›', onClick: () => d.page < d.pages && go(d.page + 1) }));
  return wrap;
}
