'use strict';

/* ---------- cabecera y enrutado ---------- */

function renderHeader() {
  const bar = $('#topbar');
  if (!state) {
    bar.classList.add('hidden');
    bar.innerHTML = '';
    return;
  }
  bar.classList.remove('hidden');
  const cm = state.commander;
  const need = xpNeedCommander(cm.level);
  const xpPct = clamp(Math.round(cm.xp / need * 100), 0, 100);
  const navs = [['hq', 'Mando'], ['fleet', 'Flota'], ['ops', 'Operaciones'], ['chests', 'Baúles'], ['campaign', 'Campaña'], ['bridge', 'Puente'], ['yard', 'Astillero'], ['codex', 'Códice']];
  const cloudState = window.GameCloud ? window.GameCloud.state : 'local';
  const cloudLabel = cloudState === 'online' ? 'NUBE · ON'
    : cloudState === 'connecting' ? 'NUBE · ...'
    : cloudState === 'error' ? 'NUBE · ERROR'
    : 'NUBE · LOCAL';
  const accountUser = window.GameCloud ? window.GameCloud.user : null;
  const accountLabel = accountUser && !accountUser.isAnonymous ? (accountUser.email || 'CUENTA') : 'INVITADO';
  const accountShort = accountLabel.length > 20 ? accountLabel.slice(0, 18) + '…' : accountLabel;

  bar.innerHTML = `
    <div class="brand" onclick="Game.go('hq')">
      <div class="brand-mark">A<span>S</span></div>
      <div class="brand-text"><strong>ACERO Y SAL</strong><small>RPG NAVAL</small></div>
    </div>
    <div class="resources">
      <div class="res"><span class="res-label">NIVEL</span><span class="res-val">${cm.level}</span></div>
      <div class="res wide"><span class="res-label">EXPERIENCIA</span><div class="mini-bar"><i style="width:${xpPct}%"></i></div><span class="res-sub">${fmt(cm.xp)} / ${fmt(need)}</span></div>
      <div class="res"><span class="res-label">CRÉDITOS</span><span class="res-val">${fmt(cm.credits)}</span></div>
      <div class="res"><span class="res-label">MISIONES</span><span class="res-val">${state.missionsWon}</span></div>
      <div class="res"><span class="res-label">BAÚLES</span><span class="res-val">${totalChests()}</span></div>
    </div>
    <button class="sound-btn" onclick="Game.toggleSound()" title="Activar o desactivar sonido">${soundOn ? 'SONIDO ON' : 'SONIDO OFF'}</button>
    <button class="cloud-chip ${cloudState}" onclick="Game.cloudSync()" title="Sincronizar la partida con Firebase">${cloudLabel}</button>
    <button class="account-chip" onclick="Game.showAccount()" title="Cuenta de usuario">${accountShort}</button>
    <nav class="nav">
      ${navs.map(n => `<button class="${state.view === n[0] ? 'active' : ''}" onclick="Game.go('${n[0]}')">${n[1]}</button>`).join('')}
    </nav>`;
}

function render() {
  renderHeader();
  if (state && state.view !== 'bridge' && typeof stopBridge === 'function') stopBridge();
  const v = $('#view');
  if (!state) { renderMenu(v); return; }
  if (state.view === 'hq') renderHQ(v);
  else if (state.view === 'fleet') renderFleet(v);
  else if (state.view === 'ops') renderOps(v);
  else if (state.view === 'chests') renderChests(v);
  else if (state.view === 'campaign') renderCampaign(v);
  else if (state.view === 'bridge') renderBridge(v);
  else if (state.view === 'yard') renderYard(v);
  else if (state.view === 'codex') renderCodex(v);
  else if (state.view === 'battle') renderBattle(v);
  else if (state.view === 'result') renderResult(v);
  else { state.view = 'hq'; renderHQ(v); }
}
Game.refresh = render;

/* ---------- menú ---------- */

function renderMenu(v) {
  v.innerHTML = `
    <section class="menu">
      <div class="hero">
        <div class="eyebrow">NEXUS FLEET COMMAND · ARCHIVO NAVAL</div>
        <h1>ACERO <span>Y SAL</span></h1>
        <p class="lead">RPG de combate naval por turnos. Dirige una flota de buques reales, forma oficiales, mejora tus naves y sobrevive a campañas inspiradas en la historia naval.</p>
        <div class="hero-actions">
          ${state ? `<button class="btn primary" onclick="Game.go('hq')">Continuar campaña</button>` : ''}
          <button class="btn ${state ? 'ghost' : 'primary'}" onclick="Game.scrollStarters()">Nueva campaña</button>
          <button class="btn ghost" onclick="Game.howTo()">Cómo se juega</button>
          <button class="btn ghost" onclick="Game.showAccount()">Cuenta / Iniciar sesión</button>
        </div>
        <div class="hero-note">91 buques reales · 10 capítulos · 19 logros · cuentas y cofres</div>
      </div>
      <div class="starter-head" id="starters">
        <h2>Elige tu buque insignia</h2>
        <p>La campaña comienza con un buque y 1.400 créditos. Podrás ampliar la flota en el astillero.</p>
      </div>
      <div class="starter-grid">
        ${STARTERS.map(id => {
          const s = SHIP_MAP[id];
          return `<article class="starter-card">
            ${shipSVG(s.role, 150)}
            <div class="starter-body">
              <h3>${s.name}</h3>
              ${tagList(s)}
              <p>${s.history}</p>
              <div class="mini-stats">${miniStats(s)}</div>
              <button class="btn primary full" onclick="Game.newGame('${s.id}')">Zarpar con este buque</button>
            </div>
          </article>`;
        }).join('')}
      </div>
    </section>`;
}

/* ---------- cuartel general ---------- */

const SKILL_DEFS = [
  { key: 'artilleria', name: 'Artillería', desc: 'Daño de cañón +2% por rango.' },
  { key: 'navegacion', name: 'Navegación', desc: 'Evasión +1,5 y puntería +0,4% por rango.' },
  { key: 'ingenieria', name: 'Ingeniería', desc: 'Reparaciones de emergencia +6% por rango.' },
  { key: 'liderazgo', name: 'Liderazgo', desc: 'Daño recibido −1,5% por rango.' },
  { key: 'tactica', name: 'Táctica', desc: 'Probabilidad de crítico +1,2% e iniciativa por rango.' },
  { key: 'logistica', name: 'Logística', desc: 'Créditos de operaciones +5% por rango.' },
  { key: 'inteligencia', name: 'Inteligencia', desc: 'Experiencia obtenida +3% por rango.' }
];

function renderHQ(v) {
  const cm = state.commander;
  const need = xpNeedCommander(cm.level);
  const xpPct = clamp(Math.round(cm.xp / need * 100), 0, 100);

  v.innerHTML = `
    <section class="screen">
      <div class="screen-head">
        <div><div class="eyebrow">ESTADO MAYOR</div><h2>Mando de la flota</h2></div>
        <div class="head-actions">
          <button class="btn ghost" onclick="Game.howTo()">Manual</button>
          <button class="btn danger ghost" onclick="Game.reset()">Reiniciar</button>
        </div>
      </div>
      <div class="hq-grid">
        <article class="panel commander">
          <div class="panel-head"><h3>Comandante</h3><span class="badge">NIVEL ${cm.level}</span></div>
          <div class="xp-block">
            <div class="bar"><i style="width:${xpPct}%"></i></div>
            <span>${fmt(cm.xp)} / ${fmt(need)} XP</span>
          </div>
          <div class="cmd-stats">
            <div><span>Puntos de habilidad</span><strong>${cm.points}</strong></div>
            <div><span>Buques activos</span><strong>${activeShips().length}/${slots()}</strong></div>
            <div><span>Operaciones ganadas</span><strong>${state.missionsWon}</strong></div>
            <div><span>Campaña</span><strong>${typeof campaignCount === 'function' ? campaignCount(state) : 0}/${typeof CAMPAIGN !== 'undefined' ? CAMPAIGN.length : 0}</strong></div>
            <div><span>Oficiales contratados</span><strong>${state.officers.length}/${OFFICERS.length}</strong></div>
          </div>
          <p class="lore">Tu misión: mantener abiertas las rutas marítimas y neutralizar cualquier amenaza en el teatro de operaciones. Cada victoria acerca a tu flota a la supremacía naval.</p>
        </article>
        <article class="panel skills">
          <div class="panel-head"><h3>Habilidades del comandante</h3><span class="badge">${cm.points} PUNTOS</span></div>
          ${SKILL_DEFS.map(s => {
            const rank = cm.skills[s.key];
            return `<div class="skill-row">
              <div class="skill-info"><strong>${s.name}</strong><span>${s.desc}</span></div>
              <div class="skill-rank">
                <div class="pips">${pips(rank, 10)}</div>
                <span>${rank}/10</span>
                <button class="btn small" ${cm.points <= 0 || rank >= 10 ? 'disabled' : ''} onclick="Game.upSkill('${s.key}')">+</button>
              </div>
            </div>`;
          }).join('')}
        </article>
      </div>
      <article class="panel achievements">
        <div class="panel-head"><h3>Logros</h3><span class="badge">${state.achievements.length}/${ACHIEVEMENTS.length}</span></div>
        <div class="ach-grid">
          ${ACHIEVEMENTS.map(function (a) {
            const on = state.achievements.indexOf(a.id) !== -1;
            return '<div class="ach ' + (on ? 'on' : '') + '"><div class="ach-badge">' + (on ? '✓' : '·') + '</div>' +
              '<div class="ach-text"><strong>' + a.name + '</strong><span>' + a.desc + '</span>' +
              '<small>+' + fmt(a.reward.credits) + ' cr · +' + fmt(a.reward.xp) + ' XP</small></div></div>';
          }).join('')}
        </div>
      </article>
      <div class="quick-actions">
        <button class="btn primary" onclick="Game.go('ops')">Ir a operaciones</button>
        <button class="btn ghost" onclick="Game.go('chests')">Abrir baúles</button>
        <button class="btn ghost" onclick="Game.go('campaign')">Campaña</button>
        <button class="btn ghost" onclick="Game.go('bridge')">Tomar el timón</button>
        <button class="btn ghost" onclick="Game.go('fleet')">Gestionar flota</button>
        <button class="btn ghost" onclick="Game.cloudSync()">Sincronizar nube</button>
        <button class="btn ghost" onclick="window.location.href='nexus/'">Centro Nexus</button>
        <button class="btn ghost" onclick="Game.go('yard')">Astillero</button>
      </div>
    </section>`;
}

/* ---------- flota ---------- */

function renderFleet(v) {
  v.innerHTML = `
    <section class="screen">
      <div class="screen-head">
        <div><div class="eyebrow">DIVISIÓN DE BUQUES</div><h2>Flota</h2></div>
        <div class="head-actions">
          <span class="tag">${activeShips().length}/${slots()} activos</span>
          <button class="btn ghost" onclick="Game.repairAll()">Reparar todo</button>
          <button class="btn primary" onclick="Game.go('yard')">Comprar buques</button>
        </div>
      </div>
      <p class="hint">Activa hasta ${slots()} buques para desplegarlos en operaciones. Los buques en reserva no combaten.</p>
      <div class="fleet-grid">${state.fleet.map(fleetCard).join('')}</div>
    </section>`;
}

function fleetCard(e) {
  const s = SHIP_MAP[e.shipId];
  const max = shipMaxHp(e);
  const hpPct = clamp(Math.round(e.hp / max * 100), 0, 100);
  const need = xpNeedShip(e.level);
  const rCost = repairCost(e);

  return `<article class="ship-card ${e.active ? 'active' : ''}">
    <div class="ship-card-top">
      ${shipSVG(s.role, 110)}
      <div class="ship-id">
        <h3>${s.name}</h3>
        <div class="tags">
          <span class="tag">${SHIP_ROLES[s.role].label}</span>
          <span class="tag">${s.nation}</span>
          <span class="tag">${s.year}</span>
          <span class="tag">Nv. ${e.level}</span>
        </div>
      </div>
      <span class="state ${e.active ? 'on' : 'off'}">${e.active ? 'ACTIVO' : 'RESERVA'}</span>
    </div>
    <div class="hp-line">
      <span>CASCO</span>
      <div class="bar"><i class="${hpPct < 35 ? 'low' : hpPct < 70 ? 'mid' : ''}" style="width:${hpPct}%"></i></div>
      <b>${fmt(Math.round(e.hp))}/${fmt(max)}</b>
    </div>
    <div class="xp-line">
      <span>XP ${fmt(e.xp)}/${fmt(need)}</span>
      <div class="bar thin"><i style="width:${clamp(Math.round(e.xp / need * 100), 0, 100)}%"></i></div>
    </div>
    <div class="stat-grid">${statGrid(s, e)}</div>
    <div class="modules">
      ${['guns', 'armor', 'engine'].map(k => `<div class="mod">
        <span>${MOD_LABEL[k]}</span>
        <div class="pips small">${pips(e.modules[k], 5)}</div>
        <button class="btn tiny" ${e.modules[k] >= 5 ? 'disabled' : ''} onclick="Game.upgrade('${e.uid}','${k}')">
          ${e.modules[k] >= 5 ? 'MAX' : fmt(moduleCost(e, k)) + ' cr'}
        </button>
      </div>`).join('')}
    </div>
    <div class="officer-line">
      <label>Oficial</label>
      <select onchange="Game.assignOfficer('${e.uid}',this.value)">
        <option value="">Sin oficial</option>
        ${state.officers.map(id => {
          const o = OFFICER_MAP[id];
          const taken = state.fleet.some(f => f.officer === id && f.uid !== e.uid);
          return `<option value="${id}" ${e.officer === id ? 'selected' : ''} ${taken ? 'disabled' : ''}>${o.name}${taken ? ' (asignado)' : ''}</option>`;
        }).join('')}
      </select>
    </div>
    <div class="card-actions">
      <button class="btn small ${e.active ? 'ghost' : 'primary'}" onclick="Game.toggleActive('${e.uid}')">${e.active ? 'Pasar a reserva' : 'Activar'}</button>
      <button class="btn small ghost" onclick="Game.repair('${e.uid}')">${rCost > 0 ? 'Reparar ' + fmt(rCost) + ' cr' : 'Casco completo'}</button>
      <button class="btn small ghost" onclick="Game.bridgeWith('${e.uid}')">Tomar el timón</button>
      <button class="btn small ghost" onclick="Game.shipDetails('${s.id}')">Ficha</button>
    </div>
  </article>`;
}

/* ---------- logros ---------- */

function checkAchievements() {
  if (!state) return [];
  state.stats = state.stats || { sunk: 0, specials: 0, bossWins: 0, kills: {} };
  state.stats.kills = state.stats.kills || {};
  state.achievements = state.achievements || [];
  const unlocked = [];
  let changed = true;
  let guard = 0;

  while (changed && guard++ < 10) {
    changed = false;
    for (let i = 0; i < ACHIEVEMENTS.length; i++) {
      const a = ACHIEVEMENTS[i];
      if (state.achievements.indexOf(a.id) !== -1) continue;
      let ok = false;
      try { ok = !!a.check(state); } catch (e) { ok = false; }
      if (!ok) continue;
      state.achievements.push(a.id);
      if (a.reward.credits) state.commander.credits += a.reward.credits;
      if (a.reward.xp && typeof addCommanderXp === 'function') addCommanderXp(a.reward.xp);
      if (a.reward.chest && typeof CHEST_MAP !== 'undefined' && CHEST_MAP[a.reward.chest]) {
        state.chests = state.chests || { bronze: 0, silver: 0, gold: 0, legendary: 0 };
        state.chests[a.reward.chest] = (state.chests[a.reward.chest] || 0) + 1;
      }
      unlocked.push(a);
      changed = true;
    }
  }

  if (unlocked.length) {
    save();
    if (typeof renderHeader === 'function') renderHeader();
  }
  return unlocked;
}
window.checkAchievements = checkAchievements;

/* ---------- acciones ---------- */

Game.go = function (view) {
  if (!state) { render(); return; }
  if (battle && !battle.over && view !== 'battle') {
    if (!confirm('Si sales ahora abandonarás el combate en curso. ¿Continuar?')) return;
    battle = null;
  }
  if (view !== 'bridge' && typeof stopBridge === 'function') stopBridge();
  if (view === 'ops') ensureOps();
  state.view = view;
  save();
  render();
};

Game.newGame = function (starterId) {
  if (state && !confirm('Ya hay una campaña guardada. Se reemplazará. ¿Continuar?')) return;
  state = {
    version: 1,
    commander: {
      level: 1, xp: 0, credits: 1400, points: 2,
      skills: { artilleria: 0, navegacion: 0, ingenieria: 0, liderazgo: 0, tactica: 0, logistica: 0, inteligencia: 0 }
    },
    fleet: [makeEntry(starterId, true)],
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
  save();
  tapSound();
  toast('Campaña iniciada. Bienvenido a bordo, comandante.');
  render();
};

Game.scrollStarters = function () {
  const el = $('#starters');
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

Game.toggleSound = function () {
  soundOn = !soundOn;
  try { localStorage.setItem(SOUND_KEY, soundOn ? 'on' : 'off'); } catch (e) { /* sin almacenamiento */ }
  if (soundOn) sfx('tap');
  renderHeader();
};

Game.upSkill = function (key) {
  const cm = state.commander;
  if (cm.points <= 0 || cm.skills[key] >= 10) return;
  cm.points--;
  cm.skills[key]++;
  tapSound();
  checkAchievements();
  save();
  render();
};

Game.upgrade = function (uid, key) {
  const e = state.fleet.find(x => x.uid === uid);
  if (!e || e.modules[key] >= 5) return;
  const cost = moduleCost(e, key);
  if (state.commander.credits < cost) { toast('Créditos insuficientes.'); return; }
  state.commander.credits -= cost;
  e.modules[key]++;
  tapSound();
  checkAchievements();
  save();
  render();
  toast(MOD_LABEL[key] + ' mejorado a nivel ' + e.modules[key] + '.');
};

Game.toggleActive = function (uid) {
  const e = state.fleet.find(x => x.uid === uid);
  if (!e) return;
  if (e.active) {
    e.active = false;
  } else {
    if (activeShips().length >= slots()) {
      toast('Solo puedes tener ' + slots() + ' buques activos. Sube de nivel o pasa otro a reserva.');
      return;
    }
    e.active = true;
  }
  tapSound();
  save();
  render();
};

Game.assignOfficer = function (uid, officerId) {
  const e = state.fleet.find(x => x.uid === uid);
  if (!e) return;
  if (officerId) {
    state.fleet.forEach(f => {
      if (f.uid !== uid && f.officer === officerId) f.officer = null;
    });
  }
  e.officer = officerId || null;
  save();
  render();
};

Game.repair = function (uid) {
  const e = state.fleet.find(x => x.uid === uid);
  if (!e) return;
  const cost = repairCost(e);
  if (cost <= 0) { toast('El casco ya está completo.'); return; }
  if (state.commander.credits < cost) { toast('Créditos insuficientes para reparar.'); return; }
  state.commander.credits -= cost;
  e.hp = shipMaxHp(e);
  tapSound();
  save();
  render();
  toast(SHIP_MAP[e.shipId].name + ' reparado.');
};

Game.repairAll = function () {
  let total = 0;
  state.fleet.forEach(e => { total += repairCost(e); });
  if (total <= 0) { toast('Toda la flota está intacta.'); return; }
  if (state.commander.credits < total) { toast('Necesitas ' + fmt(total) + ' créditos para reparar todo.'); return; }
  state.commander.credits -= total;
  state.fleet.forEach(e => { e.hp = shipMaxHp(e); });
  tapSound();
  save();
  render();
  toast('Flota reparada por ' + fmt(total) + ' créditos.');
};

Game.buyShip = function (id) {
  const s = SHIP_MAP[id];
  if (s.exclusive) { toast('Ese buque es exclusivo: solo se obtiene en cofres.'); return; }
  if (state.fleet.some(e => e.shipId === id)) { toast('Ya tienes este buque.'); return; }
  if (state.commander.level < s.unlockLevel) { toast('Requiere nivel ' + s.unlockLevel + '.'); return; }
  if (state.commander.credits < s.cost) { toast('Créditos insuficientes.'); return; }
  state.commander.credits -= s.cost;
  state.fleet.push(makeEntry(id, activeShips().length < slots()));
  tapSound();
  checkAchievements();
  save();
  render();
  toast(s.name + ' se une a la flota.');
};

Game.buyOfficer = function (id) {
  const o = OFFICER_MAP[id];
  if (state.officers.indexOf(id) !== -1) { toast('Ya contrataste a este oficial.'); return; }
  if (state.commander.level < o.unlockLevel) { toast('Requiere nivel ' + o.unlockLevel + '.'); return; }
  if (state.commander.credits < o.cost) { toast('Créditos insuficientes.'); return; }
  state.commander.credits -= o.cost;
  state.officers.push(id);
  tapSound();
  checkAchievements();
  save();
  render();
  toast(o.name + ' se incorpora a tu estado mayor.');
};

Game.regenOps = function () {
  state.ops = [];
  ensureOps();
  save();
  render();
  toast('Se han generado nuevas operaciones.');
};

Game.reset = function () {
  if (!confirm('¿Reiniciar la campaña? Se perderá todo el progreso.')) return;
  try { localStorage.removeItem(SAVE_KEY); } catch (e) { /* sin almacenamiento */ }
  if (typeof deleteCloudSave === 'function') deleteCloudSave();
  state = null;
  battle = null;
  render();
};

/* ---------- cuenta ---------- */

function showAuthError(message) {
  const box = $('#authError');
  if (box) {
    box.textContent = message;
    box.className = 'auth-error';
    box.classList.remove('hidden');
  } else {
    toast(message);
  }
}

function showAuthInfo(message) {
  const box = $('#authError');
  if (box) {
    box.textContent = message;
    box.className = 'auth-error success';
    box.classList.remove('hidden');
  } else {
    toast(message);
  }
}

Game.showAccount = function () {
  const cloud = window.GameCloud;
  const user = cloud ? cloud.user : null;

  if (user && !user.isAnonymous) {
    Game.modal(`
      <div class="modal-head">
        <div><div class="eyebrow">CUENTA</div><h2>${user.email || 'Sesión iniciada'}</h2></div>
        <button class="modal-close" onclick="Game.closeModal()">×</button>
      </div>
      <p class="account-lead">Tu progreso se guarda en Firebase y se sincroniza en los dispositivos donde inicies sesión con esta cuenta.</p>
      <div class="account-uid"><span>UID</span><code>${cloud.uid || '—'}</code></div>
      <div class="modal-actions">
        <button class="btn primary" onclick="Game.cloudSync()">Sincronizar ahora</button>
        <button class="btn ghost" onclick="window.location.href='nexus/'">Centro Nexus</button>
        <button class="btn danger" onclick="Game.authLogout()">Cerrar sesión</button>
      </div>
    `);
    return;
  }

  const ready = !!(cloud && cloud.ready);
  Game.modal(`
    <div class="modal-head">
      <div><div class="eyebrow">CUENTA</div><h2>Iniciar sesión o crear cuenta</h2></div>
      <button class="modal-close" onclick="Game.closeModal()">×</button>
    </div>
    <p class="account-lead">Estás jugando como <strong>invitado</strong>. Crea una cuenta para conservar tu progreso actual y recuperarlo en otros dispositivos. Si inicias sesión en una cuenta existente, se cargará la partida de esa cuenta.</p>
    <div class="auth-form">
      <label>Email<input id="authEmail" type="email" autocomplete="email" placeholder="tu@email.com"/></label>
      <label>Contraseña<input id="authPass" type="password" autocomplete="current-password" placeholder="Mínimo 6 caracteres"/></label>
      <div id="authError" class="auth-error hidden"></div>
      <div class="modal-actions">
        <button class="btn primary" ${ready ? '' : 'disabled'} onclick="Game.authLogin()">Iniciar sesión</button>
        <button class="btn ghost" ${ready ? '' : 'disabled'} onclick="Game.authRegister()">Crear cuenta y conservar progreso</button>
        <button class="btn ghost" onclick="Game.closeModal()">Seguir como invitado</button>
      </div>
      <button class="link-btn" ${ready ? '' : 'disabled'} onclick="Game.authReset()">¿Olvidaste tu contraseña?</button>
    </div>
    ${ready ? '' : '<p class="tiny">Conectando con Firebase…</p>'}
  `);
};

Game.authLogin = function () {
  if (!window.cloudLogin) { showAuthError('La nube aún no está conectada.'); return; }
  const email = $('#authEmail') ? $('#authEmail').value.trim() : '';
  const pass = $('#authPass') ? $('#authPass').value : '';
  if (!email || email.indexOf('@') === -1) { showAuthError('Introduce un email válido.'); return; }
  if (pass.length < 6) { showAuthError('La contraseña debe tener al menos 6 caracteres.'); return; }
  window.cloudLogin(email, pass).then(function () {
    Game.closeModal();
    toast('Sesión iniciada. Partida sincronizada.');
    render();
  }).catch(function (e) {
    showAuthError(window.authErrorMessage ? window.authErrorMessage(e) : (e.message || 'Error'));
  });
};

Game.authRegister = function () {
  if (!window.cloudRegister) { showAuthError('La nube aún no está conectada.'); return; }
  const email = $('#authEmail') ? $('#authEmail').value.trim() : '';
  const pass = $('#authPass') ? $('#authPass').value : '';
  if (!email || email.indexOf('@') === -1) { showAuthError('Introduce un email válido.'); return; }
  if (pass.length < 6) { showAuthError('La contraseña debe tener al menos 6 caracteres.'); return; }
  window.cloudRegister(email, pass).then(function () {
    Game.closeModal();
    toast('Cuenta creada. Tu progreso queda vinculado a ' + email + '.');
    render();
  }).catch(function (e) {
    showAuthError(window.authErrorMessage ? window.authErrorMessage(e) : (e.message || 'Error'));
  });
};

Game.authLogout = function () {
  if (!window.cloudLogout) { toast('La nube aún no está conectada.'); return; }
  if (!confirm('¿Cerrar sesión? Tu partida quedará guardada en Firebase.')) return;
  window.cloudLogout().then(function () {
    Game.closeModal();
    toast('Sesión cerrada. Ahora juegas como invitado.');
    render();
  }).catch(function (e) {
    toast(window.authErrorMessage ? window.authErrorMessage(e) : (e.message || 'No se pudo cerrar sesión.'));
  });
};

Game.authReset = function () {
  if (!window.cloudResetPassword) { showAuthError('La nube aún no está conectada.'); return; }
  const email = $('#authEmail') ? $('#authEmail').value.trim() : '';
  if (!email || email.indexOf('@') === -1) { showAuthError('Introduce tu email para restablecer la contraseña.'); return; }
  window.cloudResetPassword(email).then(function () {
    showAuthInfo('Si el email está registrado, recibirás un enlace para restablecer la contraseña.');
  }).catch(function (e) {
    showAuthError(window.authErrorMessage ? window.authErrorMessage(e) : (e.message || 'No se pudo enviar el correo.'));
  });
};

/* ---------- modales ---------- */

Game.modal = function (html) {
  $('#modalCard').innerHTML = html;
  $('#modal').classList.remove('hidden');
};

Game.closeModal = function () {
  $('#modal').classList.add('hidden');
};

Game.shipDetails = function (id) {
  const s = SHIP_MAP[id];
  const sp = SHIP_ROLES[s.role].special;
  Game.modal(`
    <div class="modal-head">
      <div><div class="eyebrow">FICHA DE BUQUE</div><h2>${s.name}</h2></div>
      <button class="modal-close" onclick="Game.closeModal()">×</button>
    </div>
    <div class="modal-hero">${shipSVG(s.role, 280)}${tagList(s)}</div>
    <div class="detail-grid">
      <div><span>Clase</span><strong>${SHIP_ROLES[s.role].label}</strong></div>
      <div><span>País</span><strong>${s.nation}</strong></div>
      <div><span>Año</span><strong>${s.year}</strong></div>
      <div><span>Eslora</span><strong>${s.length}</strong></div>
      <div><span>Desplazamiento</span><strong>${s.displacement}</strong></div>
      <div><span>Tripulación</span><strong>${s.crew}</strong></div>
    </div>
    <div class="modal-stats">${statGrid(s)}</div>
    <p class="armament"><strong>Armamento:</strong> ${s.armament}</p>
    <p class="history">${s.history}</p>
    <div class="special-box"><strong>${sp.name}</strong><p>${sp.desc} Recarga: ${sp.cd} turnos.</p></div>
  `);
};

Game.howTo = function () {
  Game.modal(`
    <div class="modal-head">
      <div><div class="eyebrow">MANUAL DE CAMPAÑA</div><h2>Cómo se juega</h2></div>
      <button class="modal-close" onclick="Game.closeModal()">×</button>
    </div>
    <div class="manual">
      <h3>Objetivo</h3>
      <p>Dirige una flota histórica, gana operaciones y sube de nivel. Cada victoria otorga créditos y experiencia para el comandante y los buques.</p>
      <h3>Flota</h3>
      <p>Empiezas con un buque insignia. En el Astillero puedes comprar más unidades reales. Los espacios activos aumentan con tu nivel (1 al inicio, hasta 4).</p>
      <h3>Combate</h3>
      <p>El orden de turno depende de la velocidad y la táctica. En tu turno elige cañoneo, torpedos, maniobra evasiva, reparación o la habilidad especial del buque. Los submarinos pueden sumergirse; los portaaviones atacan a toda la flota enemiga.</p>
      <h3>Progresión</h3>
      <p>Invierte puntos en cinco habilidades del comandante. Mejora cañones, blindaje y motores de cada buque. Contrata oficiales y asígnalos desde la pantalla Flota para obtener bonus permanentes.</p>
      <h3>Consejos</h3>
      <p>Repara la flota entre misiones. Usa la maniobra evasiva contra acorazados lentos. Los torpedos ignoran parte del blindaje, pero son menos precisos. Guarda créditos para reparaciones después de una derrota.</p>
    </div>
  `);
};
