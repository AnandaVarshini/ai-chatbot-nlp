// ============================================================
// AI Study Assistant - Shared Scripts
// ============================================================

const API_URL = 'http://127.0.0.1:8080';

// ============================================================
// Theme management (default: light)
// ============================================================
function initTheme() {
  const saved = localStorage.getItem('theme');
  const htmlTheme = document.documentElement.getAttribute('data-theme');
  const theme = saved || htmlTheme || 'light';
  document.documentElement.setAttribute('data-theme', theme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  updateThemeToggleIcon();
}

function updateThemeToggleIcon() {
  const theme = document.documentElement.getAttribute('data-theme') || 'light';
  const moon = document.getElementById('themeIconMoon');
  const sun = document.getElementById('themeIconSun');
  const label = document.getElementById('themeLabel');
  if (!moon || !sun) return;

  if (theme === 'dark') {
    moon.style.display = 'block';
    sun.style.display = 'none';
    if (label) label.textContent = 'Dark mode';
  } else {
    moon.style.display = 'none';
    sun.style.display = 'block';
    if (label) label.textContent = 'Light mode';
  }
}

initTheme();

// ============================================================
// Session management
// ============================================================
let currentSessionId = null;

function getUserId() { return localStorage.getItem('userId'); }
function getToken() { return localStorage.getItem('token'); }

async function createNewSession() {
  try {
    const res = await fetch(`${API_URL}/api/sessions/new`, { method: 'POST' });
    const data = await res.json();
    currentSessionId = data.session_id;
  } catch (err) {
    console.error('Session creation failed:', err);
    currentSessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).slice(2, 10);
  }
  localStorage.setItem('currentSessionId', currentSessionId);
  return currentSessionId;
}

async function loadSessions() {
  const userId = getUserId();
  if (!userId) return;

  const list = document.getElementById('sessionsList');
  if (!list) return;

  try {
    const res = await fetch(`${API_URL}/api/sessions/${userId}`);
    if (!res.ok) throw new Error('Failed to load sessions');
    const sessions = await res.json();
    renderSessions(sessions);
  } catch (err) {
    console.error('Load sessions failed:', err);
  }
}

function renderSessions(sessions) {
  const list = document.getElementById('sessionsList');
  if (!list) return;

  if (!sessions.length) {
    list.innerHTML = '<div class="sessions-empty">No conversations yet</div>';
    return;
  }

  list.innerHTML = '';
  sessions.forEach((session) => {
    const item = document.createElement('div');
    item.className = 'session-item';
    if (session.session_id === currentSessionId) item.classList.add('active');
    item.dataset.sessionId = session.session_id;

    const title = document.createElement('span');
    title.className = 'session-title';
    title.textContent = session.title || 'Untitled';
    title.title = session.title || '';

    const del = document.createElement('button');
    del.className = 'session-delete';
    del.type = 'button';
    del.setAttribute('aria-label', 'Delete conversation');
    del.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>';

    item.addEventListener('click', (e) => {
      if (e.target.closest('.session-delete')) return;
      switchSession(session.session_id);
    });

    del.addEventListener('click', (e) => {
      e.stopPropagation();
      if (confirm('Delete this conversation?')) deleteSession(session.session_id);
    });

    item.appendChild(title);
    item.appendChild(del);
    list.appendChild(item);
  });
}

async function switchSession(sessionId) {
  const userId = getUserId();
  if (!userId) return;

  currentSessionId = sessionId;
  localStorage.setItem('currentSessionId', sessionId);

  const chatBody = document.getElementById('chatBody');
  if (chatBody) chatBody.innerHTML = '';

  try {
    const res = await fetch(`${API_URL}/api/sessions/${userId}/${sessionId}`);
    const messages = await res.json();

    messages.forEach((msg) => {
      appendUserMessage(msg.query);
      appendBotMessage(msg.response, msg.intent);
    });

    loadSessions();
  } catch (err) {
    console.error('Load session messages failed:', err);
  }
}

async function deleteSession(sessionId) {
  const userId = getUserId();
  if (!userId) return;

  try {
    await fetch(`${API_URL}/api/sessions/${userId}/${sessionId}`, { method: 'DELETE' });

    if (sessionId === currentSessionId) {
      await createNewSession();
      const chatBody = document.getElementById('chatBody');
      if (chatBody) chatBody.innerHTML = '';
      showWelcomeMessage();
    }

    loadSessions();
  } catch (err) {
    console.error('Delete session failed:', err);
  }
}

// ============================================================
// Rendering helpers
// ============================================================
function formatTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[c]));
}

function linkify(html) {
  const urlRegex = /(https?:\/\/[^\s<]+)/g;
  return html.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener">$1</a>');
}

const BOT_AVATAR_SVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/></svg>';
const USER_AVATAR_SVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>';

function appendUserMessage(text) {
  const chatBody = document.getElementById('chatBody');
  if (!chatBody) return;

  const msg = document.createElement('div');
  msg.className = 'message user';
  msg.innerHTML = `
    <div class="message-avatar">${USER_AVATAR_SVG}</div>
    <div class="message-content">
      <div class="message-header">
        <span class="message-sender">You</span>
        <span class="message-time">${formatTime()}</span>
      </div>
      <div class="message-text">${escapeHtml(text).replace(/\n/g, '<br>')}</div>
    </div>
  `;
  chatBody.appendChild(msg);
  chatBody.scrollTop = chatBody.scrollHeight;
}

function appendBotMessage(text, intent) {
  const chatBody = document.getElementById('chatBody');
  if (!chatBody) return;

  const msg = document.createElement('div');
  msg.className = 'message bot';
  msg.innerHTML = `
    <div class="message-avatar">${BOT_AVATAR_SVG}</div>
    <div class="message-content">
      <div class="message-header">
        <span class="message-sender">Assistant</span>
        <span class="message-time">${formatTime()}</span>
      </div>
      <div class="message-text">${linkify(escapeHtml(text).replace(/\n/g, '<br>'))}</div>
    </div>
  `;
  chatBody.appendChild(msg);
  chatBody.scrollTop = chatBody.scrollHeight;
}

function showTyping() {
  const chatBody = document.getElementById('chatBody');
  if (!chatBody) return;

  const msg = document.createElement('div');
  msg.className = 'message bot';
  msg.id = 'typingIndicator';
  msg.innerHTML = `
    <div class="message-avatar">${BOT_AVATAR_SVG}</div>
    <div class="message-content">
      <div class="typing-indicator"><span></span><span></span><span></span></div>
    </div>
  `;
  chatBody.appendChild(msg);
  chatBody.scrollTop = chatBody.scrollHeight;
}

function removeTyping() {
  const t = document.getElementById('typingIndicator');
  if (t) t.remove();
}

function showWelcomeMessage() {
  const chatBody = document.getElementById('chatBody');
  if (!chatBody) return;

  const msg = document.createElement('div');
  msg.className = 'message bot';
  msg.innerHTML = `
    <div class="message-avatar">${BOT_AVATAR_SVG}</div>
    <div class="message-content">
      <div class="message-header">
        <span class="message-sender">Assistant</span>
        <span class="message-time">Just now</span>
      </div>
      <div class="message-text">Hello. I am your AI Study Assistant.<br><br>I can help with:<br>- Definitions: ask "What is [topic]?"<br>- Examples: ask "Give an example of [topic]?"<br>- Real-world examples: ask "Give a real-world example of [topic]?"<br>- Images: ask "Show images of [topic]?"<br>- Resources: ask "Where can I learn more about [topic]?"<br><br>Try asking about AI, machine learning, NLP, Python, or databases.</div>
    </div>
  `;
  chatBody.appendChild(msg);
}

// ============================================================
// Send message
// ============================================================
async function sendQuery() {
  const input = document.getElementById('queryInput');
  if (!input) return;

  const query = input.value.trim();
  if (!query) return;

  if (!currentSessionId) await createNewSession();

  appendUserMessage(query);
  input.value = '';
  showTyping();

  try {
    const userId = getUserId();
    const token = getToken();
    let url = `${API_URL}/api/chat`;
    if (userId && token) url = `${API_URL}/api/chat/${userId}`;

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      body: JSON.stringify({ query: query, session_id: currentSessionId })
    });

    if (!res.ok) throw new Error('Server error');

    const data = await res.json();
    removeTyping();
    appendBotMessage(data.response || 'No response received.', data.intent);
    loadSessions();
  } catch (err) {
    removeTyping();
    appendBotMessage('Connection failed. Please check your internet or try again.', 'Error');
  }
}

function handleKeyPress(event) {
  if (event.key === 'Enter') {
    event.preventDefault();
    sendQuery();
  }
}

function quickQuestion(text) {
  const input = document.getElementById('queryInput');
  if (!input) return;
  input.value = text;
  sendQuery();
}

// ============================================================
// Sidebar actions
// ============================================================
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;

  if (window.innerWidth <= 768) {
    sidebar.classList.toggle('mobile-open');
  } else {
    sidebar.classList.toggle('collapsed');
  }
}

async function handleNewChat() {
  await createNewSession();

  const chatBody = document.getElementById('chatBody');
  if (chatBody) chatBody.innerHTML = '';

  showWelcomeMessage();
  loadSessions();
}

function logout() {
  if (!confirm('Are you sure you want to logout?')) return;
  localStorage.clear();
  window.location.href = 'login.html';
}

// ============================================================
// Page initialization (chat page)
// ============================================================
async function initChatPage() {
  const token = getToken();
  const username = localStorage.getItem('username');
  const userId = getUserId();

  if (!token) {
    window.location.href = 'login.html';
    return;
  }

  const usernameEl = document.getElementById('navUsername');
  if (usernameEl) usernameEl.textContent = username || 'User';

  updateThemeToggleIcon();

  currentSessionId = localStorage.getItem('currentSessionId');
  if (!currentSessionId) {
    await createNewSession();
  }

  await loadSessions();

  if (currentSessionId && userId) {
    try {
      const res = await fetch(`${API_URL}/api/sessions/${userId}/${currentSessionId}`);
      if (res.ok) {
        const messages = await res.json();
        const chatBody = document.getElementById('chatBody');
        if (chatBody) chatBody.innerHTML = '';

        if (messages.length === 0) {
          showWelcomeMessage();
        } else {
          messages.forEach((msg) => {
            appendUserMessage(msg.query);
            appendBotMessage(msg.response, msg.intent);
          });
        }
      } else {
        showWelcomeMessage();
      }
    } catch (err) {
      showWelcomeMessage();
    }
  } else {
    showWelcomeMessage();
  }

  const input = document.getElementById('queryInput');
  if (input) input.focus();
}

window.addEventListener('online', () => {
  const badge = document.getElementById('offlineBadge');
  if (badge) badge.classList.remove('active');
});

window.addEventListener('offline', () => {
  const badge = document.getElementById('offlineBadge');
  if (badge) badge.classList.add('active');
});