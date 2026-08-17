const AUTH_KEY = 'psyos_auth';

const Auth = {
  save(data) {
    localStorage.setItem(AUTH_KEY, JSON.stringify(data));
  },

  load() {
    try {
      return JSON.parse(localStorage.getItem(AUTH_KEY) || 'null');
    } catch {
      return null;
    }
  },

  clear() {
    localStorage.removeItem(AUTH_KEY);
  },

  token() {
    return this.load()?.access_token || null;
  },

  role() {
    return this.load()?.role || null;
  },

  locale() {
    return localStorage.getItem('psyos_locale') || this.load()?.locale || 'uk';
  },

  setLocale(locale) {
    localStorage.setItem('psyos_locale', locale);
  },

  requireRole(role) {
    const current = this.load();
    if (!current?.access_token) {
      window.location.href = role === 'client' ? 'login.html' : 'login-psychologist.html';
      return null;
    }
    if (current.role !== role) {
      window.location.href = current.role === 'client' ? 'client-dashboard.html' : 'psychologist-dashboard.html';
      return null;
    }
    return current;
  },

  logout() {
    this.clear();
    window.location.href = 'index.html';
  },
};
