'use strict';

/* Panel privado del propietario. No está enlazado desde el juego. */

function showNotice(message, ok) {
  const box = document.getElementById('notice');
  if (!box) return;
  box.className = 'notice' + (ok ? ' success' : '');
  box.textContent = message;
  box.classList.remove('hidden');
}

function toast(message) {
  showNotice(message, true);
}

function showGateError(message) {
  const box = document.getElementById('gateError');
  if (!box) return;
  box.className = 'notice error';
  box.textContent = message;
  box.classList.remove('hidden');
}

function updateCloudStatus() {
  const chip = document.getElementById('cloudChip');
  if (!chip) return;
  const c = window.GameCloud ? window.GameCloud.state : 'local';
  const labels = { online: 'NUBE · ON', connecting: 'NUBE · ...', error: 'NUBE · ERROR', local: 'NUBE · LOCAL' };
  chip.textContent = labels[c] || 'NUBE · LOCAL';
  chip.className = 'status-chip ' + c;
}

function sha256(text) {
  return crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)).then(function (buffer) {
    return Array.from(new Uint8Array(buffer)).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
  });
}

function adminUnlock() {
  const input = document.getElementById('adminPass');
  const pass = input ? input.value : '';
  if (!(window.isAdminAccount && window.isAdminAccount())) {
    showGateError('Inicia sesión en el juego con la cuenta de propietario.');
    return;
  }
  if (!pass) { showGateError('Introduce la contraseña.'); return; }
  if (!crypto.subtle) { showGateError('Este navegador no permite validar la contraseña.'); return; }
  sha256(pass).then(function (hash) {
    if (hash === window.ADMIN_CONFIG.passwordHash) {
      sessionStorage.setItem('aceroAdmin', '1');
      renderAdmin();
      showNotice('Acceso concedido. Panel desbloqueado.', true);
    } else {
      showGateError('Contraseña incorrecta.');
    }
  }).catch(function () {
    showGateError('No se pudo validar la contraseña.');
  });
}
window.adminUnlock = adminUnlock;

function adminLogout() {
  sessionStorage.removeItem('aceroAdmin');
  location.reload();
}
window.adminLogout = adminLogout;

function showAdminLoginError(message) {
  const box = document.getElementById('adminLoginError');
  if (!box) return;
  box.textContent = message;
  box.className = 'notice error';
  box.classList.remove('hidden');
}

async function adminLogin() {
  const email = document.getElementById('adminEmail');
  const password = document.getElementById('adminLoginPass');
  if (!email || !password) return;
  if (!window.cloudLogin) {
    showAdminLoginError('La conexión con Firebase aún no está lista.');
    return;
  }
  try {
    await window.cloudLogin(email.value.trim(), password.value);
    if (!(window.isAdminAccount && window.isAdminAccount())) {
      showAdminLoginError('Esa cuenta no es la cuenta del propietario.');
      return;
    }
    renderAdmin();
  } catch (e) {
    showAdminLoginError(window.authErrorMessage ? window.authErrorMessage(e) : (e.message || 'No se pudo iniciar sesión.'));
  }
}
window.adminLogin = adminLogin;

function adminOpenDb() {
  const panel = document.getElementById('dbPanel');
  if (!panel) return;
  panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  adminDbStatus();
}
window.adminOpenDb = adminOpenDb;

function baseState() {
  return {
    version: 1,
    commander: {
      level: 1, xp: 0, credits: 5000, points: 5,
      skills: { artilleria: 0, navegacion: 0, ingenieria: 0, liderazgo: 0, tactica: 0, logistica: 0, inteligencia: 0 }
    },
    fleet: [makeEntry('fletcher', true)],
    officers: [],
    missionsWon: 0,
    ops: [],
    lastResult: null,
    achievements: [],
    campaign: { cleared: {} },
    stats: { sunk: 0, specials: 0, bossWins: 0, kills: {} },
    chests: { bronze: 1, silver: 0, gold: 0, legendary: 0 },
    view: 'hq'
  };
}

function populateSelects() {
  const shipSelect = document.getElementById('shipSelect');
  if (shipSelect && !shipSelect.options.length) {
    const ships = SHIPS.slice().sort(function (a, b) { return a.name.localeCompare(b.name); });
    shipSelect.innerHTML = ships.map(function (s) {
      return '<option value="' + s.id + '">' + s.name + (s.exclusive ? ' · EXCLUSIVO' : '') + '</option>';
    }).join('');
  }

  const officerSelect = document.getElementById('officerSelect');
  if (officerSelect && !officerSelect.options.length) {
    const officers = OFFICERS.slice().sort(function (a, b) { return a.name.localeCompare(b.name); });
    officerSelect.innerHTML = officers.map(function (o) {
      return '<option value="' + o.id + '">' + o.name + ' · ' + o.title + '</option>';
    }).join('');
  }

  const chestType = document.getElementById('chestType');
  if (chestType && !chestType.options.length) {
    chestType.innerHTML = CHESTS.map(function (c) {
      return '<option value="' + c.id + '">' + c.name + '</option>';
    }).join('');
  }
}

function renderAdmin() {
  const gate = document.getElementById('gate');
  const dashboard = document.getElementById('dashboard');
  const restricted = document.getElementById('restricted');
  const adminAccount = !!(window.isAdminAccount && window.isAdminAccount());

  if (!adminAccount) {
    if (gate) gate.classList.add('hidden');
    if (dashboard) dashboard.classList.add('hidden');
    if (restricted) restricted.classList.remove('hidden');
    return;
  }

  if (restricted) restricted.classList.add('hidden');
  const unlocked = sessionStorage.getItem('aceroAdmin') === '1';
  if (gate) gate.classList.toggle('hidden', unlocked);
  if (dashboard) dashboard.classList.toggle('hidden', !unlocked);
  if (!unlocked) return;

  updateCloudStatus();
  populateSelects();
  if (!window.__dbAutoChecked) {
    window.__dbAutoChecked = true;
    setTimeout(function () { adminDbStatus(); }, 600);
  }

  const summary = document.getElementById('summary');
  const noSave = document.getElementById('noSave');
  const tools = document.getElementById('tools');
  if (!summary) return;

  if (!state) {
    summary.innerHTML = '';
    if (noSave) noSave.classList.remove('hidden');
    if (tools) tools.classList.add('hidden');
    return;
  }

  if (noSave) noSave.classList.add('hidden');
  if (tools) tools.classList.remove('hidden');

  const cleared = state.campaign && state.campaign.cleared ? Object.keys(state.campaign.cleared).length : 0;
  const uid = window.GameCloud && window.GameCloud.uid ? window.GameCloud.uid : '—';
  summary.innerHTML =
    '<div><span>Nivel</span><b>' + state.commander.level + '</b></div>' +
    '<div><span>Créditos</span><b>' + fmt(state.commander.credits) + '</b></div>' +
    '<div><span>Buques</span><b>' + state.fleet.length + '</b></div>' +
    '<div><span>Baúles</span><b>' + totalChests() + '</b></div>' +
    '<div><span>Campaña</span><b>' + cleared + '/' + CAMPAIGN.length + '</b></div>' +
    '<div><span>Logros</span><b>' + state.achievements.length + '/' + ACHIEVEMENTS.length + '</b></div>' +
    '<div><span>UID</span><b style="font-size:.7rem">' + uid.slice(0, 10) + '…</b></div>';
}

window.render = renderAdmin;
window.renderHeader = updateCloudStatus;

function persist(message) {
  if (!state) return;
  state.savedAt = Date.now();
  save();
  if (window.GameCloud && window.GameCloud.ready && typeof pushCloud === 'function') {
    pushCloud();
  }
  renderAdmin();
  showNotice(message, true);
}

window.adminAddCredits = function (sign) {
  if (!state) { showNotice('No hay partida. Crea una partida base primero.', false); return; }
  const input = document.getElementById('creditsAmount');
  const value = Math.max(0, parseInt(input.value, 10) || 0);
  if (value <= 0) { showNotice('Introduce una cantidad válida.', false); return; }
  state.commander.credits = Math.max(0, state.commander.credits + sign * value);
  persist((sign > 0 ? 'Añadidos ' : 'Quitados ') + fmt(value) + ' créditos.');
};

window.adminSetLevel = function () {
  if (!state) { showNotice('No hay partida. Crea una partida base primero.', false); return; }
  const level = parseInt(document.getElementById('levelValue').value, 10) || 1;
  const points = parseInt(document.getElementById('pointsValue').value, 10) || 0;
  state.commander.level = clamp(level, 1, 99);
  state.commander.points = clamp(points, 0, 99);
  persist('Nivel ' + state.commander.level + ' y ' + state.commander.points + ' puntos aplicados.');
};

window.adminAddShip = function () {
  if (!state) { showNotice('No hay partida. Crea una partida base primero.', false); return; }
  const id = document.getElementById('shipSelect').value;
  const ship = SHIP_MAP[id];
  if (!ship) return;
  if (state.fleet.some(function (e) { return e.shipId === id; })) {
    showNotice('Ya tienes ' + ship.name + '.', false);
    return;
  }
  state.fleet.push(makeEntry(id, activeShips().length < slots()));
  persist('Buque añadido: ' + ship.name + '.');
};

window.adminAddOfficer = function () {
  if (!state) { showNotice('No hay partida. Crea una partida base primero.', false); return; }
  const id = document.getElementById('officerSelect').value;
  const officer = OFFICER_MAP[id];
  if (!officer) return;
  if (state.officers.indexOf(id) !== -1) {
    showNotice('Ya tienes a ' + officer.name + '.', false);
    return;
  }
  state.officers.push(id);
  persist('Oficial añadido: ' + officer.name + '.');
};

window.adminAddChest = function () {
  if (!state) { showNotice('No hay partida. Crea una partida base primero.', false); return; }
  const type = document.getElementById('chestType').value;
  const count = Math.max(1, parseInt(document.getElementById('chestCount').value, 10) || 1);
  if (!CHEST_MAP[type]) return;
  state.chests = state.chests || { bronze: 0, silver: 0, gold: 0, legendary: 0 };
  state.chests[type] = (state.chests[type] || 0) + count;
  persist('Añadidos ' + count + ' ' + CHEST_MAP[type].name + '.');
};

window.adminGrantExclusive = function () {
  if (!state) { showNotice('No hay partida. Crea una partida base primero.', false); return; }
  let count = 0;
  EXCLUSIVE_SHIPS.forEach(function (s) {
    if (!state.fleet.some(function (e) { return e.shipId === s.id; })) {
      state.fleet.push(makeEntry(s.id, activeShips().length < slots()));
      count++;
    }
  });
  persist(count ? 'Añadidos ' + count + ' buques exclusivos.' : 'Ya tienes todos los exclusivos.');
};

window.adminUnlockCampaign = function () {
  if (!state) { showNotice('No hay partida. Crea una partida base primero.', false); return; }
  state.campaign = state.campaign || { cleared: {} };
  CAMPAIGN.forEach(function (c, i) { state.campaign.cleared[i] = true; });
  persist('Campaña desbloqueada al 100%.');
};

window.adminUnlockAchievements = function () {
  if (!state) { showNotice('No hay partida. Crea una partida base primero.', false); return; }
  state.achievements = ACHIEVEMENTS.map(function (a) { return a.id; });
  persist('Todos los logros marcados como completados (sin recompensas).');
};

window.adminRepairFleet = function () {
  if (!state) { showNotice('No hay partida. Crea una partida base primero.', false); return; }
  state.fleet.forEach(function (e) { e.hp = shipMaxHp(e); });
  persist('Flota reparada al 100%.');
};

window.adminSync = function () {
  if (!window.GameCloud || !window.GameCloud.ready) {
    showNotice('La nube aún no está conectada.', false);
    return;
  }
  pushCloud().then(function (ok) {
    showNotice(ok ? 'Partida guardada en Firebase.' : 'No se pudo guardar en Firebase.', ok);
    renderAdmin();
  });
};

window.adminCreateBase = function () {
  replaceState(baseState());
  persist('Partida base creada.');
};

/* ---------- PostgreSQL ---------- */

function escapeDb(value) {
  if (value === null || value === undefined) return '<span class="db-null">NULL</span>';
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .slice(0, 240);
}

async function adminApi(url, options) {
  if (!(window.isAdminAccount && window.isAdminAccount())) throw new Error('Inicia sesión con la cuenta de propietario.');
  if (!window.GameCloud || !window.GameCloud.user) throw new Error('Sin sesión de Firebase.');
  const token = await window.GameCloud.user.getIdToken();
  const headers = Object.assign({}, options && options.headers, { Authorization: 'Bearer ' + token });
  const res = await fetch(url, Object.assign({}, options, { headers }));
  const data = await res.json().catch(function () { return {}; });
  if (!res.ok) throw new Error(data.error || ('HTTP ' + res.status));
  return data;
}

function renderDbRows(columns, rows) {
  if (!rows || !rows.length) return '<p class="db-empty">Sin filas.</p>';
  let html = '<table class="db-table"><thead><tr>';
  columns.forEach(function (c) { html += '<th>' + escapeDb(c) + '</th>'; });
  html += '</tr></thead><tbody>';
  rows.forEach(function (row) {
    html += '<tr>';
    columns.forEach(function (c) { html += '<td>' + escapeDb(row[c]) + '</td>'; });
    html += '</tr>';
  });
  return html + '</tbody></table>';
}

async function adminDbStatus() {
  const statusEl = document.getElementById('dbStatus');
  const browserEl = document.getElementById('dbBrowser');
  if (!statusEl) return;
  statusEl.textContent = 'Comprobando conexión…';
  if (browserEl) browserEl.classList.add('hidden');
  try {
    const data = await adminApi('/api/db/status');
    if (!data.configured) {
      statusEl.innerHTML = 'PostgreSQL no configurado. Crea una base en <strong>Neon</strong> o <strong>Supabase</strong> y guarda <code>DATABASE_URL</code> como secreto de App Hosting.';
      return;
    }
    if (!data.connected) {
      statusEl.textContent = 'Configurado pero sin conexión: ' + (data.error || 'error desconocido');
      return;
    }
    statusEl.innerHTML = 'Conectado a <code>' + escapeDb(data.database) + '</code><br><span class="tiny">' + escapeDb(data.version) + '</span>';
    if (browserEl) browserEl.classList.remove('hidden');
    await adminLoadTables();
  } catch (e) {
    statusEl.textContent = e.message;
  }
}

async function adminLoadTables() {
  const tablesEl = document.getElementById('dbTables');
  if (!tablesEl) return;
  tablesEl.innerHTML = 'Cargando tablas…';
  try {
    const data = await adminApi('/api/db/tables');
    window.__adminDbTables = data.tables || [];
    if (!window.__adminDbTables.length) {
      tablesEl.innerHTML = '<span class="db-empty">Sin tablas.</span>';
      return;
    }
    tablesEl.innerHTML = window.__adminDbTables.map(function (t, index) {
      return '<button class="db-table-btn" onclick="adminLoadTable(' + index + ')">' + escapeDb(t.table_schema + '.' + t.table_name) + '</button>';
    }).join('');
  } catch (e) {
    tablesEl.innerHTML = '<span class="db-error">' + escapeDb(e.message) + '</span>';
  }
}

async function adminLoadTable(index) {
  const table = window.__adminDbTables && window.__adminDbTables[index];
  const contentEl = document.getElementById('dbContent');
  if (!table || !contentEl) return;
  contentEl.textContent = 'Cargando…';
  try {
    const data = await adminApi(
      '/api/db/tables/' + encodeURIComponent(table.table_schema) + '/' + encodeURIComponent(table.table_name) + '?limit=100'
    );
    contentEl.innerHTML = '<div class="db-title">' + escapeDb(data.schema + '.' + data.table) + ' <span class="tiny">(' + data.rows.length + ' filas, límite ' + data.limit + ')</span></div>' +
      renderDbRows(data.columns, data.rows);
  } catch (e) {
    contentEl.innerHTML = '<div class="db-error">' + escapeDb(e.message) + '</div>';
  }
}

async function adminRunQuery() {
  const sqlEl = document.getElementById('dbSql');
  const outEl = document.getElementById('dbQueryResult');
  if (!sqlEl || !outEl) return;
  const sql = sqlEl.value.trim();
  if (!sql) { outEl.innerHTML = '<div class="db-error">Escribe una consulta.</div>'; return; }
  outEl.textContent = 'Ejecutando…';
  try {
    const data = await adminApi('/api/db/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql: sql })
    });
    outEl.innerHTML = '<div class="db-title">Resultado <span class="tiny">(' + (data.rowCount || 0) + ' filas)</span></div>' +
      renderDbRows(data.columns || [], data.rows || []);
  } catch (e) {
    outEl.innerHTML = '<div class="db-error">' + escapeDb(e.message) + '</div>';
  }
}

window.adminDbStatus = adminDbStatus;
window.adminLoadTables = adminLoadTables;
window.adminLoadTable = adminLoadTable;
window.adminRunQuery = adminRunQuery;

document.addEventListener('DOMContentLoaded', function () {
  const saved = load();
  if (saved) replaceState(saved);

  const pass = document.getElementById('adminPass');
  if (pass) {
    pass.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') adminUnlock();
    });
  }

  renderAdmin();
  if (typeof initCloud === 'function') initCloud();
});
