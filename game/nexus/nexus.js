'use strict';

const NEXUS_SDK = 'https://www.gstatic.com/firebasejs/10.14.1/';

const nexus = {
  auth: null,
  db: null,
  fs: null,
  uid: null,
  docRef: null,
  save: null,
  savedAt: 0
};

function el(id) { return document.getElementById(id); }
function fmt(n) { return Number(n || 0).toLocaleString('es-ES'); }
function shortUid(uid) { return uid ? uid.slice(0, 8) + '…' + uid.slice(-4) : '—'; }

function setChip(text, cls) {
  const chip = el('dbChip');
  if (!chip) return;
  chip.textContent = text;
  chip.className = 'db-chip' + (cls ? ' ' + cls : '');
}

function showError(message) {
  const box = el('errorBox');
  if (!box) return;
  box.className = 'error';
  box.textContent = message;
  box.classList.remove('hidden');
}

function showNotice(message) {
  const box = el('errorBox');
  if (!box) return;
  box.className = 'error success';
  box.textContent = message;
  box.classList.remove('hidden');
}

function clearMessage() {
  const box = el('errorBox');
  if (!box) return;
  box.classList.add('hidden');
  box.textContent = '';
  box.className = 'error hidden';
}

function formatDate(ts) {
  if (!ts) return '—';
  const d = new Date(Number(ts));
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleString('es-ES', { dateStyle: 'medium', timeStyle: 'short' });
}

function fleetPower(save) {
  let power = 0;
  (save.fleet || []).forEach(function (entry) {
    const ship = SHIP_MAP[entry.shipId];
    if (!ship) return;
    const lvl = 1 + 0.05 * ((entry.level || 1) - 1);
    const mods = entry.modules || { guns: 0, armor: 0, engine: 0 };
    power += (ship.stats.firepower * (1 + 0.09 * mods.guns) + ship.stats.armor * (1 + 0.09 * mods.armor)) * lvl;
    power += ship.stats.hp * (1 + 0.06 * ((entry.level || 1) - 1)) * 0.3;
    power += ship.stats.torpedo * (1 + 0.07 * mods.guns) * lvl * 0.5;
  });
  return Math.round(power);
}

function showEmpty() {
  nexus.save = null;
  el('saveTitle').textContent = 'Sin partida guardada';
  el('saveData').classList.add('hidden');
  el('saveEmpty').classList.remove('hidden');
  el('syncTime').textContent = '—';
  el('syncSource').textContent = 'sin datos';
}

function renderSave(save, savedAt, updatedAt) {
  nexus.save = save;
  nexus.savedAt = Number(savedAt || save.savedAt || 0);
  const cm = save.commander || { level: 1, credits: 0 };
  const fleet = save.fleet || [];

  el('saveTitle').textContent = 'Comandante · Nivel ' + (cm.level || 1);
  el('saveEmpty').classList.add('hidden');
  el('saveData').classList.remove('hidden');

  el('sLevel').textContent = cm.level || 1;
  el('sCredits').textContent = fmt(cm.credits);
  el('sMissions').textContent = fmt(save.missionsWon || 0);
  const cleared = (save.campaign && save.campaign.cleared) ? Object.keys(save.campaign.cleared).length : 0;
  el('sCampaign').textContent = cleared + '/' + (typeof CAMPAIGN !== 'undefined' ? CAMPAIGN.length : 10);
  el('sAchievements').textContent = (save.achievements || []).length + '/' + (typeof ACHIEVEMENTS !== 'undefined' ? ACHIEVEMENTS.length : 19);
  el('sSunk').textContent = fmt((save.stats && save.stats.sunk) || 0);
  const chestCount = save.chests ? ((save.chests.bronze || 0) + (save.chests.silver || 0) + (save.chests.gold || 0) + (save.chests.legendary || 0)) : 0;
  el('sChests').textContent = fmt(chestCount);
  el('sFleet').textContent = fleet.length;
  el('sPower').textContent = fmt(fleetPower(save));

  el('syncTime').textContent = formatDate(nexus.savedAt);
  el('syncSource').textContent = 'Firestore · documento saves/' + (nexus.uid ? nexus.uid.slice(0, 6) + '…' : '—');

  const list = el('fleetList');
  list.innerHTML = '';
  if (!fleet.length) {
    list.innerHTML = '<div class="fleet-row"><span>Sin buques guardados</span></div>';
    return;
  }
  fleet.forEach(function (entry) {
    const ship = SHIP_MAP[entry.shipId];
    if (!ship) return;
    const row = document.createElement('div');
    row.className = 'fleet-row';
    const role = SHIP_ROLES[ship.role] ? SHIP_ROLES[ship.role].label : ship.role;
    row.innerHTML = '<div class="f-left"><span class="dot"></span><span>' + ship.name +
      ' <span class="f-meta">' + role + ' · ' + ship.nation + ' · ' + ship.year + ' · Nv. ' + (entry.level || 1) + '</span></span></div>' +
      '<b>' + (entry.active ? 'ACTIVO' : 'RESERVA') + '</b>';
    list.appendChild(row);
  });
}

async function loadSave() {
  if (!nexus.fs || !nexus.docRef) return;
  clearMessage();
  try {
    const snap = await nexus.fs.getDoc(nexus.docRef);
    if (!snap.exists()) {
      showEmpty();
      return;
    }
    const data = snap.data() || {};
    let save = null;
    try { save = data.json ? JSON.parse(data.json) : null; } catch (e) { save = null; }
    if (!save || !save.commander || !Array.isArray(save.fleet)) {
      showEmpty();
      return;
    }
    renderSave(save, data.savedAt, data.updatedAt);
  } catch (e) {
    showError('No se pudo leer la partida: ' + ((e && e.message) || 'error'));
  }
}

function downloadSave() {
  if (!nexus.save) {
    showError('No hay partida para descargar.');
    return;
  }
  const payload = JSON.parse(JSON.stringify(nexus.save));
  payload.savedAt = nexus.savedAt || Date.now();
  const text = JSON.stringify(payload, null, 2);
  const blob = new Blob([text], { type: 'application/json' });
  const a = document.createElement('a');
  const date = new Date().toISOString().slice(0, 10);
  a.href = URL.createObjectURL(blob);
  a.download = 'acero-y-sal-' + (nexus.uid ? nexus.uid.slice(0, 6) : 'save') + '-' + date + '.json';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
  showNotice('Copia descargada. Guárdala para restaurarla en otro navegador.');
}

async function importSave(file) {
  if (!file) return;
  clearMessage();
  try {
    if (file.size > 900000) throw new Error('El archivo es demasiado grande.');
    const text = await file.text();
    const data = JSON.parse(text);
    if (!data || !data.commander || !Array.isArray(data.fleet) || !data.fleet.length) {
      throw new Error('El archivo no parece una partida de ACERO Y SAL.');
    }
    data.fleet.forEach(function (entry) {
      if (!entry.shipId || !SHIP_MAP[entry.shipId]) throw new Error('La partida contiene un buque desconocido.');
    });
    data.savedAt = Date.now();
    await nexus.fs.setDoc(nexus.docRef, {
      json: JSON.stringify(data),
      savedAt: data.savedAt,
      updatedAt: new Date().toISOString()
    });
    await loadSave();
    showNotice('Copia restaurada en Firestore. Abre el juego para cargarla.');
  } catch (e) {
    showError('No se pudo restaurar la copia: ' + ((e && e.message) || 'archivo inválido'));
  }
}

async function initNexus() {
  setChip('FIRESTORE · CONECTANDO');
  if (!window.FIREBASE_CONFIG) {
    setChip('FIRESTORE · SIN CONFIG', 'error');
    showError('Falta la configuración de Firebase.');
    return;
  }

  try {
    const mods = await Promise.all([
      import(NEXUS_SDK + 'firebase-app.js'),
      import(NEXUS_SDK + 'firebase-auth.js'),
      import(NEXUS_SDK + 'firebase-firestore.js')
    ]);
    const app = mods[0].initializeApp(window.FIREBASE_CONFIG);
    nexus.auth = mods[1].getAuth(app);
    nexus.db = mods[2].getFirestore(app);
    nexus.fs = mods[2];

    const cred = await mods[1].signInAnonymously(nexus.auth);
    nexus.uid = cred.user.uid;
    nexus.docRef = nexus.fs.doc(nexus.db, 'saves', nexus.uid);

    setChip('FIRESTORE · ONLINE', 'online');
    el('dbStatus').textContent = 'Conectada';
    el('authStatus').textContent = 'Anónima';
    el('uidText').textContent = 'UID: ' + shortUid(nexus.uid);
    el('uidText').title = nexus.uid;

    await loadSave();
  } catch (e) {
    setChip('FIRESTORE · ERROR', 'error');
    el('dbStatus').textContent = 'Error';
    el('authStatus').textContent = 'Sin sesión';
    showError('No se pudo conectar con Firebase: ' + ((e && e.message) || 'error de red'));
  }
}

el('refreshBtn').addEventListener('click', function () {
  clearMessage();
  loadSave();
});
el('downloadBtn').addEventListener('click', downloadSave);
el('importInput').addEventListener('change', function (e) {
  const file = e.target.files && e.target.files[0];
  importSave(file);
  e.target.value = '';
});

initNexus();
