/* Point of Sale view — barcode scanning, search, cart, checkout, hold/resume. */
KAKA_VIEWS.pos = {
  title: () => t('nav.pos'),
  async render(root) {
    const state = { cart: [], discount: 0, customer_id: null };
    UI.clear(root);

    const searchInput = UI.el('input', { type: 'text',
      placeholder: t('pos.search_placeholder'), id: 'pos-search', autocomplete: 'off' });
    const suggest = UI.el('div', { class: 'pos-suggest', id: 'pos-suggest' });
    const grid = UI.el('div', { class: 'pos-grid', id: 'pos-grid' });

    const left = UI.el('div', { class: 'pos-left' }, [
      UI.el('div', { class: 'pos-search' }, [searchInput, suggest]),
      grid,
    ]);

    const cartItems = UI.el('div', { class: 'cart-items', id: 'cart-items' });
    const totalsBox = UI.el('div', { id: 'cart-totals' });
    const cart = UI.el('div', { class: 'cart' }, [
      UI.el('div', { class: 'cart-head' }, [
        UI.el('h3', { text: t('pos.cart') }),
        UI.el('button', { class: 'btn btn-sm btn-ghost', text: t('pos.hold'),
          onClick: holdSale }),
      ]),
      cartItems,
      UI.el('div', { class: 'cart-foot' }, [totalsBox]),
    ]);

    root.appendChild(UI.el('div', { class: 'pos-layout' }, [left, cart]));

    // Load popular products as quick tiles.
    loadTiles();
    renderCart();
    searchInput.focus();

    async function loadTiles() {
      const d = await API.get('/api/products?per_page=24&sort=created_at&order=desc');
      UI.clear(grid);
      d.products.forEach(p => {
        const tile = UI.el('div', { class: 'pos-tile', onClick: () => addToCart(p) }, [
          UI.el('div', { class: 'pt-name', text: p.name_en || p.name_ar }),
          UI.el('div', { class: 'pt-price', text: money(p.selling_price) }),
          UI.el('div', { class: 'pt-stock', text: `${t('prod.stock')}: ${num(p.quantity)}` }),
        ]);
        grid.appendChild(tile);
      });
    }

    // Debounced instant search + barcode auto-add on Enter.
    let timer, activeIdx = -1, currentResults = [];
    searchInput.addEventListener('input', () => {
      clearTimeout(timer);
      const q = searchInput.value.trim();
      if (!q) { suggest.classList.remove('open'); return; }
      timer = setTimeout(() => doSearch(q), 120);
    });
    searchInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        if (activeIdx >= 0 && currentResults[activeIdx]) { addToCart(currentResults[activeIdx]); resetSearch(); }
        else doSearch(searchInput.value.trim(), true);
      } else if (e.key === 'ArrowDown') { activeIdx = Math.min(activeIdx + 1, currentResults.length - 1); highlight(); }
      else if (e.key === 'ArrowUp') { activeIdx = Math.max(activeIdx - 1, 0); highlight(); }
      else if (e.key === 'Escape') resetSearch();
    });
    function highlight() {
      suggest.querySelectorAll('.pos-suggest-item').forEach((el, i) =>
        el.classList.toggle('active', i === activeIdx));
    }
    async function doSearch(q, autoAdd) {
      if (!q) return;
      const d = await API.get('/api/products/search?q=' + encodeURIComponent(q));
      currentResults = d.products; activeIdx = -1;
      if (d.exact_barcode && autoAdd !== false && d.products.length === 1) {
        addToCart(d.products[0]); resetSearch(); return;
      }
      UI.clear(suggest);
      if (!d.products.length) {
        suggest.appendChild(UI.el('div', { class: 'pos-suggest-item', text: 'No match' }));
      }
      d.products.forEach((p, i) => {
        const item = UI.el('div', { class: 'pos-suggest-item', onClick: () => { addToCart(p); resetSearch(); } }, [
          UI.el('div', {}, [
            UI.el('div', { style: 'font-weight:600', text: p.name_en || p.name_ar }),
            UI.el('div', { class: 'muted', style: 'font-size:12px', text: (p.barcode || '') + ' · ' + t('prod.stock') + ': ' + num(p.quantity) }),
          ]),
          UI.el('strong', { text: money(p.selling_price) }),
        ]);
        suggest.appendChild(item);
      });
      suggest.classList.add('open');
    }
    function resetSearch() { searchInput.value = ''; suggest.classList.remove('open');
      currentResults = []; activeIdx = -1; searchInput.focus(); }

    function addToCart(p) {
      if (p.quantity <= 0) { UI.toast('Out of stock: ' + (p.name_en || p.name_ar), 'error'); return; }
      const line = state.cart.find(l => l.product_id === p.id);
      if (line) {
        if (line.quantity + 1 > p.quantity) { UI.toast('Not enough stock', 'error'); return; }
        line.quantity += 1;
      } else {
        state.cart.push({ product_id: p.id, name: p.name_en || p.name_ar,
          unit_price: p.selling_price, purchase_price: p.purchase_price,
          tax_rate: p.tax_rate, quantity: 1, stock: p.quantity, discount: 0 });
      }
      renderCart();
    }

    function renderCart() {
      UI.clear(cartItems);
      if (!state.cart.length) {
        cartItems.appendChild(UI.el('div', { class: 'cart-empty', text: t('pos.empty_cart') }));
      }
      state.cart.forEach((l, idx) => {
        const lineTotal = l.unit_price * l.quantity - l.discount;
        cartItems.appendChild(UI.el('div', { class: 'cart-line' }, [
          UI.el('div', {}, [
            UI.el('div', { class: 'cl-name', text: l.name }),
            UI.el('div', { class: 'cl-controls' }, [
              UI.el('button', { class: 'qty-btn', text: '−', onClick: () => changeQty(idx, -1) }),
              qtyInput(l, idx),
              UI.el('button', { class: 'qty-btn', text: '+', onClick: () => changeQty(idx, 1) }),
              can('edit_price') ? priceInput(l) : UI.el('span', { class: 'muted', style: 'font-size:12px', text: '× ' + money(l.unit_price) }),
            ]),
          ]),
          UI.el('div', {}, [
            UI.el('div', { class: 'cl-total', text: money(lineTotal) }),
            UI.el('div', { class: 'cl-remove right', html: '🗑', onClick: () => { state.cart.splice(idx, 1); renderCart(); } }),
          ]),
        ]));
      });
      renderTotals();
    }
    function qtyInput(l, idx) {
      const inp = UI.el('input', { class: 'cl-qty', type: 'number', value: l.quantity, step: 'any' });
      inp.addEventListener('change', () => {
        let v = parseFloat(inp.value) || 0;
        if (v > l.stock) { v = l.stock; UI.toast('Max stock: ' + l.stock, 'error'); }
        if (v <= 0) { state.cart.splice(idx, 1); } else l.quantity = v;
        renderCart();
      });
      return inp;
    }
    function priceInput(l) {
      const inp = UI.el('input', { class: 'cl-qty', type: 'number', value: l.unit_price, step: '0.01', title: 'Edit price' });
      inp.style.width = '70px';
      inp.addEventListener('change', () => { l.unit_price = parseFloat(inp.value) || 0; renderCart(); });
      return inp;
    }
    function changeQty(idx, delta) {
      const l = state.cart[idx];
      if (l.quantity + delta > l.stock) { UI.toast('Not enough stock', 'error'); return; }
      l.quantity += delta;
      if (l.quantity <= 0) state.cart.splice(idx, 1);
      renderCart();
    }

    function computeTotals() {
      let subtotal = 0, tax = 0, cost = 0;
      state.cart.forEach(l => {
        const gross = l.unit_price * l.quantity - l.discount;
        subtotal += gross; tax += gross * (l.tax_rate || 0) / 100; cost += l.purchase_price * l.quantity;
      });
      const total = subtotal - state.discount + tax;
      return { subtotal, tax, cost, total, profit: subtotal - state.discount - cost };
    }
    function renderTotals() {
      const tot = computeTotals();
      UI.clear(totalsBox);
      totalsBox.appendChild(UI.el('div', { class: 'cart-total-row' }, [
        UI.el('span', { text: t('pos.subtotal') }), UI.el('span', { text: money(tot.subtotal) })]));
      const discField = UI.el('input', { type: 'number', value: state.discount, step: '0.01', style: 'width:90px;text-align:end' });
      discField.addEventListener('change', () => { state.discount = parseFloat(discField.value) || 0; renderTotals(); });
      totalsBox.appendChild(UI.el('div', { class: 'cart-total-row' }, [
        UI.el('span', { text: t('pos.discount') }), can('discount') ? discField : UI.el('span', { text: money(state.discount) })]));
      totalsBox.appendChild(UI.el('div', { class: 'cart-total-row' }, [
        UI.el('span', { text: t('pos.tax') }), UI.el('span', { text: money(tot.tax) })]));
      totalsBox.appendChild(UI.el('div', { class: 'cart-total-row grand' }, [
        UI.el('span', { text: t('common.total') }), UI.el('span', { text: money(tot.total) })]));
      totalsBox.appendChild(UI.el('div', { class: 'cart-actions' }, [
        UI.el('button', { class: 'btn btn-ghost', text: t('pos.clear'),
          onClick: () => { if (state.cart.length) UI.confirm('Clear the cart?', () => { state.cart = []; state.discount = 0; renderCart(); }); } }),
        UI.el('button', { class: 'btn btn-success btn-lg', text: t('pos.pay') + ' · ' + money(tot.total),
          onClick: () => openPayment(tot) }),
      ]));
    }

    async function holdSale() {
      if (!state.cart.length) return;
      await API.post('/api/sales/hold', { label: 'Sale ' + new Date().toLocaleTimeString(),
        cart: { cart: state.cart, discount: state.discount, customer_id: state.customer_id } });
      state.cart = []; state.discount = 0; renderCart();
      UI.toast('Sale held', 'success');
    }

    function openPayment(tot) {
      if (!state.cart.length) { UI.toast(t('pos.empty_cart'), 'error'); return; }
      const paidInput = UI.el('input', { type: 'number', step: '0.01', value: tot.total.toFixed(2), style: 'font-size:20px' });
      const changeEl = UI.el('div', { class: 'stat-value', text: money(0) });
      const methodSel = UI.el('select', {}, [
        UI.el('option', { value: 'cash' }, 'Cash'), UI.el('option', { value: 'card' }, 'Card'),
        UI.el('option', { value: 'transfer' }, 'Bank Transfer'), UI.el('option', { value: 'credit' }, 'Credit (Customer)'),
      ]);
      paidInput.addEventListener('input', () => {
        const change = (parseFloat(paidInput.value) || 0) - tot.total;
        changeEl.textContent = money(Math.max(change, 0));
      });
      const body = UI.el('div', {}, [
        UI.el('div', { class: 'stat', style: 'text-align:center;margin-bottom:16px' }, [
          UI.el('div', { class: 'stat-label', text: t('common.total') }),
          UI.el('div', { class: 'stat-value', text: money(tot.total) })]),
        UI.el('div', { class: 'field' }, [UI.el('label', { text: 'Payment Method' }), methodSel]),
        UI.el('div', { class: 'field mt' }, [UI.el('label', { text: t('pos.paid') }), paidInput]),
        UI.el('div', { class: 'flex mt', style: 'justify-content:space-between' }, [
          UI.el('span', { class: 'muted', text: t('pos.change') }), changeEl]),
      ]);
      UI.modal(t('pos.pay'), body, [
        { label: t('common.cancel'), class: 'btn-ghost' },
        { label: t('pos.pay'), class: 'btn-success', onClick: async () => {
          try {
            const res = await API.post('/api/sales/checkout', {
              items: state.cart, discount: state.discount, customer_id: state.customer_id,
              payment_method: methodSel.value, paid: parseFloat(paidInput.value) || 0,
            });
            UI.toast('Sale ' + res.receipt_no + ' completed · change ' + money(res.change_due), 'success');
            state.cart = []; state.discount = 0; renderCart(); loadTiles(); searchInput.focus();
            printReceipt(res.sale_id);
          } catch (err) { UI.toast(err.data ? (err.data.error + (err.data.product ? ': ' + err.data.product : '')) : err.message, 'error'); return false; }
        } },
      ]);
      setTimeout(() => paidInput.select(), 50);
    }
  },
};

function printReceipt(saleId) {
  const w = window.open('/api/sales/' + saleId + '/receipt.pdf', '_blank');
  if (!w) UI.toast('Allow pop-ups to print receipts', 'error');
}
