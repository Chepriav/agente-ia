/**
 * Fetches the list of indexed documents for an organization.
 * @returns {Promise<Array>} Array of document objects, or throws on error.
 */
export async function fetchDocuments(orgId) {
  const res = await fetch(`/org/${orgId}/documents`);
  if (res.status === 404) return [];
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.documents || [];
}

/**
 * Uploads a document file to an organization.
 * @returns {Promise<Object>} Response data, or throws on error.
 */
export async function uploadDocument(orgId, file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`/org/${orgId}/upload`, { method: 'POST', body: formData });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

/**
 * Sends a question to the knowledge base.
 * @returns {Promise<{answer: string, context_chunks_used: number}>}
 */
export async function queryKnowledgeBase(orgId, question, lang) {
  const res = await fetch(`/org/${orgId}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, language: lang }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}
