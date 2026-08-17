document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireRole('client')) return;

  let profile = null;

  const els = {
    userName: document.getElementById('userName'),
    sessionsList: document.getElementById('sessionsList'),
    homeworkList: document.getElementById('homeworkList'),
    chatMessages: document.getElementById('chatMessages'),
    chatInput: document.getElementById('chatInput'),
  };

  async function init() {
    profile = await API.me();
    els.userName.textContent = `${profile.first_name} ${profile.last_name}`;

    bindPanels();
    await loadSessions();
    await loadHomework();
    await loadChat();

    document.getElementById('logoutBtn').addEventListener('click', () => Auth.logout());

    document.getElementById('sosBtn').addEventListener('click', async () => {
      const message = prompt('Коротко опишіть ситуацію (необов\'язково):') || null;
      await API.triggerSos(message);
      alert('SOS надіслано вашому психологу');
    });

    document.getElementById('payBtn').addEventListener('click', async () => {
      const res = await API.paymentStub(80000, null);
      alert('Демо-оплата створена. Статус: ' + res.status);
    });

    document.getElementById('sendChatBtn').addEventListener('click', sendChat);
    setInterval(loadChat, 10000);
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
  }

  async function loadSessions() {
    const sessions = await API.listSessions();
    els.sessionsList.innerHTML = sessions.length
      ? sessions.map(s => `<div class="card"><h3>${new Date(s.scheduled_at).toLocaleString('uk-UA')}</h3><p>Статус: ${s.status}</p></div>`).join('')
      : '<div class="empty-state">Записів поки немає</div>';
  }

  async function loadHomework() {
    const items = await API.listHomework(profile.id);
    els.homeworkList.innerHTML = items.length
      ? items.map(h => `
        <div class="card">
          <h3>${h.title}</h3>
          <p>${h.description}</p>
          <span class="badge badge-muted">${h.status}</span>
          ${h.status !== 'completed' ? `<button class="btn btn-sm btn-primary" data-hw="${h.id}">Виконано</button>` : ''}
        </div>`).join('')
      : '<div class="empty-state">Домашніх завдань немає</div>';

    els.homeworkList.querySelectorAll('[data-hw]').forEach(btn => {
      btn.addEventListener('click', async () => {
        await API.completeHomework(btn.dataset.hw);
        await loadHomework();
      });
    });
  }

  async function loadChat() {
    const messages = await API.listMessages(profile.id);
    els.chatMessages.innerHTML = messages.map(m =>
      `<div class="chat-message ${m.sender_role}">${m.body}</div>`
    ).join('');
    els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
  }

  async function sendChat() {
    if (!els.chatInput.value.trim()) return;
    await API.sendMessage(profile.id, els.chatInput.value.trim());
    els.chatInput.value = '';
    await loadChat();
  }

  init().catch(() => Auth.logout());
});
