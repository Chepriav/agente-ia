import { currentLang, t, setLang } from './i18n.js';
import { fetchDocuments, uploadDocument, queryKnowledgeBase } from './api.js';
import { showPanels, renderDocList, addMessage, addTyping, removeTyping, showToast, setUploadProgress } from './ui.js';

let currentOrg = null;

// --- Org loading ---

async function loadOrg() {
  const orgId = document.getElementById('org-input').value.trim();
  if (!orgId) return;

  currentOrg = orgId;

  try {
    const documents = await fetchDocuments(orgId);
    showPanels(documents);
    showToast(t('toast_loaded'), 'success');
  } catch {
    showToast(t('toast_org_error'), 'error');
  }
}

// --- File upload ---

async function uploadFile(file) {
  if (!file || !currentOrg) return;

  setUploadProgress(true);

  try {
    await uploadDocument(currentOrg, file);
    showToast(t('toast_uploaded'), 'success');
    const documents = await fetchDocuments(currentOrg);
    renderDocList(documents);
  } catch {
    showToast(t('toast_error'), 'error');
  } finally {
    setUploadProgress(false);
  }
}

// --- Chat ---

async function sendMessage() {
  const input = document.getElementById('question-input');
  const question = input.value.trim();
  if (!question || !currentOrg) return;

  addMessage(question, 'user');
  input.value = '';
  document.getElementById('send-btn').disabled = true;

  const typingId = addTyping();

  try {
    const data = await queryKnowledgeBase(currentOrg, question, currentLang);
    removeTyping(typingId);
    addMessage(data.answer, 'assistant', data.context_chunks_used);
  } catch {
    removeTyping(typingId);
    addMessage('Error al obtener respuesta.', 'assistant');
  }

  document.getElementById('send-btn').disabled = false;
  input.focus();
}

// --- Event listeners ---

document.addEventListener('DOMContentLoaded', () => {
  // Lang toggle
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => setLang(btn.textContent.toLowerCase()));
  });

  // Org input — Enter key
  document.getElementById('org-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') loadOrg();
  });

  // Load org button
  document.getElementById('load-org-btn').addEventListener('click', loadOrg);

  // File input change
  document.getElementById('file-input').addEventListener('change', e => {
    const file = e.target.files[0];
    if (file) uploadFile(file);
    e.target.value = '';
  });

  // Send button
  document.getElementById('send-btn').addEventListener('click', sendMessage);

  // Question input — Enter key
  document.getElementById('question-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') sendMessage();
  });

  // Drag and drop
  const uploadArea = document.getElementById('upload-area');
  uploadArea.addEventListener('dragover', e => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
  });
  uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
  });
  uploadArea.addEventListener('drop', e => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  });
});
