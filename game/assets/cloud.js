'use strict';

/* Guardado en la nube con Firebase Authentication (anónimo) + Firestore. */

const CLOUD_SDK = 'https://www.gstatic.com/firebasejs/10.14.1/';

const cloud = {
  state: 'local',
  ready: false,
  uid: null,
  app: null,
  auth: null,
  db: null,
  fs: null,
  timer: null,
  lastSync: 0,
  lastError: ''
};
window.GameCloud = cloud;

function setCloudState(next, error) {
  cloud.state = next;
  if (error) cloud.lastError = error;
  if (typeof renderHeader === 'function') renderHeader();
}
window.setCloudState = setCloudState;

async function initCloud() {
  if (!window.FIREBASE_CONFIG || !window.FIREBASE_CONFIG.projectId) {
    setCloudState('local');
    return;
  }
  if (cloud.ready) return;

  setCloudState('connecting');
  try {
    const mods = await Promise.all([
      import(CLOUD_SDK + 'firebase-app.js'),
      import(CLOUD_SDK + 'firebase-auth.js'),
      import(CLOUD_SDK + 'firebase-firestore.js')
    ]);
    const appMod = mods[0];
    const authMod = mods[1];
    const fsMod = mods[2];

    const app = appMod.initializeApp(window.FIREBASE_CONFIG);
    const auth = authMod.getAuth(app);
    const db = fsMod.getFirestore(app);

    const cred = await authMod.signInAnonymously(auth);

    cloud.app = app;
    cloud.auth = auth;
    cloud.db = db;
    cloud.fs = fsMod;
    cloud.uid = cred.user.uid;
    cloud.ready = true;
    setCloudState('online');

    await pullCloud();
  } catch (e) {
    cloud.ready = false;
    cloud.lastError = (e && e.message) || 'Error de conexión';
    setCloudState('error', cloud.lastError);
    if (window.console) console.warn('[nube]', cloud.lastError);
  }
}
window.initCloud = initCloud;

async function pushCloud() {
  if (!cloud.ready || !cloud.db || typeof state === 'undefined' || !state) return false;
  try {
    state.savedAt = Date.now();
    const payload = JSON.parse(JSON.stringify(state));
    payload.savedAt = state.savedAt;
    await cloud.fs.setDoc(cloud.fs.doc(cloud.db, 'saves', cloud.uid), {
      json: JSON.stringify(payload),
      savedAt: payload.savedAt,
      updatedAt: new Date().toISOString()
    });
    cloud.lastSync = payload.savedAt;
    setCloudState('online');
    return true;
  } catch (e) {
    setCloudState('error', (e && e.message) || 'No se pudo guardar');
    return false;
  }
}
window.pushCloud = pushCloud;

async function pullCloud() {
  if (!cloud.ready || !cloud.db) return;
  try {
    const snap = await cloud.fs.getDoc(cloud.fs.doc(cloud.db, 'saves', cloud.uid));
    if (!snap.exists()) {
      if (typeof state !== 'undefined' && state) await pushCloud();
      return;
    }
    const data = snap.data() || {};
    let remote = null;
    try { remote = data.json ? JSON.parse(data.json) : null; } catch (e) { remote = null; }
    if (!remote || !remote.commander) {
      if (typeof state !== 'undefined' && state) await pushCloud();
      return;
    }

    const remoteTime = Number(data.savedAt || remote.savedAt || 0);
    const localTime = (typeof state !== 'undefined' && state) ? Number(state.savedAt || 0) : 0;

    if (typeof battle !== 'undefined' && battle && !battle.over) return;

    if (typeof state === 'undefined' || !state || remoteTime > localTime + 500) {
      remote.savedAt = remoteTime;
      remote.view = 'hq';
      if (typeof replaceState === 'function') replaceState(remote);
      else state = remote;
      try { localStorage.setItem(SAVE_KEY, JSON.stringify(remote)); } catch (e) { /* sin almacenamiento */ }
      if (typeof render === 'function') render();
      if (typeof toast === 'function') toast('Partida cargada desde Firebase.');
    } else if (localTime > remoteTime + 500) {
      await pushCloud();
    }
  } catch (e) {
    setCloudState('error', (e && e.message) || 'No se pudo leer la nube');
  }
}
window.pullCloud = pullCloud;

function scheduleCloudSave() {
  if (!cloud.ready || typeof state === 'undefined' || !state) return;
  clearTimeout(cloud.timer);
  cloud.timer = setTimeout(function () { pushCloud(); }, 1200);
}
window.scheduleCloudSave = scheduleCloudSave;

Game.cloudSync = function () {
  if (!cloud.ready) {
    toast('La nube aún no está conectada. Revisa tu conexión.');
    return;
  }
  pushCloud().then(function (ok) {
    toast(ok ? 'Partida sincronizada con Firebase.' : 'No se pudo sincronizar la partida.');
  });
};
