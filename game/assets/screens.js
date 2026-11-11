'use strict';

/* ---------- operaciones ---------- */

function ensureOps() {
  if (!state.ops || !state.ops.length || state.ops.every(o => o.done)) {
    state.ops = generateOps();
    return;
  }
  const pending = state.ops.filter(o => !o.done);
  if (pending.length === 1 && pending[0].boss) {
    const fresh = generateOps().filter(o => !o.boss).slice(0, 2);
    state.ops = [pending[0]].concat(fresh);
  }
}

function generateOps() {
  const lvl = state.commander.level;
  const fleetSize = clamp(activeShips().length, 1, 3);
  const templates = shuffle(OPS_TEMPLATES).slice(0, 3);

  const ops = templates.map((t, i) => {
    const opLevel = clamp(lvl + (i === 1 ? 1 : 0) - (i === 2 ? 1 : 0), 1, 12);
    const count = fleetSize;
    const minTier = opLevel <= 8 ? 1 : opLevel <= 10 ? 2 : 3;
    const maxTier = opLevel <= 6 ? 1 : opLevel <= 8 ? 2 : opLevel <= 10 ? 3 : 4;
    const pool = SHIPS.filter(s => !s.exclusive && s.tier >= minTier && s.tier <= maxTier);
    const enemyIds = [];
    for (let k = 0; k < count; k++) {
      const candidates = pool.filter(s => enemyIds.indexOf(s.id) === -1);
      enemyIds.push(pick(candidates.length ? candidates : pool).id);
    }
    const rewardBase = enemyIds.reduce((sum, id) => sum + SHIP_MAP[id].cost, 0);
    return {
      id: 'op' + Date.now().toString(36) + i,
      name: t.name,
      desc: t.desc,
      level: opLevel,
      enemyIds: enemyIds,
      done: false,
      boss: false,
      credits: Math.round(rewardBase * 0.2 + opLevel * 50),
      xp: 60 + opLevel * 35
    };
  });

  if (state.missionsWon > 0 && state.missionsWon % 4 === 0) {
    const bossPool = lvl < 6 ? ['hood'] : lvl < 9 ? ['bismarck', 'enterprise', 'hood'] : ['yamato', 'bismarck', 'enterprise'];
    const bossDef = pick(BOSS_OPS.filter(b => bossPool.indexOf(b.ship) !== -1));
    const bossLevel = clamp(lvl, 3, 12);
    const rewardBase = SHIP_MAP[bossDef.ship].cost;
    ops[2] = {
      id: 'boss' + Date.now().toString(36),
      name: bossDef.name,
      desc: bossDef.desc,
      level: bossLevel,
      enemyIds: [bossDef.ship],
      done: false,
      boss: true,
      credits: Math.round(rewardBase * 0.32 + bossLevel * 80),
      xp: Math.round((60 + bossLevel * 35) * 1.5)
    };
  }

  return ops;
}

function renderOps(v) {
  ensureOps();
  save();
  const active = activeShips();

  v.innerHTML = `
    <section class="screen">
      <div class="screen-head">
        <div><div class="eyebrow">TEATRO DE OPERACIONES</div><h2>Operaciones disponibles</h2></div>
        <div class="head-actions">
          <span class="tag">NIVEL ${state.commander.level}</span>
          <button class="btn ghost" onclick="Game.regenOps()">Nuevas operaciones</button>
        </div>
      </div>
      <div class="fleet-strip">
        ${active.length
          ? active.map(e => `<span class="ship-chip">${SHIP_MAP[e.shipId].name}<b>Nv.${e.level}</b></span>`).join('')
          : '<span class="warn">No hay buques activos. Ve a Flota y activa al menos uno.</span>'}
      </div>
      <div class="ops-grid">${state.ops.map(opCard).join('')}</div>
    </section>`;
}

function opCard(op) {
  const hasFleet = activeShips().length > 0;
  const enemies = op.enemyIds.map(id => {
    const s = SHIP_MAP[id];
    return `<span class="enemy-chip">${s.name}<b>${SHIP_ROLES[s.role].label}</b></span>`;
  }).join('');

  return `<article class="op-card ${op.boss ? 'boss ' : ''}${op.done ? 'done' : ''}">
    <div class="op-top">
      <span class="tag">NIVEL ${op.level}</span>
      ${op.boss ? '<span class="tag danger">ESPECIAL</span>' : ''}
      ${op.done ? '<span class="tag ok">COMPLETADA</span>' : ''}
    </div>
    <h3>${op.name}</h3>
    <p>${op.desc}</p>
    <div class="enemy-list">${enemies}</div>
    <div class="op-rewards"><span>+${fmt(op.credits)} créditos</span><span>+${fmt(op.xp)} XP</span></div>
    <button class="btn ${op.boss ? 'danger' : 'primary'} full" ${op.done || !hasFleet ? 'disabled' : ''} onclick="Game.deploy('${op.id}')">
      ${op.done ? 'Completada' : hasFleet ? 'Desplegar flota' : 'Sin flota activa'}
    </button>
  </article>`;
}

/* ---------- campaña ---------- */

function renderCampaign(v) {
  if (!state) return;
  const cleared = (state.campaign && state.campaign.cleared) ? state.campaign.cleared : {};
  const done = campaignCount(state);
  const active = activeShips();
  const pct = Math.round(done / CAMPAIGN.length * 100);

  v.innerHTML = `
    <section class="screen">
      <div class="screen-head">
        <div><div class="eyebrow">CAMPAÑA HISTÓRICA</div><h2>ACERO FINAL</h2></div>
        <div class="head-actions">
          <span class="tag">${done}/${CAMPAIGN.length} CAPÍTULOS</span>
          <button class="btn ghost" onclick="Game.go('ops')">Operaciones libres</button>
        </div>
      </div>
      <div class="campaign-progress">
        <div class="bar"><i style="width:${pct}%"></i></div>
        <span>${pct}% de la campaña completada</span>
      </div>
      <div class="fleet-strip">
        ${active.length
          ? active.map(e => `<span class="ship-chip">${SHIP_MAP[e.shipId].name}<b>Nv.${e.level}</b></span>`).join('')
          : '<span class="warn">No hay buques activos. Ve a Flota y activa al menos uno.</span>'}
      </div>
      <div class="campaign-grid">${CAMPAIGN.map((c, i) => campaignCard(c, i, cleared)).join('')}</div>
    </section>`;
}

function campaignCard(c, i, cleared) {
  const completed = !!cleared[i];
  const unlocked = typeof campaignUnlocked === 'function' ? campaignUnlocked(i) : i === 0;
  const active = activeShips().length > 0;
  const rw = c.rewards || {};
  const rewards = [];
  if (rw.credits) rewards.push('+' + fmt(rw.credits) + ' créditos');
  if (rw.xp) rewards.push('+' + fmt(rw.xp) + ' XP');
  if (rw.ship && SHIP_MAP[rw.ship]) rewards.push('Buque: ' + SHIP_MAP[rw.ship].name);
  if (rw.officer && OFFICER_MAP[rw.officer]) rewards.push('Oficial: ' + OFFICER_MAP[rw.officer].name);

  const enemies = c.enemyIds.map(function (id) {
    const s = SHIP_MAP[id];
    return `<span class="enemy-chip">${s.name}<b>${SHIP_ROLES[s.role].label}</b></span>`;
  }).join('');

  return `<article class="campaign-card ${completed ? 'done' : ''} ${!unlocked ? 'locked' : ''} ${c.boss ? 'boss' : ''}">
    <div class="camp-top">
      <span class="camp-num">${c.chapter}</span>
      <span class="tag">NIVEL ${c.level}</span>
      ${c.boss ? '<span class="tag danger">ESPECIAL</span>' : ''}
      ${completed ? '<span class="tag ok">COMPLETADO</span>' : ''}
      ${!unlocked ? '<span class="tag">BLOQUEADO</span>' : ''}
    </div>
    <h3>${c.name}</h3>
    <p class="camp-desc">${c.desc}</p>
    <blockquote>${c.narrative}</blockquote>
    <div class="enemy-list">${enemies}</div>
    <div class="camp-rewards">${rewards.join(' · ')}</div>
    <button class="btn ${completed ? 'ghost' : unlocked ? 'primary' : 'ghost'} full" ${completed || !unlocked || !active ? 'disabled' : ''} onclick="Game.startCampaign(${i})">
      ${completed ? 'Completado' : !unlocked ? 'Bloqueado' : active ? 'Iniciar capítulo' : 'Sin flota activa'}
    </button>
  </article>`;
}

/* ---------- astillero ---------- */

function renderYard(v) {
  const owned = {};
  state.fleet.forEach(e => { owned[e.shipId] = true; });

  v.innerHTML = `
    <section class="screen">
      <div class="screen-head">
        <div><div class="eyebrow">ASTILLERO NAVAL</div><h2>Catálogo de buques</h2></div>
        <div class="head-actions"><span class="tag">${fmt(state.commander.credits)} CRÉDITOS</span></div>
      </div>
      <p class="hint">Buques reales de la historia naval. Cada unidad es única: no puedes comprar dos veces el mismo buque.</p>
      ${filterBar('yard')}
      <div class="catalog-grid" id="yardGrid">
        ${SHIPS.filter(s => !s.exclusive).slice().sort((a, b) => a.tier - b.tier || a.cost - b.cost).map(s => {
          const isOwned = !!owned[s.id];
          const locked = state.commander.level < s.unlockLevel;
          const poor = state.commander.credits < s.cost;
          let label = 'Comprar';
          if (isOwned) label = 'En tu flota';
          else if (locked) label = 'Nivel ' + s.unlockLevel;
          else if (poor) label = 'Créditos insuficientes';
          return `<article class="catalog-card ${isOwned ? 'owned' : ''}" data-ship="${s.id}" data-name="${s.name.toLowerCase()}" data-role="${s.role}" data-nation="${s.nation}" data-tier="${s.tier}">
            ${shipSVG(s.role, 120)}
            <div class="catalog-body">
              <div class="catalog-top"><h3>${s.name}</h3><span class="tag">T${s.tier}</span></div>
              ${tagList(s)}
              <div class="mini-stats">${miniStats(s)}</div>
              <div class="price-row">
                <span class="price">${fmt(s.cost)} cr</span>
                <button class="btn small ${isOwned ? 'ghost' : 'primary'}" ${isOwned || locked || poor ? 'disabled' : ''} onclick="Game.buyShip('${s.id}')">${label}</button>
              </div>
              <button class="link-btn" onclick="Game.shipDetails('${s.id}')">Ver ficha histórica</button>
            </div>
          </article>`;
        }).join('')}
      </div>
      <h2 class="sub-title">Oficiales</h2>
      <p class="hint">Asigna un oficial a cada buque desde la pantalla Flota. Sus bonus son permanentes mientras esté embarcado.</p>
      <div class="officers-grid">
        ${OFFICERS.map(o => {
          const isOwned = state.officers.indexOf(o.id) !== -1;
          const locked = state.commander.level < o.unlockLevel;
          const poor = state.commander.credits < o.cost;
          let label = 'Contratar';
          if (isOwned) label = 'Contratado';
          else if (locked) label = 'Nivel ' + o.unlockLevel;
          else if (poor) label = 'Créditos insuficientes';
          return `<article class="officer-card ${isOwned ? 'owned' : ''}">
            <div class="officer-avatar">${o.name.split(' ').map(p => p[0]).join('').slice(0, 2)}</div>
            <div class="officer-body">
              <h3>${o.name}</h3>
              <span class="officer-title">${o.title}</span>
              <p>${o.desc}</p>
              <div class="price-row">
                <span class="price">${fmt(o.cost)} cr</span>
                <button class="btn small ${isOwned ? 'ghost' : 'primary'}" ${isOwned || locked || poor ? 'disabled' : ''} onclick="Game.buyOfficer('${o.id}')">${label}</button>
              </div>
            </div>
          </article>`;
        }).join('')}
      </div>
    </section>`;
}

/* ---------- filtros ---------- */

function filterBar(prefix) {
  const nations = Array.from(new Set(SHIPS.map(s => s.nation))).sort();
  return `<div class="filter-bar">
    <input class="filter-input" id="${prefix}Search" placeholder="Buscar buque…" oninput="Game.filterShips('${prefix}')"/>
    <select class="filter-select" id="${prefix}Role" onchange="Game.filterShips('${prefix}')">
      <option value="">Todos los roles</option>
      ${Object.keys(SHIP_ROLES).map(r => `<option value="${r}">${SHIP_ROLES[r].label}</option>`).join('')}
    </select>
    <select class="filter-select" id="${prefix}Nation" onchange="Game.filterShips('${prefix}')">
      <option value="">Todas las naciones</option>
      ${nations.map(n => `<option value="${n}">${n}</option>`).join('')}
    </select>
    <select class="filter-select" id="${prefix}Tier" onchange="Game.filterShips('${prefix}')">
      <option value="">Todos los niveles</option>
      <option value="1">Tier 1</option>
      <option value="2">Tier 2</option>
      <option value="3">Tier 3</option>
      <option value="4">Tier 4</option>
    </select>
    <button class="btn tiny ghost" onclick="Game.resetFilters('${prefix}')">Limpiar</button>
    <span class="filter-count" id="${prefix}Count"></span>
  </div>`;
}

Game.filterShips = function (prefix) {
  const grid = $('#' + prefix + 'Grid');
  if (!grid) return;
  const search = $('#' + prefix + 'Search');
  const role = $('#' + prefix + 'Role');
  const nation = $('#' + prefix + 'Nation');
  const tier = $('#' + prefix + 'Tier');
  const norm = function (value) {
    const s = String(value || '').toLowerCase();
    return s.normalize ? s.normalize('NFD').replace(/[\u0300-\u036f]/g, '') : s;
  };
  const q = search ? norm(search.value.trim()) : '';
  const r = role ? role.value : '';
  const n = nation ? nation.value : '';
  const t = tier ? tier.value : '';
  const cards = grid.querySelectorAll('[data-ship]');
  let shown = 0;

  cards.forEach(function (card) {
    const ok = (!q || norm(card.getAttribute('data-name')).indexOf(q) !== -1) &&
      (!r || card.getAttribute('data-role') === r) &&
      (!n || card.getAttribute('data-nation') === n) &&
      (!t || card.getAttribute('data-tier') === t);
    card.classList.toggle('filtered-out', !ok);
    if (ok) shown++;
  });

  const count = $('#' + prefix + 'Count');
  if (count) count.textContent = shown + (shown === 1 ? ' buque' : ' buques');
};

Game.resetFilters = function (prefix) {
  ['Search', 'Role', 'Nation', 'Tier'].forEach(function (suffix) {
    const el = $('#' + prefix + suffix);
    if (el) el.value = '';
  });
  Game.filterShips(prefix);
};

function renderCodex(v) {
  v.innerHTML = `
    <section class="screen">
      <div class="screen-head">
        <div><div class="eyebrow">ARCHIVO HISTÓRICO</div><h2>Códice de buques</h2></div>
        <div class="head-actions"><span class="tag">${SHIPS.length} BUQUES REALES</span></div>
      </div>
      <p class="hint">Datos históricos aproximados. Los valores de combate son una abstracción jugable basada en sus características reales.</p>
      ${filterBar('codex')}
      <div class="codex-grid" id="codexGrid">
        ${SHIPS.map(s => `<article class="codex-card" data-ship="${s.id}" data-name="${s.name.toLowerCase()}" data-role="${s.role}" data-nation="${s.nation}" data-tier="${s.tier}" onclick="Game.shipDetails('${s.id}')">
          ${shipSVG(s.role, 130)}
          <h3>${s.name}</h3>
          <div class="tags"><span class="tag">${SHIP_ROLES[s.role].label}</span><span class="tag">${s.year}</span>${s.exclusive ? '<span class="tag danger">EXCLUSIVO</span>' : ''}</div>
          <p>${s.history.slice(0, 108)}…</p>
          <span class="link">Ver ficha</span>
        </article>`).join('')}
      </div>
    </section>`;
}
