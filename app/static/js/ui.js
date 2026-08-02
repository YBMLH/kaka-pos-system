/* KAKA POS — UI helpers: DOM building, toasts, modals, tables, forms. */
const UI = {
  /* Minimal hyperscript-style element builder. */
  el(tag, attrs, children) {
    const node = document.createElement(tag);
    if (attrs) for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class') node.className = v;
      else if (k === 'html') node.innerHTML = v;
      else if (k === 'text') node.textContent = v;
      else if (k.startsWith('on') && typeof v === 'function')
        node.addEventListener(k.slice(2).toLowerCase(), v);
      else if (v === true) node.setAttribute(k, '');
      else if (v !== false && v != null) node.setAttribute(k, v);
    }
    if (children != null) (Array.isArray(children) ? children : [children]).forEach(c => {
      if (c == null || c === false) return;
      node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    });
    return node;
  },

  esc(s) { const d = document.createElement('div'); d.textContent = s == null ? '' : s;
    return d.innerHTML; },

  toast(msg, type) {
    const root = document.getElementById('toast-root');
    const el = UI.el('div', { class: 'toast ' + (type || ''), text: msg });
    root.appendChild(el);
    setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 3200);
  },

  /* Open a modal. content is a DOM node; buttons = [{label, class, onClick, keepOpen}]. */
  modal(title, content, buttons, opts) {
    opts = opts || {};
    const root = document.getElementById('modal-root');
    const overlay = UI.el('div', { class: 'modal-overlay' });
    const foot = UI.el('div', { class: 'modal-foot' });
    const close = () => overlay.remove();
    (buttons || [{ label: t('common.close'), class: 'btn-ghost' }]).forEach(b => {
      const btn = UI.el('button', { class: 'btn ' + (b.class || 'btn-ghost'), text: b.label });
      btn.addEventListener('click', async () => {
        if (b.onClick) { const r = await b.onClick(); if (r === false) return; }
        if (!b.keepOpen) close();
      });
      foot.appendChild(btn);
    });
    const box = UI.el('div', { class: 'modal ' + (opts.large ? 'modal-lg' : '') }, [
      UI.el('div', { class: 'modal-head' }, [
        UI.el('h3', { text: title }),
        UI.el('button', { class: 'modal-close', html: '&times;', onClick: close }),
      ]),
      UI.el('div', { class: 'modal-body' }, content),
      foot,
    ]);
    overlay.appendChild(box);
    overlay.addEventListener('click', e => { if (e.target === overlay && !opts.sticky) close(); });
    root.appendChild(overlay);
    return { close, overlay };
  },

  confirm(message, onYes) {
    UI.modal(t('common.confirm'), UI.el('p', { text: message }), [
      { label: t('common.cancel'), class: 'btn-ghost' },
      { label: t('common.yes'), class: 'btn-danger', onClick: onYes },
    ]);
  },

  /* Build a form from a field spec; returns {node, values()}. */
  form(fields, initial) {
    initial = initial || {};
    const grid = UI.el('div', { class: 'form-grid' });
    const inputs = {};
    fields.forEach(f => {
      if (f.hidden) return;
      const wrap = UI.el('div', { class: 'field' + (f.full ? ' full' : '') });
      wrap.appendChild(UI.el('label', { text: f.label }));
      let input;
      if (f.type === 'select') {
        input = UI.el('select');
        (f.options || []).forEach(o => input.appendChild(
          UI.el('option', { value: o.value }, o.label)));
        input.value = initial[f.name] != null ? initial[f.name] : (f.default || '');
      } else if (f.type === 'textarea') {
        input = UI.el('textarea', { rows: f.rows || 2 });
        input.value = initial[f.name] || '';
      } else {
        input = UI.el('input', { type: f.type || 'text' });
        input.value = initial[f.name] != null ? initial[f.name] : (f.default || '');
        if (f.step) input.step = f.step;
        if (f.placeholder) input.placeholder = f.placeholder;
      }
      inputs[f.name] = input;
      wrap.appendChild(input);
      grid.appendChild(wrap);
    });
    return {
      node: grid,
      values() {
        const out = {};
        fields.forEach(f => {
          if (!inputs[f.name]) return;
          let v = inputs[f.name].value;
          if (f.type === 'number') v = v === '' ? 0 : parseFloat(v);
          out[f.name] = v;
        });
        return out;
      },
      inputs,
    };
  },

  table(columns, rows, opts) {
    opts = opts || {};
    const thead = UI.el('tr', {}, columns.map(c =>
      UI.el('th', { class: c.num ? 'num' : '' }, c.label)));
    const tbody = UI.el('tbody');
    if (!rows.length) {
      tbody.appendChild(UI.el('tr', {}, UI.el('td', {
        colspan: columns.length, class: 'empty' }, opts.empty || 'No records')));
    }
    rows.forEach(r => {
      const tr = UI.el('tr');
      columns.forEach(c => {
        const td = UI.el('td', { class: c.num ? 'num' : '' });
        const val = c.render ? c.render(r) : r[c.key];
        if (val instanceof Node) td.appendChild(val);
        else td.innerHTML = val == null ? '' : val;
        tr.appendChild(td);
      });
      if (opts.onRow) tr.addEventListener('click', () => opts.onRow(r));
      tbody.appendChild(tr);
    });
    return UI.el('div', { class: 'table-wrap' },
      UI.el('table', {}, [UI.el('thead', {}, thead), tbody]));
  },

  badge(text, color) { return `<span class="badge badge-${color}">${UI.esc(text)}</span>`; },

  /* Pure-CSS bar chart from [{label, value, value2?}]. */
  barChart(data, opts) {
    opts = opts || {};
    const max = Math.max(1, ...data.map(d => Math.max(d.value, d.value2 || 0)));
    const bars = data.map(d => {
      const b1 = UI.el('div', { class: 'chart-bar', title: `${d.label}: ${money(d.value)}`,
        style: `height:${(d.value / max) * 100}%` });
      const kids = [b1];
      if (d.value2 != null) kids.unshift(UI.el('div', { class: 'chart-bar profit',
        title: `${money(d.value2)}`, style: `height:${(d.value2 / max) * 100}%` }));
      return UI.el('div', { class: 'chart-bar-wrap' },
        [UI.el('div', { class: 'flex', style: 'align-items:flex-end;gap:2px;height:100%' }, kids),
         UI.el('div', { class: 'chart-label', text: d.label })]);
    });
    return UI.el('div', { class: 'chart' }, bars);
  },

  clear(node) { while (node.firstChild) node.removeChild(node.firstChild); },
};
window.UI = UI;
