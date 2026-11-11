'use strict';

function chestSVG(type, width) {
  const def = CHEST_MAP[type] || CHESTS[0];
  const c = def.color;
  const w = width || 120;
  return `<svg class="chest-svg" viewBox="0 0 120 96" width="${w}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <rect x="14" y="38" width="92" height="44" rx="8" fill="#0d1927" stroke="${c}" stroke-width="2.5"/>
    <path d="M14 44 Q14 18 60 18 Q106 18 106 44" fill="rgba(255,255,255,0.04)" stroke="${c}" stroke-width="2.5"/>
    <rect x="52" y="42" width="16" height="22" rx="3" fill="${c}" opacity="0.82"/>
    <circle cx="60" cy="52" r="3.2" fill="#0b1420"/>
    <line x1="28" y1="62" x2="92" y2="62" stroke="${c}" stroke-opacity="0.25" stroke-width="2"/>
    <line x1="28" y1="69" x2="92" y2="69" stroke="${c}" stroke-opacity="0.12" stroke-width="2"/>
  </svg>`;
}

function renderChests(v) {
  if (!state) return;
  state.chests = state.chests || { bronze: 0, silver: 0, gold: 0, legendary: 0 };
  const total = totalChests();
  const ownedExclusive = EXCLUSIVE_SHIPS.filter(function (s) {
    return state.fleet.some(function (e) { return e.shipId === s.id; });
  }).length;

  v.innerHTML = `
    <section class="screen">
      <div class="screen-head">
        <div><div class="eyebrow">TESORERÍA NAVAL</div><h2>Baúles</h2></div>
        <div class="head-actions">
          <span class="tag">${total} BAÚLES</span>
          <span class="tag">${ownedExclusive}/${EXCLUSIVE_SHIPS.length} EXCLUSIVOS</span>
        </div>
      </div>
      <p class="hint">Consigue cofres en operaciones, jefes, campaña y logros. Los cofres de plata, oro y legendario pueden contener buques exclusivos que no se venden en el astillero.</p>
      <div class="chest-grid">
        ${CHESTS.map(function (c) {
          const count = state.chests[c.id] || 0;
          const shortNames = { bronze: 'bronce', silver: 'plata', gold: 'oro', legendary: 'legendario' };
          const shortName = shortNames[c.id] || c.name;
          return `<article class="chest-card ${c.id}">
            ${chestSVG(c.id, 130)}
            <div class="chest-card-body">
              <div class="chest-top"><h3>${c.name}</h3><span class="chest-count">${count}</span></div>
              <p>${c.desc}</p>
              <div class="chest-rewards">+${fmt(c.credits[0])}–${fmt(c.credits[1])} créditos${c.exclusiveChance > 0 ? ' · buque exclusivo' : ''}</div>
              <button class="btn ${count > 0 ? 'primary' : 'ghost'} full" ${count > 0 ? '' : 'disabled'} onclick="Game.openChest('${c.id}')">${count > 0 ? 'Abrir ' + shortName : 'Sin cofres'}</button>
            </div>
          </article>`;
        }).join('')}
      </div>
      <h2 class="sub-title">Buques exclusivos</h2>
      <div class="exclusive-grid">
        ${EXCLUSIVE_SHIPS.map(function (s) {
          const owned = state.fleet.some(function (e) { return e.shipId === s.id; });
          return `<article class="exclusive-card ${owned ? 'owned' : ''}" onclick="Game.shipDetails('${s.id}')">
            ${shipSVG(s.role, 120)}
            <h3>${s.name}</h3>
            <div class="tags"><span class="tag">${SHIP_ROLES[s.role].label}</span><span class="tag">${s.year}</span><span class="tag danger">EXCLUSIVO</span></div>
            <span class="exclusive-state ${owned ? 'on' : ''}">${owned ? 'EN TU FLOTA' : 'SOLO EN COFRES'}</span>
          </article>`;
        }).join('')}
      </div>
    </section>`;
}

function grantChest(type, count) {
  if (!CHEST_MAP[type]) return;
  state.chests = state.chests || { bronze: 0, silver: 0, gold: 0, legendary: 0 };
  state.chests[type] = (state.chests[type] || 0) + (count || 1);
}
window.grantChest = grantChest;

Game.openChest = function (type) {
  if (!state || !CHEST_MAP[type]) return;
  state.chests = state.chests || { bronze: 0, silver: 0, gold: 0, legendary: 0 };
  if (!state.chests[type] || state.chests[type] <= 0) {
    toast('No tienes ' + CHEST_MAP[type].name + '.');
    return;
  }

  const def = CHEST_MAP[type];
  state.chests[type]--;
  const rewards = [];
  let credits = Math.floor(rand(def.credits[0], def.credits[1] + 1));
  state.commander.credits += credits;
  rewards.push('+' + fmt(credits) + ' créditos');

  let ship = null;
  const unowned = EXCLUSIVE_SHIPS.filter(function (s) {
    return !state.fleet.some(function (e) { return e.shipId === s.id; });
  });

  if (unowned.length && (def.exclusiveChance >= 1 || Math.random() < def.exclusiveChance)) {
    ship = pick(unowned);
    state.fleet.push(makeEntry(ship.id, activeShips().length < slots()));
    rewards.push('Buque exclusivo: ' + ship.name);
  } else if (unowned.length === 0 && def.exclusiveChance > 0) {
    const extra = def.bonus || 2000;
    state.commander.credits += extra;
    credits += extra;
    rewards.push('Todos los exclusivos ya están en tu flota: +' + fmt(extra) + ' créditos');
  }

  if (def.bonus && ship) {
    state.commander.credits += def.bonus;
    rewards.push('Bonus legendario: +' + fmt(def.bonus) + ' créditos');
  }

  save();
  checkAchievements();
  render();

  Game.modal(`
    <div class="modal-head">
      <div><div class="eyebrow">BAÚL ABIERTO</div><h2>${def.name}</h2></div>
      <button class="modal-close" onclick="Game.closeModal()">×</button>
    </div>
    <div class="chest-reveal">
      ${chestSVG(type, 200)}
      <div class="chest-reward-list">${rewards.map(function (r) { return '<div>' + r + '</div>'; }).join('')}</div>
      <div class="modal-actions">
        <button class="btn primary" ${state.chests[type] > 0 ? '' : 'disabled'} onclick="Game.openChest('${type}')">Abrir otro (${state.chests[type]})</button>
        <button class="btn ghost" onclick="Game.closeModal()">Cerrar</button>
      </div>
    </div>
  `);
};
