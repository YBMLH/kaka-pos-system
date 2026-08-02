/* KAKA POS — application bootstrap, navigation and routing. */
(function () {
  const NAV = [
    { id: 'dashboard', icon: '📊', perm: 'dashboard' },
    { id: 'pos', icon: '🛒', perm: 'pos', label: 'nav.pos' },
    { id: 'products', icon: '📦', perm: 'products.view' },
    { id: 'inventory', icon: '📋', perm: 'inventory' },
    { id: 'purchases', icon: '🚚', perm: 'purchases' },
    { id: 'suppliers', icon: '🏭', perm: 'suppliers' },
    { id: 'customers', icon: '👥', perm: 'customers' },
    { id: 'history', icon: '🧾', perm: 'pos', label: 'nav.history' },
    { id: 'expenses', icon: '💸', perm: 'expenses' },
    { id: 'reports', icon: '📈', perm: 'reports' },
    { id: 'register', icon: '💰', perm: 'register' },
    { id: 'zakat', icon: '🕌', perm: 'zakat' },
    { id: 'users', icon: '🔐', perm: '*' },
    { id: 'settings', icon: '⚙️', perm: 'settings' },
  ];
  const EXTRA_LABELS = { 'nav.history': { en: 'Sales History', fr: 'Historique', ar: 'سجل المبيعات' } };

  function navLabel(item) {
    const key = item.label || ('nav.' + item.id);
    return t(key) !== key ? t(key) : (item.id.charAt(0).toUpperCase() + item.id.slice(1));
  }

  async function boot() {
    const data = await API.get('/api/auth/me');
    if (!data || !data.user) { window.location.href = '/login'; return; }
    KAKA_STATE.user = data.user;
    KAKA_STATE.settings = (await API.get('/api/settings')).settings;
    KAKA_STATE.lang = data.user.language || KAKA_STATE.lang;
    KAKA_STATE.theme = data.user.theme || KAKA_STATE.theme;

    applyLang(KAKA_STATE.lang);
    applyTheme(KAKA_STATE.theme);
    renderUserChip();
    buildNav();
    wireTopbar();

    document.getElementById('app-loading').hidden = true;
    document.getElementById('app').hidden = false;

    window.addEventListener('hashchange', route);
    route();
  }

  function buildNav() {
    const nav = document.getElementById('nav');
    UI.clear(nav);
    NAV.filter(i => can(i.perm)).forEach(item => {
      const a = UI.el('a', { href: '#/' + item.id, 'data-view': item.id }, [
        UI.el('span', { class: 'nav-icon', text: item.icon }),
        UI.el('span', { text: navLabel(item) }),
      ]);
      nav.appendChild(a);
    });
  }

  function route() {
    let id = (location.hash || '#/dashboard').replace('#/', '') || 'dashboard';
    const item = NAV.find(i => i.id === id);
    if (!item || !can(item.perm) || !KAKA_VIEWS[id]) {
      id = can('dashboard') ? 'dashboard' : (NAV.find(i => can(i.perm)) || {}).id;
      if (!id) return;
    }
    document.querySelectorAll('#nav a').forEach(a =>
      a.classList.toggle('active', a.getAttribute('data-view') === id));
    document.getElementById('page-title').textContent =
      KAKA_VIEWS[id].title ? KAKA_VIEWS[id].title() : id;
    document.getElementById('sidebar').classList.remove('open');
    const view = document.getElementById('view');
    view.scrollTop = 0;
    KAKA_VIEWS[id].render(view).catch(err => {
      console.error(err);
      view.innerHTML = '<div class="empty">Error loading view: ' + UI.esc(err.message) + '</div>';
    });
  }

  function renderUserChip() {
    const u = KAKA_STATE.user;
    document.getElementById('user-name').textContent = u.full_name || u.username;
    document.getElementById('user-role').textContent = u.role_label;
    document.getElementById('user-avatar').textContent = (u.username[0] || 'U').toUpperCase();
  }

  function applyLang(lang) {
    KAKA_STATE.lang = lang;
    localStorage.setItem('kaka_lang', lang);
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    const sel = document.getElementById('lang-select');
    if (sel) sel.value = lang;
  }

  function applyTheme(theme) {
    KAKA_STATE.theme = theme;
    localStorage.setItem('kaka_theme', theme);
    document.body.setAttribute('data-theme', theme);
  }

  function wireTopbar() {
    document.getElementById('menu-toggle').addEventListener('click', () =>
      document.getElementById('sidebar').classList.toggle('open'));

    document.getElementById('theme-toggle').addEventListener('click', () => {
      const next = KAKA_STATE.theme === 'light' ? 'dark' : 'light';
      applyTheme(next);
      API.post('/api/auth/preferences', { theme: next }).catch(() => {});
    });

    document.getElementById('lang-select').addEventListener('change', e => {
      applyLang(e.target.value);
      API.post('/api/auth/preferences', { language: e.target.value }).catch(() => {});
      buildNav();
      route();
    });

    const menuBtn = document.getElementById('user-menu-btn');
    const menu = document.getElementById('user-menu');
    menuBtn.addEventListener('click', e => { e.stopPropagation(); menu.classList.toggle('open'); });
    document.addEventListener('click', () => menu.classList.remove('open'));
    menu.addEventListener('click', e => {
      const action = e.target.getAttribute('data-action');
      if (action === 'logout') logout();
      if (action === 'change-password') changePassword();
    });
  }

  function changePassword() {
    const form = UI.form([
      { name: 'current_password', label: 'Current Password', type: 'password', full: true },
      { name: 'new_password', label: 'New Password', type: 'password', full: true },
    ]);
    UI.modal(t('menu.change_password'), form.node, [
      { label: t('common.cancel'), class: 'btn-ghost' },
      { label: t('common.save'), class: 'btn-primary', onClick: async () => {
        try { await API.post('/api/auth/change-password', form.values());
          UI.toast('Password changed', 'success'); }
        catch (e) { UI.toast(e.message, 'error'); return false; } } },
    ]);
  }

  async function logout() {
    await API.post('/api/auth/logout');
    window.location.href = '/login';
  }

  document.addEventListener('DOMContentLoaded', boot);
})();
