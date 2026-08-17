document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireRole('psychologist')) return;

  let profile = null;
  let clients = [];
  let selectedClientId = null;

  const els = {
    userName: document.getElementById('userName'),
    clientsList: document.getElementById('clientsList'),
    clientSelect: document.getElementById('clientSelect'),
    sessionsList: document.getElementById('sessionsList'),
    notesList: document.getElementById('notesList'),
    homeworkList: document.getElementById('homeworkList'),
    sosList: document.getElementById('sosList'),
    timelineList: document.getElementById('timelineList'),
    chatMessages: document.getElementById('chatMessages'),
    chatInput: document.getElementById('chatInput'),
    aiStatus: document.getElementById('aiStatus'),
  };

  async function init() {
    profile = await API.me();
    els.userName.textContent = `${profile.first_name} ${profile.last_name}`;
    const health = await API.health();
    els.aiStatus.textContent = health.ai_enabled
      ? 'AI: увімкнено'
      : 'AI: вимкнено (готово до підключення API)';

    await loadClients();
    await loadSos();
    bindPanels();
    bindForms();
  }

  function bindPanels() {
    document.querySelectorAll('.sidebar-link').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.sidebar-link').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.dashboard-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(btn.dataset.panel).classList.add('active');
      });
    });
    document.getElementById('logoutBtn').addEventListener('click', () => Auth.logout());
  }

  async function loadClients() {
    clients = await API.listClients();
    els.clientsList.innerHTML = clients.length
      ? clients.map(c => `
        <div class="card">
          <h3>${c.first_name} ${c.last_name}</h3>
          <p>@${c.username}</p>
          <button class="btn btn-secondary btn-sm" data-open-client="${c.id}">Відкрити</button>
        </div>`).join('')
      : '<div class="empty-state">Ще немає клієнтів. Додайте першого.</div>';

    els.clientSelect.innerHTML = '<option value="">— Оберіть клієнта —</option>' +
      clients.map(c => `<option value="${c.id}">${c.first_name} ${c.last_name}</option>`).join('');

    els.clientsList.querySelectorAll('[data-open-client]').forEach(btn => {
      btn.addEventListener('click', () => selectClient(btn.dataset.openClient));
    });
  }

  async function selectClient(id) {
    selectedClientId = id;
    els.clientSelect.value = id;
    document.querySelector('[data-panel="panel-client"]').click();
    await refreshClientData();
  }

  els.clientSelect?.addEventListener('change', async (e) => {
    selectedClientId = e.target.value || null;
    if (selectedClientId) await refreshClientData();
  });

  async function refreshClientData() {
    if (!selectedClientId) return;
    const [sessions, notes, homework, timeline] = await Promise.all([
      API.listSessions(selectedClientId),
      API.listNotes(selectedClientId),
      API.listHomework(selectedClientId),
      API.listTimeline(selectedClientId),
    ]);

    els.sessionsList.innerHTML = sessions.length
      ? sessions.map(s => `<div class="card"><h3>${new Date(s.scheduled_at).toLocaleString('uk-UA')}</h3><p>Статус: ${s.status}</p></div>`).join('')
      : '<div class="empty-state">Сесій поки немає</div>';

    els.notesList.innerHTML = notes.length
      ? notes.map(n => `<div class="card"><p>${(n.content_text || n.transcript || '').slice(0, 200)}</p><div class="card-meta">${new Date(n.created_at).toLocaleString('uk-UA')}</div>${n.ai_summary ? `<div class="ai-placeholder">${n.ai_summary}</div>` : ''}</div>`).join('')
      : '<div class="empty-state">Нотаток поки немає</div>';

    els.homeworkList.innerHTML = homework.length
      ? homework.map(h => `<div class="card"><h3>${h.title}</h3><p>${h.description}</p><span class="badge badge-muted">${h.status}</span></div>`).join('')
      : '<div class="empty-state">Домашніх завдань немає</div>';

    els.timelineList.innerHTML = timeline.length
      ? timeline.map(ev => `<div class="card"><h3>${ev.emoji || '•'} ${ev.title}</h3><p>${new Date(ev.event_date).toLocaleDateString('uk-UA')}</p></div>`).join('')
      : '<div class="empty-state">Timeline порожній</div>';

    await loadChat();
  }

  async function loadChat() {
    if (!selectedClientId) return;
    const messages = await API.listMessages(selectedClientId);
    els.chatMessages.innerHTML = messages.map(m =>
      `<div class="chat-message ${m.sender_role}">${m.body}</div>`
    ).join('');
    els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
  }

  async function loadSos() {
    const items = await API.listSos();
    els.sosList.innerHTML = items.length
      ? items.map(s => `<div class="card"><span class="badge badge-warning">${s.status}</span><p>${s.message || 'SOS'}</p><button class="btn btn-sm btn-secondary" data-sos-id="${s.id}">Позначити переглянутим</button></div>`).join('')
      : '<div class="empty-state">SOS-повідомлень немає</div>';

    els.sosList.querySelectorAll('[data-sos-id]').forEach(btn => {
      btn.addEventListener('click', async () => {
        await API.markSosViewed(btn.dataset.sosId);
        await loadSos();
      });
    });
  }

  function bindForms() {
    document.getElementById('addClientForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const f = e.target;
      await API.createClient({
        username: f.username.value.trim(),
        password: f.password.value,
        first_name: f.first_name.value.trim(),
        last_name: f.last_name.value.trim(),
        phone: f.phone.value.trim() || null,
        locale: Auth.locale(),
      });
      f.reset();
      await loadClients();
    });

    document.getElementById('addSessionForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!selectedClientId) return alert('Оберіть клієнта');
      const f = e.target;
      await API.createSession({
        client_id: selectedClientId,
        scheduled_at: new Date(f.scheduled_at.value).toISOString(),
        duration_minutes: Number(f.duration_minutes.value),
      });
      f.reset();
      await refreshClientData();
    });

    document.getElementById('addNoteForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!selectedClientId) return alert('Оберіть клієнта');
      await API.createNoteText({
        client_id: selectedClientId,
        content_text: e.target.content_text.value.trim(),
      });
      e.target.reset();
      await refreshClientData();
    });

    document.getElementById('addHomeworkForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!selectedClientId) return alert('Оберіть клієнта');
      const f = e.target;
      await API.createHomework({
        client_id: selectedClientId,
        title: f.title.value.trim(),
        description: f.description.value.trim(),
        due_at: f.due_at.value ? new Date(f.due_at.value).toISOString() : null,
      });
      f.reset();
      await refreshClientData();
    });

    document.getElementById('addTimelineForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!selectedClientId) return alert('Оберіть клієнта');
      const f = e.target;
      await API.createTimelineEvent({
        client_id: selectedClientId,
        event_date: new Date(f.event_date.value).toISOString(),
        title: f.title.value.trim(),
        emoji: f.emoji.value.trim() || null,
      });
      f.reset();
      await refreshClientData();
    });

    document.getElementById('sendChatBtn').addEventListener('click', async () => {
      if (!selectedClientId || !els.chatInput.value.trim()) return;
      await API.sendMessage(selectedClientId, els.chatInput.value.trim());
      els.chatInput.value = '';
      await loadChat();
    });

    setInterval(async () => {
      if (selectedClientId) await loadChat();
      await loadSos();
    }, 10000);
  }

  init().catch(() => Auth.logout());
});
