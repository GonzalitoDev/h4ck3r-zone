'use strict';

/* Firebase Auth (invitado o email) + Firestore. */

const CLOUD_SDK = 'https://www.gstatic.com/firebasejs/10.14.1/';

const cloud = {
  state: 'local',
  ready: false,
  uid: null,
  user: null,
  app: null,
  auth: null,
  authMod: null,
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

function isAdminAccount() {
  const user = cloud.user;
  return !!(user && !user.isAnonymous && user.email && window.ADMIN_EMAIL &&
    user.email.toLowerCase() === String(window.ADMIN_EMAIL).toLowerCase());
}
window.isAdminAccount = isAdminAccount;

function authErrorMessage(error) {  const code = (error && error.code) || '';
  if (code.indexOf('email-already-in-use') !== -1) return 'Ese email ya está registrado. Inicia sesión.';
  if (code.indexOf('invalid-email') !== -1) return 'El email no es válido.';
  if (code.indexOf('weak-password') !== -1) return 'La contraseña debe tener al menos 6 caracteres.';
  if (code.indexOf('wrong-password') !== -1 || code.indexOf('invalid-credential') !== -1) return 'Email o contraseña incorrectos.';
  if (code.indexOf('user-not-found') !== -1) return 'No existe una cuenta con ese email.';
  if (code.indexOf('network-request-failed') !== -1) return 'Sin conexión a Firebase.';
  if (code.indexOf('requires-recent-login') !== -1) return 'Vuelve a iniciar sesión para continuar.';
  return (error && error.message) || 'Error de autenticación.';
}
window.authErrorMessage = authErrorMessage;

async function applyUser(user, keepState) {
  cloud.uid = user.uid;
  cloud.user = user;
  setSaveKey(user.uid, user.isAnonymous);
  cloud.ready = true;

  if (!keepState) {
    let local = null;
    if (typeof load === 'function') local = load();
    if (typeof replaceState === 'function') replaceState(local);
    else if (typeof state !== 'undefined') state = local;
  }

  setCloudState('online');
  await pullCloud();

  if (typeof render === 'function') render();
  if (typeof renderHeader === 'function') renderHeader();
}
window.applyAuthUser = applyUser;

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

    cloud.app = app;
    cloud.auth = auth;
    cloud.authMod = authMod;
    cloud.db = db;
    cloud.fs = fsMod;

    try {
      await authMod.setPersistence(auth, authMod.browserLocalPersistence);
    } catch (e) { /* persistencia por defecto */ }

    if (typeof auth.authStateReady === 'function') {
      await auth.authStateReady();
    }

    let user = auth.currentUser;
    if (!user) {
      const cred = await authMod.signInAnonymously(auth);
      user = cred.user;
    }

    if (user.isAnonymous) {
      cloud.uid = user.uid;
      cloud.user = user;
      setSaveKey(user.uid, true);
      cloud.ready = true;
      setCloudState('online');
      await pullCloud();
    } else {
      await applyUser(user, false);
    }
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

/* ---------- cuentas ---------- */

async function cloudLogin(email, password) {
  if (!cloud.auth || !cloud.authMod) throw new Error('La nube aún no está conectada.');
  if (typeof battle !== 'undefined' && battle && !battle.over) throw new Error('Termina el combate antes de iniciar sesión.');
  if (typeof state !== 'undefined' && state) {
    save();
    if (cloud.ready) await pushCloud();
  }
  const cred = await cloud.authMod.signInWithEmailAndPassword(cloud.auth, email, password);
  await applyUser(cred.user, false);
  return cred.user;
}
window.cloudLogin = cloudLogin;

async function cloudRegister(email, password) {
  if (!cloud.auth || !cloud.authMod) throw new Error('La nube aún no está conectada.');
  if (typeof battle !== 'undefined' && battle && !battle.over) throw new Error('Termina el combate antes de crear la cuenta.');
  const auth = cloud.auth;
  const authMod = cloud.authMod;
  if (auth.currentUser && !auth.currentUser.isAnonymous) throw new Error('Ya hay una sesión iniciada.');

  const guestState = (typeof state !== 'undefined' && state) ? JSON.parse(JSON.stringify(state)) : null;
  if (guestState) {
    save();
    if (cloud.ready) await pushCloud();
  }
  let cred = null;

  if (auth.currentUser && auth.currentUser.isAnonymous) {
    const credential = authMod.EmailAuthProvider.credential(email, password);
    cred = await authMod.linkWithCredential(auth.currentUser, credential);
  } else {
    cred = await authMod.createUserWithEmailAndPassword(auth, email, password);
  }

  const user = cred.user;
  cloud.uid = user.uid;
  cloud.user = user;
  setSaveKey(user.uid, false);
  cloud.ready = true;
  setCloudState('online');
  if (typeof renderHeader === 'function') renderHeader();

  if (guestState) {
    if (typeof replaceState === 'function') replaceState(guestState);
    else state = guestState;
    save();
    await pushCloud();
  } else {
    let local = null;
    if (typeof load === 'function') local = load();
    if (typeof replaceState === 'function') replaceState(local);
    else state = local;
    await pullCloud();
  }

  clearGuestSave();
  setCloudState('online');
  if (typeof render === 'function') render();
  if (typeof renderHeader === 'function') renderHeader();
  return user;
}
window.cloudRegister = cloudRegister;

async function cloudLogout() {
  if (!cloud.auth || !cloud.authMod) throw new Error('La nube aún no está conectada.');
  if (typeof battle !== 'undefined' && battle && !battle.over) throw new Error('Termina el combate antes de cerrar sesión.');

  if (typeof state !== 'undefined' && state) {
    save();
    await pushCloud();
  }

  await cloud.authMod.signOut(cloud.auth);
  const cred = await cloud.authMod.signInAnonymously(cloud.auth);
  await applyUser(cred.user, false);
  return cred.user;
}
window.cloudLogout = cloudLogout;

async function cloudResetPassword(email) {
  if (!cloud.auth || !cloud.authMod) throw new Error('La nube aún no está conectada.');
  if (!email || email.indexOf('@') === -1) throw new Error('Introduce un email válido.');
  await cloud.authMod.sendPasswordResetEmail(cloud.auth, email);
}
window.cloudResetPassword = cloudResetPassword;

async function deleteCloudSave() {
  if (!cloud.ready || !cloud.db || !cloud.fs) return false;
  try {
    await cloud.fs.deleteDoc(cloud.fs.doc(cloud.db, 'saves', cloud.uid));
    return true;
  } catch (e) {
    return false;
  }
}
window.deleteCloudSave = deleteCloudSave;

Game.cloudSync = function () {
  if (!cloud.ready) {
    toast('La nube aún no está conectada. Revisa tu conexión.');
    return;
  }
  pushCloud().then(function (ok) {
    toast(ok ? 'Partida sincronizada con Firebase.' : 'No se pudo sincronizar la partida.');
  });
};
