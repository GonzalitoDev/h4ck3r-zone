import express from 'express';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import pg from 'pg';
import admin from 'firebase-admin';

const { Pool } = pg;
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const port = process.env.PORT || 8080;

const gameDir = path.join(__dirname, 'game');
const FIREBASE_API_KEY = process.env.FIREBASE_API_KEY || 'AIzaSyBEiIHIE1BaXoliSfYNwr2VZCKUBrNToUY';
const ADMIN_EMAIL = (process.env.ADMIN_EMAIL || 'willirexpilowey@gmail.com').toLowerCase();
const FIREBASE_PROJECT_ID = 'juego-e0d5f';

let pgPool = null;
let adminApp = null;

function getAdminServices() {
  if (!adminApp) {
    adminApp = admin.initializeApp({
      credential: admin.credential.applicationDefault(),
      projectId: FIREBASE_PROJECT_ID
    });
  }
  return { auth: admin.auth(), db: admin.firestore() };
}

function userSummary(user) {
  return {
    uid: user.uid,
    email: user.email || null,
    phone: user.phoneNumber || null,
    displayName: user.displayName || null,
    disabled: user.disabled,
    emailVerified: user.emailVerified,
    providers: (user.providerData || []).map((p) => p.providerId),
    anonymous: (user.providerData || []).length === 0,
    vip: !!(user.customClaims && user.customClaims.vip),
    created: user.metadata && user.metadata.creationTime,
    lastSignIn: user.metadata && user.metadata.lastSignInTime
  };
}

function saveSummary(save) {
  if (!save) return null;
  return {
    level: save.commander && save.commander.level,
    credits: save.commander && save.commander.credits,
    missionsWon: save.missionsWon,
    fleet: Array.isArray(save.fleet) ? save.fleet.length : 0,
    chests: save.chests || null,
    vip: !!save.vip,
    achievements: Array.isArray(save.achievements) ? save.achievements.length : 0,
    campaign: save.campaign && save.campaign.cleared ? Object.keys(save.campaign.cleared).length : 0
  };
}

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

app.get('/api/admin/users', requireAdmin, async (req, res) => {
  try {
    const { auth } = getAdminServices();
    const list = await auth.listUsers(1000);
    res.json({ users: list.users.map(userSummary) });
  } catch (e) {
    res.status(500).json({ error: 'No se pudieron listar los usuarios: ' + e.message });
  }
});

app.get('/api/admin/users/:uid', requireAdmin, async (req, res) => {
  try {
    const { auth, db } = getAdminServices();
    const user = await auth.getUser(req.params.uid);
    const snap = await db.collection('saves').doc(user.uid).get();
    let save = null;
    let savedAt = 0;
    if (snap.exists) {
      const data = snap.data() || {};
      savedAt = Number(data.savedAt || 0);
      try { save = JSON.parse(data.json); } catch (e) { save = null; }
    }
    res.json({ user: userSummary(user), save, saveExists: !!save, savedAt });
  } catch (e) {
    res.status(500).json({ error: 'No se pudo leer el usuario: ' + e.message });
  }
});

app.patch('/api/admin/users/:uid', requireAdmin, async (req, res) => {
  try {
    const { auth } = getAdminServices();
    const uid = req.params.uid;
    const body = req.body || {};
    const updates = {};
    if (typeof body.email === 'string' && body.email.trim()) updates.email = body.email.trim();
    if (typeof body.password === 'string' && body.password) {
      if (body.password.length < 6) return res.status(400).json({ error: 'La contraseña debe tener al menos 6 caracteres.' });
      updates.password = body.password;
    }
    if (typeof body.disabled === 'boolean') updates.disabled = body.disabled;
    if (typeof body.emailVerified === 'boolean') updates.emailVerified = body.emailVerified;
    if (typeof body.displayName === 'string') updates.displayName = body.displayName;
    if (!Object.keys(updates).length) return res.status(400).json({ error: 'No hay cambios válidos.' });
    if (req.dbAdmin && req.dbAdmin.localId === uid && (updates.email || updates.disabled)) {
      return res.status(400).json({ error: 'No cambies el email ni desactives la cuenta admin desde el panel.' });
    }
    const user = await auth.updateUser(uid, updates);
    res.json({ ok: true, user: userSummary(user) });
  } catch (e) {
    res.status(500).json({ error: 'No se pudo actualizar el usuario: ' + e.message });
  }
});

app.post('/api/admin/users/:uid/vip', requireAdmin, async (req, res) => {
  try {
    const { auth, db } = getAdminServices();
    const uid = req.params.uid;
    const enabled = !!(req.body && req.body.vip);
    const user = await auth.getUser(uid);
    const claims = Object.assign({}, user.customClaims || {}, { vip: enabled });
    await auth.setCustomUserClaims(uid, claims);
    const ref = db.collection('saves').doc(uid);
    const snap = await ref.get();
    if (snap.exists) {
      try {
        const data = snap.data() || {};
        const save = JSON.parse(data.json);
        save.vip = enabled;
        save.savedAt = Date.now();
        await ref.set({ json: JSON.stringify(save), savedAt: save.savedAt, updatedAt: new Date().toISOString() }, { merge: true });
      } catch (e) { /* partida no válida */ }
    }
    res.json({ ok: true, vip: enabled, message: 'El usuario debe recargar la página para recibir el VIP.' });
  } catch (e) {
    res.status(500).json({ error: 'No se pudo actualizar el VIP: ' + e.message });
  }
});

app.post('/api/admin/users/:uid/send-reset', requireAdmin, async (req, res) => {
  try {
    const { auth } = getAdminServices();
    const user = await auth.getUser(req.params.uid);
    if (!user.email) return res.status(400).json({ error: 'El usuario no tiene email.' });
    const result = await fetch('https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key=' + encodeURIComponent(FIREBASE_API_KEY), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requestType: 'PASSWORD_RESET', email: user.email })
    });
    if (!result.ok) {
      const data = await result.json().catch(() => ({}));
      return res.status(400).json({ error: (data.error && data.error.message) || 'No se pudo enviar el correo.' });
    }
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: 'No se pudo enviar el correo: ' + e.message });
  }
});

app.patch('/api/admin/users/:uid/save', requireAdmin, async (req, res) => {
  try {
    const { db } = getAdminServices();
    const uid = req.params.uid;
    const body = req.body || {};
    const ref = db.collection('saves').doc(uid);
    const snap = await ref.get();
    if (!snap.exists) return res.status(404).json({ error: 'El usuario no tiene una partida guardada.' });
    const data = snap.data() || {};
    let save;
    try { save = JSON.parse(data.json); } catch (e) { return res.status(500).json({ error: 'La partida guardada no es válida.' }); }
    if (!save.commander) return res.status(500).json({ error: 'La partida no tiene comandante.' });

    if (body.addCredits != null) {
      const delta = Number(body.addCredits);
      if (!Number.isFinite(delta)) return res.status(400).json({ error: 'Créditos no válidos.' });
      save.commander.credits = Math.max(0, Math.min(999999999, Math.round((save.commander.credits || 0) + delta)));
    }
    if (body.credits != null) {
      const value = Number(body.credits);
      if (!Number.isFinite(value)) return res.status(400).json({ error: 'Créditos no válidos.' });
      save.commander.credits = Math.max(0, Math.min(999999999, Math.round(value)));
    }
    if (body.level != null) save.commander.level = Math.max(1, Math.min(99, parseInt(body.level, 10) || 1));
    if (body.points != null) save.commander.points = Math.max(0, Math.min(99, parseInt(body.points, 10) || 0));
    if (body.chests && typeof body.chests === 'object') {
      save.chests = save.chests || { bronze: 0, silver: 0, gold: 0, legendary: 0 };
      ['bronze', 'silver', 'gold', 'legendary'].forEach((key) => {
        const value = parseInt(body.chests[key], 10) || 0;
        if (value) save.chests[key] = Math.max(0, (save.chests[key] || 0) + Math.min(999, value));
      });
    }
    if (body.unlockCampaign) {
      save.campaign = save.campaign || { cleared: {} };
      save.campaign.cleared = save.campaign.cleared || {};
      for (let i = 0; i < 10; i++) save.campaign.cleared[i] = true;
    }
    if (body.repair) {
      (save.fleet || []).forEach((entry) => { entry.hp = null; });
    }
    if (body.grantShip) {
      const shipId = String(body.grantShip);
      if (!/^[A-Za-z0-9_]+$/.test(shipId)) return res.status(400).json({ error: 'Buque no válido.' });
      save.fleet = save.fleet || [];
      if (!save.fleet.some((entry) => entry.shipId === shipId)) {
        save.fleet.push({
          uid: 'a' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7),
          shipId: shipId,
          level: 1,
          xp: 0,
          modules: { guns: 0, armor: 0, engine: 0 },
          officer: null,
          active: false,
          hp: null
        });
      }
    }
    if (body.grantOfficer) {
      const officerId = String(body.grantOfficer);
      if (!/^[A-Za-z0-9_]+$/.test(officerId)) return res.status(400).json({ error: 'Oficial no válido.' });
      save.officers = save.officers || [];
      if (save.officers.indexOf(officerId) === -1) save.officers.push(officerId);
    }

    save.savedAt = Date.now();
    await ref.set({ json: JSON.stringify(save), savedAt: save.savedAt, updatedAt: new Date().toISOString() }, { merge: true });
    res.json({ ok: true, summary: saveSummary(save), savedAt: save.savedAt });
  } catch (e) {
    res.status(500).json({ error: 'No se pudo guardar la partida: ' + e.message });
  }
});

app.delete('/api/admin/users/:uid', requireAdmin, async (req, res) => {
  try {
    const { auth, db } = getAdminServices();
    const uid = req.params.uid;
    if (req.dbAdmin && req.dbAdmin.localId === uid) return res.status(400).json({ error: 'No puedes eliminar tu propia cuenta admin.' });
    await auth.deleteUser(uid);
    await db.collection('saves').doc(uid).delete().catch(() => {});
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: 'No se pudo eliminar el usuario: ' + e.message });
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
