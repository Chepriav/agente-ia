import { t } from './i18n.js';

export function showPanels(documents) {
  document.getElementById('main-panels').style.display = 'grid';
  document.getElementById('chat-section').style.display = 'block';
  renderDocList(documents);
}

export function renderDocList(documents) {
  const list = document.getElementById('doc-list');
  if (!documents.length) {
    list.innerHTML = `<div class="empty-state">${t('docs_empty')}</div>`;
    return;
  }
  list.innerHTML = documents.map(doc => `
    <div class="doc-item">
      <div class="doc-icon">${doc.filename.endsWith('.pdf') ? '📄' : '📝'}</div>
      <div class="doc-name">${doc.filename}</div>
      <div class="doc-chunks">${doc.total_chunks} chunks</div>
    </div>
  `).join('');
}

export function addMessage(text, role, chunks) {
  const container = document.getElementById('chat-messages');
  const id = 'msg-' + Date.now();
  const meta = chunks ? `<div class="msg-meta">${chunks} fragmentos consultados</div>` : '';
  container.innerHTML += `
    <div class="msg ${role}" id="${id}">
      <div class="msg-bubble">${text}</div>
      ${meta}
    </div>
  `;
  container.scrollTop = container.scrollHeight;
  return id;
}

export function addTyping() {
  const container = document.getElementById('chat-messages');
  const id = 'typing-' + Date.now();
  container.innerHTML += `
    <div class="msg assistant" id="${id}">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  container.scrollTop = container.scrollHeight;
  return id;
}

export function removeTyping(id) {
  document.getElementById(id)?.remove();
}

export function showToast(msg, type) {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

export function setUploadProgress(visible) {
  document.getElementById('upload-progress').style.display = visible ? 'block' : 'none';
}
