const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';

async function request(path, { method = 'GET', body, headers = {} } = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      ...headers,
      ...(body && !(body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
    },
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : {};

  if (!response.ok) {
    throw new Error(data.error || 'Request failed');
  }

  return data;
}

export const api = {
  healthCheck: () => request('/api/health'),
  listSchemes: (query = '', category = '') => {
    const params = new URLSearchParams();
    if (query) params.set('query', query);
    if (category) params.set('category', category);
    return request(`/api/schemes${params.toString() ? `?${params.toString()}` : ''}`);
  },
  getScheme: (schemeId) => request(`/api/schemes/${schemeId}`),
  recommendSchemes: (profile) => request('/api/schemes/recommend', {
    method: 'POST',
    body: profile,
  }),
  askAssistant: (question, language = 'en') => request('/api/chat', {
    method: 'POST',
    body: { question, language },
  }),
  uploadPdf: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch(`${API_BASE}/api/pdf/upload`, {
      method: 'POST',
      body: formData,
    }).then(async (response) => {
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      if (!response.ok) {
        throw new Error(data.error || 'PDF upload failed');
      }
      return data;
    });
  },
  askPdf: (sessionId, question, language = 'en') => request('/api/pdf/ask', {
    method: 'POST',
    body: { session_id: sessionId, question, language },
  }),
  clearPdfSession: (sessionId) => request(`/api/pdf/session?session_id=${encodeURIComponent(sessionId)}`, { method: 'DELETE' }),
};
