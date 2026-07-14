export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Webhook-URL');
  
  if (req.method === 'OPTIONS') return res.status(200).end();

  try {
    const path = req.query.path || '';
    const method = req.query.method || 'GET';
    const webhook = req.query.webhook === '1';
    const auth = req.headers['authorization'];
    const body = req.body;

    let url;
    const headers = { 'Content-Type': 'application/json', 'User-Agent': 'H4CK3R-ZONE/6.0' };

    if (webhook) {
      url = req.headers['x-webhook-url'] || '';
      if (!url) return res.status(400).json({ error: 'Missing webhook URL' });
    } else if (path) {
      const cleanPath = path.startsWith('/') ? path : '/' + path;
      url = 'https://discord.com/api/v10' + cleanPath;
      if (auth) headers['Authorization'] = auth;
    } else {
      return res.status(400).json({ error: 'Missing path parameter' });
    }

    const fetchOpts = { method, headers };
    if (body && method !== 'GET') {
      fetchOpts.body = typeof body === 'object' ? JSON.stringify(body) : body;
    }

    const response = await fetch(url, fetchOpts);
    const contentType = response.headers.get('content-type') || '';

    if (response.status === 204 || response.status === 205) {
      return res.status(200).json({ ok: true });
    }

    if (contentType.includes('application/json')) {
      const data = await response.json();
      if (!response.ok) {
        return res.status(response.status).json({ error: data.message || data.error || 'HTTP ' + response.status });
      }
      return res.status(response.status).json(data);
    }

    const text = await response.text();
    if (!response.ok) {
      return res.status(response.status).json({ error: text.substring(0, 200) || 'HTTP ' + response.status });
    }
    return res.status(response.status).json({ ok: true, text: text.substring(0, 500) });
  } catch (err) {
    return res.status(500).json({ error: err.message || 'Internal server error' });
  }
}
