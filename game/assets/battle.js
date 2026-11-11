'use strict';

/* ---------- construcción del combate ---------- */

function enemyScale(op) {
  return 0.9 + 0.05 * (op.level - 1) + (op.boss ? 0.15 : 0);
}

function makeCombatant(side, idx, shipId, opts) {
  const ship = SHIP_MAP[shipId];
  const entry = opts.entry || null;
  const level = entry ? entry.level : (opts.level || 1);
  const scale = opts.scale || 1;
  const statLevel = entry ? level : 1;
  const stats = statsFor(ship, { entry: entry, level: statLevel, side: side, scale: scale });
  const maxHp = entry ? shipMaxHp(entry) : Math.round(ship.stats.hp * scale);
  const hp = entry ? clamp(entry.hp, 0, maxHp) : maxHp;

  return {
    key: side + idx,
    side: side,
    idx: idx,
    ship: ship,
    entry: entry,
    level: level,
    stats: stats,
    maxHp: maxHp,
    hp: hp,
    alive: hp > 0,
    status: { burn: 0, speedDown: 0, evade: 0, smoke: 0, dive: 0, nextCrit: false },
    cd: 0,
    torpCd: 0,
    repaired: false
  };
}

function blog(text, cls) {
  if (!battle) return;
  battle.log.push({ text: text, cls: cls || '' });
  if (battle.log.length > 70) battle.log.shift();
}

function combatantByKey(key) {
  if (!battle) return null;
  const all = battle.player.concat(battle.enemy);
  for (let i = 0; i < all.length; i++) if (all[i].key === key) return all[i];
  return null;
}

function buildQueue() {
  const all = battle.player.concat(battle.enemy).filter(c => c.alive);
  return all.map(c => ({
    c: c,
    init: c.stats.speed + rand(0, 6) + (c.side === 'player' ? state.commander.skills.tactica * 0.6 : 0)
  })).sort((a, b) => b.init - a.init).map(x => x.c.key);
}

function checkKill(c) {
  if (c.hp <= 0 && c.alive) {
    c.hp = 0;
    c.alive = false;
    blog(c.ship.name + ' se hunde.', 'kill');
    sfx('hit');
    if (typeof state !== 'undefined' && state && c.side === 'enemy') {
      state.stats = state.stats || { sunk: 0, specials: 0, bossWins: 0, kills: {} };
      state.stats.kills = state.stats.kills || {};
      state.stats.sunk = (state.stats.sunk || 0) + 1;
      state.stats.kills[c.ship.role] = (state.stats.kills[c.ship.role] || 0) + 1;
    }
  }
}

function applyRoundStart() {
  [battle.player, battle.enemy].forEach(side => {
    side.forEach(c => {
      if (!c.alive) return;
      if (c.cd > 0) c.cd--;
      if (c.torpCd > 0) c.torpCd--;
      if (c.status.burn > 0) {
        const dmg = Math.max(2, Math.round(c.maxHp * 0.035));
        c.hp -= dmg;
        blog(c.ship.name + ' sufre ' + dmg + ' de daño por incendio.', 'bad');
        c.status.burn--;
        checkKill(c);
      }
      if (c.status.evade > 0) c.status.evade--;
      if (c.status.smoke > 0) c.status.smoke--;
      if (c.status.dive > 0) c.status.dive--;
      if (c.status.speedDown > 0) c.status.speedDown--;
    });
  });
}

function nextTurn() {
  if (!battle || battle.over) return;
  if (checkEnd()) return;

  let guard = 0;
  while (guard++ < 30) {
    if (battle.turnIdx >= battle.queue.length) {
      battle.round++;
      battle.queue = buildQueue();
      battle.turnIdx = 0;
      applyRoundStart();
      if (checkEnd()) return;
      continue;
    }
    const c = combatantByKey(battle.queue[battle.turnIdx]);
    if (!c || !c.alive) { battle.turnIdx++; continue; }
    battle.current = c;
    if (c.side === 'player') {
      battle.phase = 'player';
      battle.pending = null;
      render();
      return;
    }
    battle.phase = 'enemy';
    render();
    setTimeout(enemyAct, 720);
    return;
  }
}

function checkEnd() {
  const enemiesAlive = battle.enemy.some(c => c.alive);
  const playerAlive = battle.player.some(c => c.alive);
  if (!enemiesAlive) { finishBattle(true); return true; }
  if (!playerAlive) { finishBattle(false); return true; }
  return false;
}

function endTurn() {
  if (!battle || battle.over) return;
  battle.current = null;
  battle.turnIdx++;
  nextTurn();
}

/* ---------- acciones de combate ---------- */

function evadeOf(c) {
  return c.stats.evade + (c.status.evade > 0 ? 25 : 0) + (c.status.smoke > 0 ? 25 : 0);
}

function hitChance(attacker, target, base) {
  return clamp(base + (attacker.stats.acc || 0) - evadeOf(target) / 320 + (target.status.speedDown > 0 ? 0.05 : 0), 0.12, 0.97);
}

function dealDamage(attacker, target, opts) {
  if (!target || !target.alive) return 0;
  const baseAcc = opts.acc == null ? 0.8 : opts.acc;
  if (rng() > hitChance(attacker, target, baseAcc)) {
    blog(attacker.ship.name + ' falla contra ' + target.ship.name + '.', 'miss');
    return 0;
  }
  const armor = target.stats.armor * (1 - (opts.ignoreArmor || 0));
  const mitigation = 100 / (100 + armor * 1.15);
  let dmg = opts.power * mitigation * rand(0.86, 1.14) * attacker.stats.damageMul;
  let crit = false;
  const critChance = attacker.stats.crit + (attacker.status.nextCrit ? 1 : 0);
  if (rng() < critChance) {
    dmg *= critChance >= 1 ? 2 : 1.65;
    crit = true;
  }
  attacker.status.nextCrit = false;
  if (target.side === 'player') dmg *= 1 - state.commander.skills.liderazgo * 0.015;
  dmg = Math.max(1, Math.round(dmg));
  target.hp -= dmg;
  blog((crit ? '¡CRÍTICO! ' : '') + attacker.ship.name + ' impacta a ' + target.ship.name + ' (' + dmg + ' de daño).', crit ? 'crit' : 'hit');
  sfx('hit');
  checkKill(target);
  return dmg;
}

function cannon(attacker, target) {
  sfx('fire');
  dealDamage(attacker, target, { power: attacker.stats.fp * 1.15, acc: 0.8 });
}

function launchTorpedo(attacker, target) {
  if (attacker.stats.torp <= 0 || attacker.torpCd > 0) return false;
  sfx('fire');
  dealDamage(attacker, target, { power: attacker.stats.torp * 1.9, acc: 0.62, ignoreArmor: 0.45 });
  attacker.torpCd = 2;
  return true;
}

function repairShip(c) {
  if (c.repaired) return false;
  const heal = Math.round(c.maxHp * 0.10 * c.stats.repairMul);
  c.hp = Math.min(c.maxHp, c.hp + heal);
  c.repaired = true;
  blog(c.ship.name + ' ejecuta reparaciones de emergencia (+' + heal + ' casco).', 'good');
  return true;
}

function useSpecial(attacker, target) {
  if (attacker.cd > 0) return false;
  const sp = SHIP_ROLES[attacker.ship.role].special;
  attacker.cd = sp.cd;
  if (attacker.side === 'player' && typeof state !== 'undefined' && state) {
    state.stats = state.stats || { sunk: 0, specials: 0, bossWins: 0, kills: {} };
    state.stats.specials = (state.stats.specials || 0) + 1;
  }
  sfx('fire');

  if (sp.kind === 'precision') {
    dealDamage(attacker, target, { power: attacker.stats.fp * 1.5, acc: 0.85, ignoreArmor: 0.4 });
  } else if (sp.kind === 'airstrike') {
    blog(attacker.ship.name + ' lanza una oleada aérea sobre la flota enemiga.', 'crit');
    battle.enemy.filter(e => e.alive).forEach(e => {
      dealDamage(attacker, e, { power: attacker.stats.fp * 0.7, acc: 0.9, ignoreArmor: 0.2 });
    });
  } else if (sp.kind === 'burning') {
    dealDamage(attacker, target, { power: attacker.stats.fp * 1.25, acc: 0.8, ignoreArmor: 0.1 });
    if (target && target.alive) {
      target.status.burn = 2;
      blog(target.ship.name + ' queda en llamas.', 'bad');
    }
  } else if (sp.kind === 'smoke') {
    battle.player.filter(p => p.alive).forEach(p => { p.status.smoke = 2; });
    blog('Cortina de humo desplegada: evasión aliada aumentada.', 'good');
  } else if (sp.kind === 'dive') {
    attacker.status.dive = 2;
    attacker.status.nextCrit = true;
    blog(attacker.ship.name + ' se sumerge y prepara un ataque crítico.', 'good');
  } else if (sp.kind === 'torpedo_burst') {
    dealDamage(attacker, target, { power: attacker.stats.torp * 2.2, acc: 0.65, ignoreArmor: 0.5 });
  } else if (sp.kind === 'ram') {
    dealDamage(attacker, target, { power: attacker.stats.fp * 1.4, acc: 0.72 });
    if (target && target.alive) {
      target.status.speedDown = 2;
      blog(target.ship.name + ' pierde velocidad.', 'bad');
    }
  } else if (sp.kind === 'board') {
    dealDamage(attacker, target, { power: attacker.stats.fp * 1.3, acc: 0.8 });
    const heal = Math.round(attacker.maxHp * 0.12);
    attacker.hp = Math.min(attacker.maxHp, attacker.hp + heal);
    blog(attacker.ship.name + ' recupera ' + heal + ' de casco tras la bordada.', 'good');
  }
  return true;
}

function enemyAct() {
  if (!battle || battle.over) return;
  const c = battle.current;
  if (!c || !c.alive || c.side !== 'enemy') { endTurn(); return; }

  const visible = battle.player.filter(p => p.alive && p.status.dive <= 0);
  const pool = visible.length ? visible : battle.player.filter(p => p.alive);
  if (!pool.length) { finishBattle(false); return; }
  const target = pool.reduce((a, b) => (a.hp < b.hp ? a : b));
  const ratio = c.hp / c.maxHp;

  let acted = false;
  if (ratio < 0.4 && !c.repaired && rng() < 0.45) acted = repairShip(c);
  if (!acted && c.cd <= 0 && rng() < 0.5) acted = useSpecial(c, target);
  if (!acted && c.stats.torp > 35 && c.torpCd <= 0 && rng() < 0.5) acted = launchTorpedo(c, target);
  if (!acted) { sfx('fire'); cannon(c, target); }
  endTurn();
}

/* ---------- punto de entrada al combate ---------- */

function deployOperation(op) {
  const active = activeShips();
  if (!active.length) { toast('Activa al menos un buque en Flota.'); return; }

  const scale = enemyScale(op);
  battle = {
    op: op,
    round: 1,
    log: [],
    queue: [],
    turnIdx: 0,
    current: null,
    pending: null,
    phase: 'player',
    over: false,
    player: active.map((e, i) => makeCombatant('player', i, e.shipId, { entry: e, level: e.level, scale: 1 })),
    enemy: op.enemyIds.map((id, i) => makeCombatant('enemy', i, id, { level: op.level, scale: scale }))
  };

  blog('Operación iniciada: ' + op.name, 'info');
  blog('Flota desplegada: ' + active.map(e => SHIP_MAP[e.shipId].name).join(', '), 'info');
  state.view = 'battle';
  battle.queue = buildQueue();
  applyRoundStart();
  render();
  setTimeout(nextTurn, 260);
}

Game.deploy = function (opId) {
  const op = state.ops.find(o => o.id === opId);
  if (!op || op.done) return;
  deployOperation(op);
};

function campaignUnlocked(index) {
  if (!state || !state.campaign || !state.campaign.cleared) return false;
  if (index === 0) return true;
  return !!state.campaign.cleared[index - 1];
}
window.campaignUnlocked = campaignUnlocked;

Game.startCampaign = function (index) {
  if (!state) return;
  const c = CAMPAIGN[index];
  if (!c) return;
  if (state.campaign && state.campaign.cleared && state.campaign.cleared[index]) {
    toast('Ese capítulo ya está completado.');
    return;
  }
  if (!campaignUnlocked(index)) {
    toast('Completa el capítulo anterior para desbloquear este.');
    return;
  }
  if (!activeShips().length) {
    toast('Activa al menos un buque en Flota.');
    return;
  }
  deployOperation({
    id: 'camp' + index,
    campaignIndex: index,
    name: 'Capítulo ' + c.chapter + ' · ' + c.name,
    desc: c.desc,
    level: c.level,
    enemyIds: c.enemyIds.slice(),
    done: false,
    boss: !!c.boss
  });
};

Game.act = function (kind) {
  if (!battle || battle.over || battle.phase !== 'player' || !battle.current) return;
  const c = battle.current;

  if (kind === 'evade') {
    c.status.evade = 2;
    blog(c.ship.name + ' realiza una maniobra evasiva (+25 evasión).', 'good');
    endTurn();
    return;
  }
  if (kind === 'repair') {
    if (!repairShip(c)) { toast('Este buque ya reparó en este combate.'); return; }
    endTurn();
    return;
  }
  if (kind === 'cannon') { battle.pending = { kind: 'cannon' }; render(); return; }
  if (kind === 'torpedo') {
    if (c.stats.torp <= 0) { toast('Este buque no tiene torpedos.'); return; }
    if (c.torpCd > 0) { toast('Torpedos recargando (' + c.torpCd + ').'); return; }
    battle.pending = { kind: 'torpedo' };
    render();
    return;
  }
  if (kind === 'special') {
    if (c.cd > 0) { toast('Habilidad en recarga (' + c.cd + ').'); return; }
    const sp = SHIP_ROLES[c.ship.role].special;
    if (sp.target) { battle.pending = { kind: 'special' }; render(); return; }
    useSpecial(c, null);
    endTurn();
  }
};

Game.cancel = function () {
  if (battle) { battle.pending = null; render(); }
};

Game.target = function (key) {
  if (!battle || !battle.pending) return;
  const target = combatantByKey(key);
  if (!target || !target.alive || target.side !== 'enemy') return;
  const c = battle.current;
  const kind = battle.pending.kind;
  battle.pending = null;
  if (kind === 'cannon') cannon(c, target);
  else if (kind === 'torpedo') launchTorpedo(c, target);
  else if (kind === 'special') useSpecial(c, target);
  endTurn();
};

/* ---------- experiencia y fin de combate ---------- */

function addCommanderXp(n) {
  const cm = state.commander;
  cm.xp += n;
  while (cm.xp >= xpNeedCommander(cm.level)) {
    cm.xp -= xpNeedCommander(cm.level);
    cm.level++;
    cm.points += 2;
    cm.credits += 150;
  }
}

function addShipXp(entry, n) {
  entry.xp += n;
  while (entry.level < 10 && entry.xp >= xpNeedShip(entry.level)) {
    entry.xp -= xpNeedShip(entry.level);
    entry.level++;
    const gain = Math.round(SHIP_MAP[entry.shipId].stats.hp * 0.06);
    entry.hp = Math.min(shipMaxHp(entry), entry.hp + gain);
  }
  if (entry.level >= 10) entry.xp = Math.min(entry.xp, xpNeedShip(10));
}

function finishBattle(victory) {
  if (!battle || battle.over) return;
  battle.over = true;
  const op = battle.op;

  battle.player.forEach(c => {
    if (!c.entry) return;
    if (c.hp <= 0) {
      c.entry.hp = Math.max(1, Math.round(c.maxHp * (victory ? 0.15 : 0.5)));
    } else {
      c.entry.hp = clamp(Math.round(c.hp), 0, c.maxHp);
    }
  });

  const result = {
    victory: victory,
    name: op.name,
    level: op.level,
    credits: 0,
    commanderXp: 0,
    shipXp: 0,
    levelUps: [],
    notes: [],
    ships: [],
    campaign: op.campaignIndex != null,
    campaignIndex: op.campaignIndex != null ? op.campaignIndex : null,
    chapter: op.campaignIndex != null ? CAMPAIGN[op.campaignIndex].chapter : ''
  };
  battle.player.forEach(c => {
    result.ships.push({ name: c.ship.name, hp: c.hp, max: c.maxHp, alive: c.alive });
  });

  if (victory) {
    const base = op.enemyIds.reduce((sum, id) => sum + SHIP_MAP[id].cost, 0);
    let credits;
    let xp;

    if (op.campaignIndex != null && CAMPAIGN[op.campaignIndex]) {
      const camp = CAMPAIGN[op.campaignIndex];
      credits = (camp.rewards && camp.rewards.credits) || Math.round(base * 0.2 + op.level * 50);
      xp = (camp.rewards && camp.rewards.xp) || (60 + op.level * 35);
    } else {
      credits = Math.round(base * 0.2 + op.level * 50);
      xp = 60 + op.level * 35;
      if (op.boss) {
        credits = Math.round(credits * 1.8);
        xp = Math.round(xp * 1.5);
        result.notes.push('Recompensa de operación especial aplicada.');
      }
    }

    const sk = state.commander.skills;
    credits = Math.round(credits * (1 + 0.05 * (sk.logistica || 0)));
    xp = Math.round(xp * (1 + 0.03 * (sk.inteligencia || 0)));

    state.commander.credits += credits;
    result.credits = credits;
    result.commanderXp = xp;
    const before = state.commander.level;
    addCommanderXp(xp);
    if (state.commander.level > before) {
      result.levelUps.push('El comandante alcanzó el nivel ' + state.commander.level + ' (+2 puntos de habilidad).');
    }
    const shipXp = 30 + op.level * 22;
    result.shipXp = shipXp;
    battle.player.forEach(c => {
      if (!c.entry) return;
      const prev = c.entry.level;
      addShipXp(c.entry, Math.round(shipXp * (c.alive ? 1 : 0.5)));
      if (c.entry.level > prev) result.levelUps.push(c.ship.name + ' alcanzó el nivel ' + c.entry.level + '.');
    });

    state.stats = state.stats || { sunk: 0, specials: 0, bossWins: 0, kills: {} };
    if (op.boss) state.stats.bossWins = (state.stats.bossWins || 0) + 1;

    if (op.campaignIndex != null && CAMPAIGN[op.campaignIndex]) {
      const camp = CAMPAIGN[op.campaignIndex];
      state.campaign = state.campaign || { cleared: {} };
      state.campaign.cleared[op.campaignIndex] = true;
      result.notes.push('Capítulo ' + camp.chapter + ' completado.');

      if (camp.rewards && camp.rewards.ship) {
        const shipId = camp.rewards.ship;
        if (state.fleet.some(e => e.shipId === shipId)) {
          const refund = Math.round(SHIP_MAP[shipId].cost * 0.6);
          state.commander.credits += refund;
          result.notes.push('Buque repetido (' + SHIP_MAP[shipId].name + '): +' + fmt(refund) + ' créditos.');
        } else {
          state.fleet.push(makeEntry(shipId, activeShips().length < slots()));
          result.notes.push('Nuevo buque desbloqueado: ' + SHIP_MAP[shipId].name + '.');
        }
      }

      if (camp.rewards && camp.rewards.officer) {
        const officerId = camp.rewards.officer;
        if (state.officers.indexOf(officerId) !== -1) {
          state.commander.credits += 800;
          result.notes.push('Oficial repetido: +800 créditos.');
        } else {
          state.officers.push(officerId);
          result.notes.push('Nuevo oficial: ' + OFFICER_MAP[officerId].name + '.');
        }
      }
    }

    let chestId = null;
    if (op.campaignIndex != null && CAMPAIGN[op.campaignIndex] && CAMPAIGN[op.campaignIndex].rewards && CAMPAIGN[op.campaignIndex].rewards.chest) {
      chestId = CAMPAIGN[op.campaignIndex].rewards.chest;
    } else if (op.boss) {
      chestId = 'gold';
    } else {
      const roll = rng();
      if (roll < 0.01) chestId = 'gold';
      else if (roll < 0.07) chestId = 'silver';
      else if (roll < 0.25) chestId = 'bronze';
    }
    if (chestId && CHEST_MAP[chestId]) {
      state.chests = state.chests || { bronze: 0, silver: 0, gold: 0, legendary: 0 };
      state.chests[chestId] = (state.chests[chestId] || 0) + 1;
      result.notes.push('Cofre obtenido: ' + CHEST_MAP[chestId].name + '.');
    }

    state.missionsWon++;
    op.done = true;
  } else {
    const credits = 150;
    state.commander.credits += credits;
    result.credits = credits;
    result.notes.push('La flota fue recuperada con daños graves. Repara los buques antes de volver al combate.');
  }

  const unlocked = checkAchievements();
  unlocked.forEach(a => {
    result.notes.push('Logro desbloqueado: ' + a.name + ' (+' + fmt(a.reward.credits) + ' créditos, +' + fmt(a.reward.xp) + ' XP).');
  });

  state.lastResult = result;
  battle = null;
  save();
  state.view = 'result';
  render();
}

/* ---------- interfaz de combate ---------- */

function renderBattle(v) {
  if (!battle) { state.view = 'ops'; renderOps(v); return; }
  const op = battle.op;

  v.innerHTML = `
    <section class="battle-screen">
      <div class="battle-head">
        <div><div class="eyebrow">COMBATE NAVAL</div><h2>${op.name}${op.boss ? ' · ESPECIAL' : ''}</h2></div>
        <div class="battle-meta">
          <span>RONDA ${battle.round}</span>
          <span>NIVEL ${op.level}</span>
          <span class="${battle.phase === 'player' ? 'good' : ''}">${battle.phase === 'player' ? 'TU TURNO' : 'TURNO ENEMIGO'}</span>
        </div>
      </div>
      <div class="combat-row enemy">${battle.enemy.map(combatCard).join('')}</div>
      <div class="battle-middle">
        <div class="log" id="battleLog">
          ${battle.log.map(l => `<div class="log-line ${l.cls}">${l.text}</div>`).join('')}
        </div>
        <div class="turn-panel">${actionPanel()}</div>
      </div>
      <div class="combat-row player">${battle.player.map(combatCard).join('')}</div>
    </section>`;

  const lg = $('#battleLog');
  if (lg) lg.scrollTop = lg.scrollHeight;
}

function combatCard(c) {
  const pct = clamp(Math.round(c.hp / c.maxHp * 100), 0, 100);
  const isTarget = battle.pending && c.side === 'enemy' && c.alive;
  const isCurrent = battle.current && battle.current.key === c.key;
  const statuses = [];
  if (c.status.burn > 0) statuses.push('INCENDIO');
  if (c.status.speedDown > 0) statuses.push('AVERIADO');
  if (c.status.smoke > 0) statuses.push('HUMO');
  if (c.status.dive > 0) statuses.push('SUMERGIDO');
  if (c.status.evade > 0) statuses.push('EVASIÓN');
  const cd = c.cd > 0 ? ' · HAB ' + c.cd : '';
  const torp = c.torpCd > 0 ? ' · TORP ' + c.torpCd : '';

  return `<div class="combat-card${c.alive ? '' : ' dead'}${isTarget ? ' targetable' : ''}${isCurrent ? ' current' : ''}"${isTarget ? ` onclick="Game.target('${c.key}')"` : ''}>
    <div class="cc-head"><span class="cc-name">${c.ship.name}</span><span class="cc-lvl">Nv.${c.level}</span></div>
    ${shipSVG(c.ship.role, 96)}
    <div class="bar"><i class="${pct < 35 ? 'low' : pct < 70 ? 'mid' : ''}" style="width:${pct}%"></i></div>
    <div class="cc-hp">${c.alive ? fmt(Math.max(0, Math.round(c.hp))) + ' / ' + fmt(c.maxHp) : 'HUNDIDO'}</div>
    <div class="cc-status">${statuses.map(s => `<span>${s}</span>`).join('')}${cd}${torp}</div>
  </div>`;
}

function actionPanel() {
  if (battle.over) return '';
  const c = battle.current;
  if (!c) return '<div class="turn-info">Preparando el siguiente turno…</div>';
  if (battle.phase !== 'player') {
    return '<div class="turn-info">Turno enemigo: <strong>' + c.ship.name + '</strong></div>';
  }

  const sp = SHIP_ROLES[c.ship.role].special;
  const pending = battle.pending
    ? '<div class="pending">Selecciona un objetivo en la flota enemiga <button class="btn tiny ghost" onclick="Game.cancel()">Cancelar</button></div>'
    : '';

  return `
    <div class="turn-info">Turno de <strong>${c.ship.name}</strong></div>
    ${pending}
    <div class="actions">
      <button class="btn action" onclick="Game.act('cannon')"><b>Cañoneo</b><span>${Math.round(c.stats.fp)} de fuego</span></button>
      <button class="btn action" onclick="Game.act('torpedo')" ${c.stats.torp <= 0 || c.torpCd > 0 ? 'disabled' : ''}><b>Torpedos</b><span>${Math.round(c.stats.torp)} de poder</span></button>
      <button class="btn action" onclick="Game.act('evade')"><b>Maniobra</b><span>+25 evasión</span></button>
      <button class="btn action" onclick="Game.act('repair')" ${c.repaired ? 'disabled' : ''}><b>Reparar</b><span>${c.repaired ? 'usado' : '+10% casco'}</span></button>
      <button class="btn action special" onclick="Game.act('special')" ${c.cd > 0 ? 'disabled' : ''}><b>${sp.name}</b><span>${c.cd > 0 ? 'recarga ' + c.cd : 'lista'}</span></button>
    </div>`;
}

function renderResult(v) {
  const r = state.lastResult;
  if (!r) { state.view = 'hq'; renderHQ(v); return; }

  v.innerHTML = `
    <section class="result-screen ${r.victory ? 'win' : 'lose'}">
      <div class="result-banner">
        <div class="eyebrow">${r.victory ? 'OPERACIÓN COMPLETADA' : 'OPERACIÓN FALLIDA'}</div>
        <h1>${r.victory ? 'VICTORIA' : 'DERROTA'}</h1>
        <p>${r.name} · Nivel ${r.level}</p>
      </div>
      <div class="result-grid">
        <div class="panel">
          <h3>Recompensas</h3>
          <div class="reward-list">
            <div><span>Créditos</span><strong>+${fmt(r.credits)}</strong></div>
            <div><span>XP comandante</span><strong>+${fmt(r.commanderXp)}</strong></div>
            <div><span>XP por buque</span><strong>+${fmt(r.shipXp)}</strong></div>
          </div>
        </div>
        <div class="panel">
          <h3>Estado de la flota</h3>
          ${r.ships.map(s => `<div class="result-ship"><span>${s.name}</span><b class="${s.alive ? 'good' : 'bad'}">${s.alive ? fmt(Math.round(s.hp)) + ' casco' : 'hundido'}</b></div>`).join('')}
        </div>
      </div>
      ${r.levelUps.length ? `<div class="panel"><h3>Ascensos</h3>${r.levelUps.map(x => `<p class="good">${x}</p>`).join('')}</div>` : ''}
      ${r.notes.length ? `<div class="panel"><h3>Informe</h3>${r.notes.map(x => `<p>${x}</p>`).join('')}</div>` : ''}
      <div class="quick-actions">
        ${r.campaign
          ? '<button class="btn primary" onclick="Game.go(\'campaign\')">Volver a la campaña</button>'
          : '<button class="btn primary" onclick="Game.go(\'ops\')">Volver a operaciones</button>'}
        <button class="btn ghost" onclick="Game.go('fleet')">Reparar flota</button>
        <button class="btn ghost" onclick="Game.go('hq')">Mando</button>
      </div>
    </section>`;
}

/* ---------- arranque ---------- */

document.addEventListener('DOMContentLoaded', function () {
  const saved = load();
  if (saved) {
    state = saved;
    state.view = 'hq';
    if (typeof checkAchievements === 'function') checkAchievements();
  }
  render();

  const modal = $('#modal');
  modal.addEventListener('click', function (e) {
    if (e.target === modal) Game.closeModal();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') Game.closeModal();
  });

  if (typeof initCloud === 'function') initCloud();
});
