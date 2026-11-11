import express from 'express';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import pg from 'pg';

const { Pool } = pg;
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const port = process.env.PORT || 8080;

const gameDir = path.join(__dirname, 'game');
const FIREBASE_API_KEY = process.env.FIREBASE_API_KEY || 'AIzaSyBEiIHIE1BaXoliSfYNwr2VZCKUBrNToUY';
const ADMIN_EMAIL = (process.env.ADMIN_EMAIL || 'willirexpilowey@gmail.com').toLowerCase();

let pgPool = null;

function getPool() {
  const url = process.env.DATABASE_URL;
  if (!url) return null;
  if (!pgPool) {
    const ssl = /sslmode=require|neon\.tech|supabase\.co/i.test(url) ? { rejectUnauthorized: false } : undefined;
    pgPool = new Pool({
      connectionString: url,
      ssl,
      max: 3,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 8000
    });
    pgPool.on('error', (err) => {
      console.error('PostgreSQL pool error:', err.message);
    });
  }
  return pgPool;
}

function serializeRows(rows) {
  return rows.map((row) => {
    const out = {};
    for (const key of Object.keys(row)) {
      const value = row[key];
      out[key] = typeof value === 'bigint' ? value.toString() : value;
    }
    return out;
  });
}

async function requireAdmin(req, res, next) {
  try {
    const header = req.get('authorization') || '';
    const token = header.startsWith('Bearer ') ? header.slice(7) : '';
    if (!token) {
      return res.status(401).json({ error: 'Falta la sesión de Firebase.' });
    }

    const lookup = await fetch('https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=' + encodeURIComponent(FIREBASE_API_KEY), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ idToken: token })
    });
    const data = await lookup.json().catch(() => ({}));
    const user = data.users && data.users[0];
    if (!lookup.ok || !user || !user.email || user.email.toLowerCase() !== ADMIN_EMAIL) {
      return res.status(403).json({ error: 'Solo el propietario puede acceder a la base de datos.' });
    }

    req.dbAdmin = user;
    next();
  } catch (e) {
    res.status(500).json({ error: 'No se pudo verificar la sesión de Firebase.' });
  }
}

app.use(express.json({ limit: '100kb' }));

app.use(express.static(gameDir, {
  extensions: ['html'],
  setHeaders: (res, filePath) => {
    if (filePath.endsWith('.html')) {
      res.setHeader('Cache-Control', 'no-cache');
    } else {
      res.setHeader('Cache-Control', 'public, max-age=3600');
    }
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  }
}));

app.get('/api/db/status', requireAdmin, async (req, res) => {
  const pool = getPool();
  if (!pool) {
    return res.json({ configured: false, connected: false });
  }
  try {
    const result = await pool.query('select version() as version, current_database() as database');
    res.json({
      configured: true,
      connected: true,
      version: result.rows[0].version,
      database: result.rows[0].database
    });
  } catch (e) {
    res.json({ configured: true, connected: false, error: 'No se pudo conectar a PostgreSQL.' });
  }
});

app.get('/api/db/tables', requireAdmin, async (req, res) => {
  const pool = getPool();
  if (!pool) return res.status(503).json({ error: 'PostgreSQL no está configurado.' });
  try {
    const result = await pool.query(
      "select table_schema, table_name from information_schema.tables where table_type = 'BASE TABLE' and table_schema not in ('pg_catalog', 'information_schema') order by table_schema, table_name"
    );
    res.json({ tables: result.rows });
  } catch (e) {
    res.status(500).json({ error: 'No se pudieron listar las tablas.' });
  }
});

app.get('/api/db/tables/:schema/:table', requireAdmin, async (req, res) => {
  const pool = getPool();
  if (!pool) return res.status(503).json({ error: 'PostgreSQL no está configurado.' });
  const schema = req.params.schema;
  const table = req.params.table;
  if (!/^[A-Za-z0-9_]+$/.test(schema) || !/^[A-Za-z0-9_]+$/.test(table)) {
    return res.status(400).json({ error: 'Nombre de tabla no válido.' });
  }
  const limit = Math.min(200, Math.max(1, parseInt(req.query.limit, 10) || 50));
  try {
    const result = await pool.query('select * from "' + schema + '"."' + table + '" limit $1', [limit]);
    res.json({
      schema,
      table,
      columns: result.fields.map((f) => f.name),
      rows: serializeRows(result.rows),
      limit
    });
  } catch (e) {
    res.status(400).json({ error: 'No se pudo leer la tabla.' });
  }
});

app.post('/api/db/query', requireAdmin, async (req, res) => {
  const pool = getPool();
  if (!pool) return res.status(503).json({ error: 'PostgreSQL no está configurado.' });
  const sql = typeof (req.body && req.body.sql) === 'string' ? req.body.sql.trim() : '';
  if (!sql) return res.status(400).json({ error: 'Escribe una consulta SELECT.' });
  if (!/^(select|with)\b/i.test(sql)) return res.status(400).json({ error: 'Solo se permiten consultas SELECT/WITH.' });
  if (sql.replace(/;\s*$/, '').includes(';')) return res.status(400).json({ error: 'Solo se permite una consulta.' });

  const client = await pool.connect();
  try {
    await client.query('BEGIN TRANSACTION READ ONLY');
    await client.query("SET LOCAL statement_timeout = '5000'");
    const result = await client.query(sql);
    await client.query('ROLLBACK');
    res.json({
      columns: result.fields ? result.fields.map((f) => f.name) : [],
      rows: serializeRows(result.rows || []),
      rowCount: result.rowCount
    });
  } catch (e) {
    try { await client.query('ROLLBACK'); } catch (err) { /* ignorar */ }
    res.status(400).json({ error: 'Error en la consulta: ' + e.message });
  } finally {
    client.release();
  }
});

app.use('/api', (req, res) => {
  res.status(404).json({ error: 'Ruta de API no encontrada.' });
});

app.use((req, res) => {
  res.sendFile(path.join(gameDir, 'index.html'));
});

app.listen(port, '0.0.0.0', () => {
  console.log('ACERO Y SAL escuchando en el puerto ' + port);
});
