/* KAKA POS — API client and shared application state. */
window.KAKA_STATE = {
  user: null,
  settings: {},
  lang: localStorage.getItem('kaka_lang') || 'en',
  theme: localStorage.getItem('kaka_theme') || 'light',
};

window.KAKA_VIEWS = {};

const API = {
  async request(method, url, body, isForm) {
    const opts = { method, headers: {} };
    if (body && !isForm) { opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body); }
    else if (isForm) { opts.body = body; }
    const res = await fetch(url, opts);
    if (res.status === 401) { window.location.href = '/login'; return; }
    const ct = res.headers.get('Content-Type') || '';
    if (ct.includes('application/json')) {
      const data = await res.json();
      if (!res.ok) throw Object.assign(new Error(data.error || 'Request failed'),
        { status: res.status, data });
      return data;
    }
    if (!res.ok) throw new Error('Request failed (' + res.status + ')');
    return res;
  },
  get(url) { return this.request('GET', url); },
  post(url, body) { return this.request('POST', url, body); },
  put(url, body) { return this.request('PUT', url, body); },
  del(url) { return this.request('DELETE', url); },
  postForm(url, form) { return this.request('POST', url, form, true); },

  /* Trigger a file download from an endpoint that returns a blob. */
  async download(url, filename) {
    const res = await fetch(url);
    if (!res.ok) { UI.toast(t('common.error') || 'Download failed', 'error'); return; }
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename || 'download';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  },
};
window.API = API;

/* Convenience: does the current user hold a permission? */
window.can = function (perm) {
  const u = KAKA_STATE.user;
  if (!u) return false;
  return u.permissions.includes('*') || u.permissions.includes(perm);
};

/* Currency formatting using the store's configured currency. */
window.money = function (n) {
  const cur = KAKA_STATE.settings.currency || 'MAD';
  const val = Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2,
    maximumFractionDigits: 2 });
  return val + ' ' + cur;
};
window.num = function (n, d) {
  return Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: d || 0,
    maximumFractionDigits: d || 0 });
};
