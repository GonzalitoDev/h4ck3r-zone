export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Webhook-URL');

  if (req.method === 'OPTIONS') return res.status(200).end();

  try {
    const { path, method, webhook } = req.query;
    const auth = req.headers['authorization'];
    const body = req.method === 'POST' ? req.body : null;

    let url;
    const headers = { 'Content-Type': 'application/json', 'User-Agent': 'H4CK3R-ZONE/6.0' };

    if (webhook === '1' && req.headers['x-webhook-url']) {
      url = decodeURIComponent(req.headers['x-webhook-url']);
    } else if (path) {
      const dcPath = '/v10/' + path.replace(/^\//, '');
      url = 'https://discord.com/api' + dcPath;
      if (auth) headers['Authorization'] = auth;
    } else {
      return res.status(400).json({ error: 'Missing path or webhook parameter' });
    }

    const fetchOpts = { method: method || 'GET', headers };
    if (body && method !== 'GET') {
      fetchOpts.body = typeof body === 'object' ? JSON.stringify(body) : body;
    }

    const response = await fetch(url, fetchOpts);
    const contentType = response.headers.get('content-type') || '';

    if (response.status === 204 || response.status === 205) {
      return res.status(response.status).end();
    }

    if (contentType.includes('application/json')) {
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || data.error || 'HTTP ' + response.status);
      return res.status(response.status).json(data);
    } else {
      const text = await response.text();
      if (!response.ok) throw new Error(text || 'HTTP ' + response.status);
      return res.status(response.status).json({ ok: true, text: text.substring(0, 500) });
    }
  } catch (err) {
    res.status(500).json({ error: err.message || 'Internal server error' });
  }
}
