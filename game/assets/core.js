'use strict';

const SAVE_KEY = 'acero-y-sal-v1';
const SOUND_KEY = 'acero-y-sal-sound';

let state = null;
let battle = null;
let soundOn = true;
try { soundOn = localStorage.getItem(SOUND_KEY) !== 'off'; } catch (e) { /* almacenamiento bloqueado */ }
let audioCtx = null;
let toastTimer = null;

const Game = {};
window.Game = Game;

const MOD_LABEL = { guns: 'Cañones', armor: 'Blindaje', engine: 'Motores' };
const ROLE_COLOR = {
  battleship: '#8ab4ff',
  carrier: '#6ee7b7',
  cruiser: '#f3b35b',
  destroyer: '#f472b6',
  submarine: '#b39cff',
  torpedo: '#ff7b7b',
  ironclad: '#9fb0c4',
  frigate: '#d9b982'
};

/* ---------- utilidades ---------- */

function $(sel, root) { return (root || document).querySelector(sel); }
function rng() { return Math.random(); }
function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function rand(a, b) { return a + Math.random() * (b - a); }
function pick(list) { return list[Math.floor(Math.random() * list.length)]; }
function fmt(n) { return Number(n).toLocaleString('es-ES'); }

function shuffle(list) {
  const a = list.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const t = a[i]; a[i] = a[j]; a[j] = t;
  }
  return a;
}

function sfx(kind) {
  if (!soundOn) return;
  try {
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    const t = audioCtx.currentTime;
    const o = audioCtx.createOscillator();
    const g = audioCtx.createGain();
    o.connect(g);
    g.connect(audioCtx.destination);
    if (kind === 'fire') {
      o.type = 'sawtooth';
      o.frequency.setValueAtTime(170, t);
      o.frequency.exponentialRampToValueAtTime(42, t + 0.25);
      g.gain.setValueAtTime(0.05, t);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.3);
      o.start(t); o.stop(t + 0.3);
    } else if (kind === 'hit') {
      o.type = 'square';
      o.frequency.setValueAtTime(95, t);
      o.frequency.exponentialRampToValueAtTime(28, t + 0.18);
      g.gain.setValueAtTime(0.05, t);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.2);
      o.start(t); o.stop(t + 0.2);
    } else {
      o.type = 'triangle';
      o.frequency.setValueAtTime(520, t);
      o.frequency.exponentialRampToValueAtTime(320, t + 0.12);
      g.gain.setValueAtTime(0.035, t);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.15);
      o.start(t); o.stop(t + 0.15);
    }
  } catch (e) { /* audio no disponible */ }
}

function tapSound() { sfx('tap'); }

function toast(msg) {
  const t = $('#toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(function () { t.classList.remove('show'); }, 2800);
}

/* ---------- estado ---------- */

function makeEntry(shipId, active) {
  const entry = {
    uid: 's' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7),
    shipId: shipId,
    level: 1,
    xp: 0,
    modules: { guns: 0, armor: 0, engine: 0 },
    officer: null,
    active: !!active,
    hp: 0
  };
  entry.hp = shipMaxHp(entry);
  return entry;
}

function shipMaxHp(entry) {
  const ship = SHIP_MAP[entry.shipId];
  return Math.round(ship.stats.hp * (1 + 0.06 * (entry.level - 1)));
}

function slots() {
  return clamp(1 + Math.floor(state.commander.level / 3), 1, 4);
}

function activeShips() {
  return state.fleet.filter(function (e) { return e.active; }).slice(0, slots());
}

function xpNeedCommander(level) { return 100 + level * 80; }
function xpNeedShip(level) { return 70 + level * 55; }

function moduleCost(entry, key) {
  const ship = SHIP_MAP[entry.shipId];
  return Math.round(ship.cost * 0.08 * Math.pow(1.65, entry.modules[key]));
}

function repairCost(entry) {
  const max = shipMaxHp(entry);
  const missing = Math.max(0, max - entry.hp);
  if (missing <= 0) return 0;
  return Math.ceil(missing * (0.45 + SHIP_MAP[entry.shipId].tier * 0.3));
}

function save() {
  try { localStorage.setItem(SAVE_KEY, JSON.stringify(state)); } catch (e) { /* sin almacenamiento */ }
}

function load() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return null;
    const s = JSON.parse(raw);
    if (!s || !s.commander || !Array.isArray(s.fleet) || !s.fleet.length) return null;
    s.officers = s.officers || [];
    s.ops = s.ops || [];
    s.missionsWon = s.missionsWon || 0;
    s.commander.skills = Object.assign(
      { artilleria: 0, navegacion: 0, ingenieria: 0, liderazgo: 0, tactica: 0 },
      s.commander.skills || {}
    );
    s.fleet.forEach(function (e) {
      e.modules = Object.assign({ guns: 0, armor: 0, engine: 0 }, e.modules || {});
      if (e.level == null) e.level = 1;
      if (e.xp == null) e.xp = 0;
      if (e.hp == null) e.hp = shipMaxHp(e);
      if (e.active == null) e.active = true;
    });
    return s;
  } catch (e) { return null; }
}

/* ---------- estadísticas ---------- */

function statsFor(ship, opts) {
  const entry = opts.entry;
  const level = opts.level;
  const side = opts.side;
  const scale = opts.scale || 1;
  const lvlMul = 1 + 0.05 * (level - 1);
  const mods = entry ? entry.modules : { guns: 0, armor: 0, engine: 0 };

  let fp = ship.stats.firepower * (1 + 0.09 * mods.guns) * lvlMul;
  let torp = ship.stats.torpedo * (1 + 0.07 * mods.guns) * lvlMul;
  let armor = ship.stats.armor * (1 + 0.09 * mods.armor) * lvlMul;
  const speed = ship.stats.speed * (1 + 0.04 * mods.engine);
  let evade = ship.stats.evade + mods.engine * 2;
  let acc = 0;
  let crit = 0.05;
  let repairMul = 1;
  let damageMul = 1;

  if (side === 'player') {
    const sk = state.commander.skills;
    damageMul *= 1 + 0.02 * sk.artilleria;
    evade += 1.5 * sk.navegacion;
    acc += 0.004 * sk.navegacion;
    crit += 0.012 * sk.tactica;
    repairMul *= 1 + 0.06 * sk.ingenieria;
  }

  const officer = entry && entry.officer ? OFFICER_MAP[entry.officer] : null;
  if (officer) {
    if (officer.bonus === 'accuracy') acc += officer.value;
    else if (officer.bonus === 'damage') damageMul *= 1 + officer.value;
    else if (officer.bonus === 'armor') armor *= 1 + officer.value;
    else if (officer.bonus === 'torpedo') torp *= 1 + officer.value;
    else if (officer.bonus === 'repair') repairMul *= 1 + officer.value;
    else if (officer.bonus === 'evade') evade += officer.value * 100;
    else if (officer.bonus === 'crit') crit += officer.value;
  }

  return {
    fp: fp * scale,
    torp: torp * scale,
    armor: armor * scale,
    speed: speed,
    evade: evade,
    acc: acc,
    crit: crit,
    repairMul: repairMul,
    damageMul: damageMul
  };
}

/* ---------- piezas de interfaz ---------- */

function pips(rank, total) {
  let out = '';
  for (let i = 0; i < total; i++) out += '<i class="' + (i < rank ? 'on' : '') + '"></i>';
  return out;
}

function miniStats(s) {
  return '<span>FUEGO <b>' + s.stats.firepower + '</b></span>' +
    '<span>BLINDAJE <b>' + s.stats.armor + '</b></span>' +
    '<span>VELOCIDAD <b>' + s.stats.speed + '</b></span>';
}

function tagList(s) {
  return '<div class="tags"><span class="tag">' + SHIP_ROLES[s.role].label + '</span>' +
    '<span class="tag">' + s.nation + '</span><span class="tag">' + s.year + '</span></div>';
}

function statGrid(s, entry) {
  let fp = s.stats.firepower, armor = s.stats.armor, torp = s.stats.torpedo, evade = s.stats.evade, speed = s.stats.speed;
  if (entry) {
    const st = statsFor(s, { entry: entry, level: entry.level, side: 'player', scale: 1 });
    fp = Math.round(st.fp);
    armor = Math.round(st.armor);
    torp = Math.round(st.torp);
    evade = Math.round(st.evade);
    speed = Math.round(st.speed);
  }
  return '<span>Fuego<b>' + fp + '</b></span>' +
    '<span>Blindaje<b>' + armor + '</b></span>' +
    '<span>Torpedo<b>' + torp + '</b></span>' +
    '<span>Evasiva<b>' + evade + '</b></span>' +
    '<span>Velocidad<b>' + speed + ' nudos</b></span>' +
    '<span>AA<b>' + s.stats.aa + '</b></span>';
}

function shipSVG(role, width) {
  const c = ROLE_COLOR[role] || '#8ab4ff';
  const w = width || 120;
  const line = 'stroke="' + c + '" stroke-width="2.4" stroke-linejoin="round"';
  const fill = 'fill="' + c + '" fill-opacity="0.13"';
  let art = '';

  if (role === 'battleship') {
    art = '<path d="M16 54 L184 54 L172 68 L28 68 Z" ' + fill + ' ' + line + '/>' +
      '<path d="M72 40 L128 40 L136 54 L64 54 Z" ' + fill + ' ' + line + '/>' +
      '<rect x="93" y="22" width="14" height="20" ' + fill + ' ' + line + '/>' +
      '<line x1="100" y1="22" x2="100" y2="8" stroke="' + c + '" stroke-width="2"/>' +
      '<rect x="36" y="46" width="22" height="8" ' + fill + ' ' + line + '/>' +
      '<line x1="44" y1="46" x2="34" y2="34" stroke="' + c + '" stroke-width="2"/>' +
      '<line x1="52" y1="46" x2="48" y2="32" stroke="' + c + '" stroke-width="2"/>' +
      '<rect x="142" y="46" width="22" height="8" ' + fill + ' ' + line + '/>' +
      '<line x1="156" y1="46" x2="166" y2="34" stroke="' + c + '" stroke-width="2"/>' +
      '<line x1="148" y1="46" x2="152" y2="32" stroke="' + c + '" stroke-width="2"/>' +
      '<line x1="10" y1="70" x2="190" y2="70" stroke="' + c + '" stroke-width="1" stroke-opacity="0.35"/>';
  } else if (role === 'carrier') {
    art = '<path d="M18 56 L182 56 L170 68 L30 68 Z" ' + fill + ' ' + line + '/>' +
      '<path d="M22 46 L178 46 L182 56 L18 56 Z" fill="' + c + '" fill-opacity="0.26" ' + line + '/>' +
      '<rect x="128" y="30" width="18" height="16" ' + fill + ' ' + line + '/>' +
      '<line x1="137" y1="30" x2="137" y2="16" stroke="' + c + '" stroke-width="2"/>' +
      '<path d="M52 42 l10 0 l-5 -8 z" ' + fill + ' ' + line + '/>' +
      '<path d="M86 42 l10 0 l-5 -8 z" ' + fill + ' ' + line + '/>' +
      '<line x1="10" y1="70" x2="190" y2="70" stroke="' + c + '" stroke-width="1" stroke-opacity="0.35"/>';
  } else if (role === 'cruiser') {
    art = '<path d="M22 56 L178 56 L166 68 L34 68 Z" ' + fill + ' ' + line + '/>' +
      '<path d="M82 42 L120 42 L128 56 L74 56 Z" ' + fill + ' ' + line + '/>' +
      '<rect x="96" y="28" width="12" height="16" ' + fill + ' ' + line + '/>' +
      '<line x1="102" y1="28" x2="102" y2="14" stroke="' + c + '" stroke-width="2"/>' +
      '<rect x="44" y="48" width="18" height="8" ' + fill + ' ' + line + '/>' +
      '<line x1="50" y1="48" x2="40" y2="37" stroke="' + c + '" stroke-width="2"/>' +
      '<rect x="140" y="48" width="18" height="8" ' + fill + ' ' + line + '/>' +
      '<line x1="152" y1="48" x2="162" y2="37" stroke="' + c + '" stroke-width="2"/>' +
      '<line x1="12" y1="70" x2="188" y2="70" stroke="' + c + '" stroke-width="1" stroke-opacity="0.35"/>';
  } else if (role === 'destroyer') {
    art = '<path d="M24 58 L176 58 L164 68 L36 68 Z" ' + fill + ' ' + line + '/>' +
      '<path d="M86 46 L118 46 L124 58 L80 58 Z" ' + fill + ' ' + line + '/>' +
      '<rect x="98" y="34" width="10" height="12" ' + fill + ' ' + line + '/>' +
      '<line x1="103" y1="34" x2="103" y2="22" stroke="' + c + '" stroke-width="2"/>' +
      '<rect x="52" y="50" width="16" height="7" ' + fill + ' ' + line + '/>' +
      '<line x1="57" y1="50" x2="48" y2="40" stroke="' + c + '" stroke-width="2"/>' +
      '<rect x="132" y="50" width="14" height="6" ' + fill + ' ' + line + '/>' +
      '<line x1="12" y1="70" x2="188" y2="70" stroke="' + c + '" stroke-width="1" stroke-opacity="0.35"/>';
  } else if (role === 'submarine') {
    art = '<ellipse cx="100" cy="56" rx="72" ry="12" ' + fill + ' ' + line + '/>' +
      '<rect x="92" y="34" width="16" height="16" ' + fill + ' ' + line + '/>' +
      '<line x1="100" y1="34" x2="100" y2="18" stroke="' + c + '" stroke-width="2"/>' +
      '<line x1="100" y1="18" x2="110" y2="18" stroke="' + c + '" stroke-width="2"/>' +
      '<circle cx="100" cy="56" r="12" fill="none" stroke="' + c + '" stroke-width="2"/>' +
      '<line x1="28" y1="56" x2="172" y2="56" stroke="' + c + '" stroke-width="1" stroke-opacity="0.3"/>' +
      '<line x1="12" y1="72" x2="188" y2="72" stroke="' + c + '" stroke-width="1" stroke-opacity="0.35" stroke-dasharray="4 5"/>';
  } else if (role === 'torpedo') {
    art = '<path d="M42 58 L158 58 L148 68 L52 68 Z" ' + fill + ' ' + line + '/>' +
      '<path d="M88 48 L118 48 L122 58 L84 58 Z" ' + fill + ' ' + line + '/>' +
      '<rect x="98" y="38" width="8" height="10" ' + fill + ' ' + line + '/>' +
      '<line x1="102" y1="38" x2="102" y2="28" stroke="' + c + '" stroke-width="2"/>' +
      '<path d="M44 54 l18 0 l-4 6 l-14 0 z" ' + fill + ' ' + line + '/>' +
      '<path d="M60 54 l18 0 l-4 6 l-14 0 z" ' + fill + ' ' + line + '/>' +
      '<line x1="8" y1="64" x2="38" y2="64" stroke="' + c + '" stroke-width="2" stroke-opacity="0.5"/>' +
      '<line x1="12" y1="70" x2="188" y2="70" stroke="' + c + '" stroke-width="1" stroke-opacity="0.35"/>';
  } else if (role === 'ironclad') {
    art = '<path d="M20 50 L180 50 L166 68 L34 68 Z" ' + fill + ' ' + line + '/>' +
      '<path d="M42 50 L54 36 L146 36 L158 50 Z" ' + fill + ' ' + line + '/>' +
      '<circle cx="100" cy="44" r="14" ' + fill + ' ' + line + '/>' +
      '<line x1="100" y1="44" x2="100" y2="26" stroke="' + c + '" stroke-width="3"/>' +
      '<rect x="130" y="20" width="8" height="18" ' + fill + ' ' + line + '/>' +
      '<circle cx="62" cy="56" r="2" fill="' + c + '"/>' +
      '<circle cx="78" cy="56" r="2" fill="' + c + '"/>' +
      '<circle cx="94" cy="56" r="2" fill="' + c + '"/>' +
      '<circle cx="110" cy="56" r="2" fill="' + c + '"/>' +
      '<line x1="10" y1="70" x2="190" y2="70" stroke="' + c + '" stroke-width="1" stroke-opacity="0.35"/>';
  } else {
    art = '<path d="M34 54 L166 54 L156 68 L44 68 Z" ' + fill + ' ' + line + '/>' +
      '<line x1="66" y1="54" x2="66" y2="16" stroke="' + c + '" stroke-width="2"/>' +
      '<line x1="100" y1="54" x2="100" y2="10" stroke="' + c + '" stroke-width="2"/>' +
      '<line x1="134" y1="54" x2="134" y2="16" stroke="' + c + '" stroke-width="2"/>' +
      '<path d="M66 22 L86 30 L66 40 Z" ' + fill + ' ' + line + '/>' +
      '<path d="M100 16 L122 26 L100 38 Z" ' + fill + ' ' + line + '/>' +
      '<path d="M134 22 L152 30 L134 40 Z" ' + fill + ' ' + line + '/>' +
      '<circle cx="58" cy="60" r="2" fill="' + c + '"/>' +
      '<circle cx="74" cy="60" r="2" fill="' + c + '"/>' +
      '<circle cx="90" cy="60" r="2" fill="' + c + '"/>' +
      '<line x1="10" y1="70" x2="190" y2="70" stroke="' + c + '" stroke-width="1" stroke-opacity="0.35"/>';
  }

  return '<svg class="ship-svg" viewBox="0 0 200 80" width="' + w + '" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + art + '</svg>';
}
