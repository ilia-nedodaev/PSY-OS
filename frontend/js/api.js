const API = {
  url(path) {
    return `${window.PSYOS_CONFIG.API_BASE}${window.PSYOS_CONFIG.API_PREFIX}${path}`;
  },

  async request(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    const token = Auth.token();
    if (token) headers.Authorization = `Bearer ${token}`;
    headers['X-Locale'] = Auth.locale();
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }

    const res = await fetch(this.url(path), { ...options, headers });
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = { detail: text };
    }

    if (!res.ok) {
      const err = new Error(data?.detail || 'Request failed');
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  },

  get(path) {
    return this.request(path);
  },

  post(path, body) {
    return this.request(path, { method: 'POST', body: JSON.stringify(body) });
  },

  patch(path, body) {
    return this.request(path, { method: 'PATCH', body: JSON.stringify(body) });
  },

  upload(path, formData) {
    return this.request(path, { method: 'POST', body: formData });
  },

  registerPsychologist(payload) {
    return this.post('/auth/psychologist/register', payload);
  },

  loginPsychologist(email, password) {
    return this.post('/auth/psychologist/login', { email, password });
  },

  loginClient(username, password) {
    return this.post('/auth/client/login', { username, password });
  },

  me() {
    return this.get('/auth/me');
  },

  listClients() {
    return this.get('/clients');
  },

  createClient(payload) {
    return this.post('/clients', payload);
  },

  listSessions(clientId) {
    const q = clientId ? `?client_id=${clientId}` : '';
    return Auth.role() === 'client' ? this.get('/sessions/my') : this.get(`/sessions${q}`);
  },

  createSession(payload) {
    return this.post('/sessions', payload);
  },

  createNoteText(payload) {
    return this.post('/notes/text', payload);
  },

  listNotes(clientId) {
    return this.get(`/notes/client/${clientId}`);
  },

  listMessages(clientId) {
    return this.get(`/messages/${clientId}`);
  },

  sendMessage(clientId, body) {
    return this.post(`/messages/${clientId}`, { body });
  },

  listHomework(clientId) {
    return this.get(`/homework/client/${clientId}`);
  },

  createHomework(payload) {
    return this.post('/homework', payload);
  },

  completeHomework(id) {
    return this.patch(`/homework/${id}/complete`, {});
  },

  triggerSos(message) {
    return this.post('/sos', { message });
  },

  listSos() {
    return this.get('/sos');
  },

  markSosViewed(id) {
    return this.patch(`/sos/${id}/viewed`, {});
  },

  paymentStub(amountCents, sessionId) {
    return this.post('/payments/stub', { amount_cents: amountCents, session_id: sessionId || null });
  },

  listTimeline(clientId) {
    return this.get(`/timeline/client/${clientId}`);
  },

  createTimelineEvent(payload) {
    return this.post('/timeline', payload);
  },

  health() {
    return this.get('/health');
  },
};
