'use strict';

/* ---------- estado del puente ---------- */

const BRIDGE_WORLD = { w: 2800, h: 2100 };

const BRIDGE_ISLANDS = [
  { x: 540, y: 470, r: 150, seed: 1 },
  { x: 2130, y: 690, r: 195, seed: 2 },
  { x: 1250, y: 1480, r: 135, seed: 3 },
  { x: 2410, y: 1770, r: 125, seed: 4 },
  { x: 430, y: 1680, r: 95, seed: 5 }
];

const BRIDGE_TARGET_POOL = SHIPS.filter(function (s) {
  return s.tier <= 3 && s.role !== 'carrier' && s.role !== 'frigate';
});

let bridge = null;
let bridgeShipUid = null;

function stopBridge() {
  if (!bridge) return;
  bridge.running = false;
  if (bridge.raf) cancelAnimationFrame(bridge.raf);
  try {
    window.removeEventListener('keydown', bridge.onKeyDown);
    window.removeEventListener('keyup', bridge.onKeyUp);
    window.removeEventListener('resize', bridge.onResize);
  } catch (e) { /* sin listeners */ }
  bridge = null;
}
window.stopBridge = stopBridge;

/* ---------- pantalla ---------- */

function renderBridge(v) {
  stopBridge();
  if (!state) { renderMenu(v); return; }

  const ships = state.fleet;
  if (!ships.length) {
    v.innerHTML = '<section class="screen"><p class="hint">No tienes buques en la flota.</p></section>';
    return;
  }

  let entry = ships.find(function (e) { return e.uid === bridgeShipUid; });
  if (!entry) entry = activeShips()[0] || ships[0];
  bridgeShipUid = entry.uid;

  const ship = SHIP_MAP[entry.shipId];
  const stats = statsFor(ship, { entry: entry, level: entry.level, side: 'player', scale: 1 });

  v.innerHTML =
    '<section class="screen bridge-screen">' +
      '<div class="screen-head">' +
        '<div><div class="eyebrow">PUENTE DE MANDO</div><h2>' + ship.name + '</h2></div>' +
        '<div class="head-actions">' +
          '<select class="bridge-select" onchange="Game.bridgeWith(this.value)">' +
            ships.map(function (e) {
              const s = SHIP_MAP[e.shipId];
              return '<option value="' + e.uid + '"' + (e.uid === entry.uid ? ' selected' : '') + '>' + s.name + ' · Nv.' + e.level + '</option>';
            }).join('') +
          '</select>' +
          '<button class="btn ghost" onclick="Game.go(\'fleet\')">Volver a flota</button>' +
        '</div>' +
      '</div>' +
      '<div class="bridge-wrap">' +
        '<canvas id="bridgeCanvas"></canvas>' +
        '<div class="bridge-hud">' +
          '<span class="hud-chip">VELOCIDAD <b id="hudSpeed">0 kn</b></span>' +
          '<span class="hud-chip">PUNTOS <b id="hudScore">0</b></span>' +
          '<span class="hud-chip">BLANCOS <b id="hudSunk">0</b></span>' +
          '<span class="hud-chip">PRÁCTICA <b id="hudReward">0/10</b></span>' +
          '<span class="hud-chip">CAÑÓN <b id="hudStatus">LISTO</b></span>' +
          '<span class="hud-chip">MÁQUINA <span class="hud-bar"><i id="hudThrottle"></i></span></span>' +
        '</div>' +
        '<div class="bridge-help">W/S acelerar · A/D girar · Espacio andanada · Clic disparar</div>' +
        '<div class="touch-controls">' +
          '<div class="joystick" id="bridgeJoy"><div class="joy-knob" id="bridgeKnob"></div></div>' +
          '<button class="fire-btn" id="bridgeFire">FUEGO</button>' +
        '</div>' +
      '</div>' +
      '<div class="bridge-stats">' +
        '<span>Clase <b>' + SHIP_ROLES[ship.role].label + '</b></span>' +
        '<span>Velocidad máx. <b>' + Math.round(stats.speed) + ' nudos</b></span>' +
        '<span>Fuego <b>' + Math.round(stats.fp) + '</b></span>' +
        '<span>Blindaje <b>' + Math.round(stats.armor) + '</b></span>' +
        '<span>Nivel <b>' + entry.level + '</b></span>' +
        '<span>Controles <b>teclado / táctil</b></span>' +
      '</div>' +
    '</section>';

  startBridge(entry, stats);
}

Game.bridgeWith = function (uid) {
  bridgeShipUid = uid;
  Game.go('bridge');
};

/* ---------- arranque ---------- */

function startBridge(entry, stats) {
  const canvas = $('#bridgeCanvas');
  if (!canvas) return;
  const ship = SHIP_MAP[entry.shipId];

  const b = {
    entry: entry,
    ship: ship,
    stats: stats,
    canvas: canvas,
    ctx: canvas.getContext('2d'),
    running: true,
    raf: 0,
    last: 0,
    time: 0,
    keys: {},
    joyX: 0,
    joyY: 0,
    score: 0,
    sunk: 0,
    rewarded: 0,
    obj: {
      x: BRIDGE_WORLD.w / 2,
      y: BRIDGE_WORLD.h / 2,
      angle: -Math.PI / 2,
      speed: 0,
      throttle: 0,
      rudder: 0,
      fireCd: 0
    },
    cam: { x: BRIDGE_WORLD.w / 2, y: BRIDGE_WORLD.h / 2 },
    targets: [],
    shells: [],
    particles: [],
    onKeyDown: null,
    onKeyUp: null,
    onResize: null
  };

  bridge = b;
  resizeBridge();
  spawnBridgeTargets();
  bindBridgeInput();

  b.raf = requestAnimationFrame(bridgeLoop);
}

function resizeBridge() {
  if (!bridge) return;
  const canvas = bridge.canvas;
  const rect = canvas.getBoundingClientRect();
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  canvas.width = Math.max(320, Math.round(rect.width * dpr));
  canvas.height = Math.max(280, Math.round(rect.height * dpr));
  bridge.cssW = Math.max(320, rect.width);
  bridge.cssH = Math.max(280, rect.height);
  bridge.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function bindBridgeInput() {
  const b = bridge;

  b.onKeyDown = function (e) {
    const k = e.key.toLowerCase();
    if (k === ' ' || k.indexOf('arrow') === 0) e.preventDefault();
    b.keys[k] = true;
    if (k === ' ' && !e.repeat) bridgeBroadside();
  };
  b.onKeyUp = function (e) {
    b.keys[e.key.toLowerCase()] = false;
  };
  b.onResize = function () { resizeBridge(); };
  window.addEventListener('keydown', b.onKeyDown);
  window.addEventListener('keyup', b.onKeyUp);
  window.addEventListener('resize', b.onResize);

  b.canvas.addEventListener('pointerdown', function (e) {
    if (e.button !== 0 && e.pointerType === 'mouse') return;
    const rect = b.canvas.getBoundingClientRect();
    const wx = b.cam.x - rect.width / 2 + (e.clientX - rect.left);
    const wy = b.cam.y - rect.height / 2 + (e.clientY - rect.top);
    fireBridgeAt(wx, wy);
  });

  const joy = $('#bridgeJoy');
  const knob = $('#bridgeKnob');
  const fire = $('#bridgeFire');
  let joyId = null;

  if (joy && knob) {
    const setJoy = function (e) {
      const rect = joy.getBoundingClientRect();
      let dx = e.clientX - (rect.left + rect.width / 2);
      let dy = e.clientY - (rect.top + rect.height / 2);
      const max = rect.width / 2 - 10;
      const len = Math.hypot(dx, dy);
      if (len > max) { dx = dx / len * max; dy = dy / len * max; }
      knob.style.transform = 'translate(' + dx + 'px,' + dy + 'px)';
      b.joyX = dx / max;
      b.joyY = dy / max;
    };
    joy.addEventListener('pointerdown', function (e) {
      joyId = e.pointerId;
      try { joy.setPointerCapture(joyId); } catch (err) { /* ignorar */ }
      setJoy(e);
      e.preventDefault();
    });
    joy.addEventListener('pointermove', function (e) {
      if (joyId === e.pointerId) setJoy(e);
    });
    const endJoy = function (e) {
      if (joyId !== e.pointerId) return;
      joyId = null;
      knob.style.transform = '';
      b.joyX = 0;
      b.joyY = 0;
    };
    joy.addEventListener('pointerup', endJoy);
    joy.addEventListener('pointercancel', endJoy);
  }

  if (fire) {
    fire.addEventListener('pointerdown', function (e) {
      e.preventDefault();
      bridgeBroadside();
    });
  }
}

/* ---------- mundo ---------- */

function insideIsland(x, y, pad) {
  for (let i = 0; i < BRIDGE_ISLANDS.length; i++) {
    const isl = BRIDGE_ISLANDS[i];
    if (Math.hypot(x - isl.x, y - isl.y) < isl.r + (pad || 0)) return true;
  }
  return false;
}

function createTarget(ship) {
  let x = 0, y = 0, tries = 0;
  do {
    x = rand(220, BRIDGE_WORLD.w - 220);
    y = rand(220, BRIDGE_WORLD.h - 220);
    tries++;
  } while (tries < 40 && (Math.hypot(x - bridge.obj.x, y - bridge.obj.y) < 480 || insideIsland(x, y, 70)));

  const hp = Math.round(ship.stats.hp * 0.55) + 60;
  return {
    ship: ship,
    x: x,
    y: y,
    angle: rand(0, Math.PI * 2),
    speed: rand(14, 30),
    turn: rand(-0.5, 0.5),
    hp: hp,
    maxHp: hp,
    radius: 26,
    alive: true,
    respawn: 0
  };
}

function spawnBridgeTargets() {
  bridge.targets = [];
  for (let i = 0; i < 4; i++) {
    bridge.targets.push(createTarget(pick(BRIDGE_TARGET_POOL)));
  }
}

function bridgeBroadside() {
  if (!bridge || bridge.obj.fireCd > 0) return;
  const b = bridge;
  const a = b.obj.angle;
  const dmg = b.stats.fp * 0.7 + 6;
  spawnBridgeShell(a + Math.PI / 2, dmg);
  spawnBridgeShell(a - Math.PI / 2, dmg);
  b.obj.fireCd = 1.0;
  b.obj.recoil = 1;
  sfx('fire');
}

function fireBridgeAt(wx, wy) {
  if (!bridge || bridge.obj.fireCd > 0) return;
  const b = bridge;
  const a = Math.atan2(wy - b.obj.y, wx - b.obj.x);
  spawnBridgeShell(a, b.stats.fp * 1.1 + 8);
  b.obj.fireCd = 0.6;
  b.obj.recoil = 0.7;
  sfx('fire');
}

function spawnBridgeShell(angle, dmg) {
  const b = bridge;
  const muzzle = 30;
  const speed = 560;
  b.shells.push({
    x: b.obj.x + Math.cos(angle) * muzzle,
    y: b.obj.y + Math.sin(angle) * muzzle,
    vx: Math.cos(angle) * speed,
    vy: Math.sin(angle) * speed,
    life: 1.35,
    dmg: dmg,
    trail: 0
  });
  for (let i = 0; i < 5; i++) {
    b.particles.push({
      x: b.obj.x + Math.cos(angle) * muzzle,
      y: b.obj.y + Math.sin(angle) * muzzle,
      vx: Math.cos(angle) * rand(10, 45) + rand(-20, 20),
      vy: Math.sin(angle) * rand(10, 45) + rand(-20, 20),
      life: rand(0.25, 0.5),
      max: 0.5,
      size: rand(2, 4),
      color: '255,210,120'
    });
  }
}

function sinkBridgeTarget(t) {
  t.alive = false;
  t.respawn = rand(3.2, 5.5);
  bridge.sunk++;

  if (bridge.rewarded < 10) {
    bridge.rewarded++;
    state.commander.credits += 15;
    bridge.score += 150;
    save();
    renderHeader();
    toast('Blanco hundido: +15 créditos (' + bridge.rewarded + '/10).');
  } else {
    bridge.score += 100;
  }

  for (let i = 0; i < 18; i++) {
    bridge.particles.push({
      x: t.x,
      y: t.y,
      vx: rand(-90, 90),
      vy: rand(-90, 90),
      life: rand(0.4, 0.9),
      max: 0.9,
      size: rand(2, 5),
      color: i % 2 ? '255,140,70' : '255,220,140'
    });
  }
  sfx('hit');
}

/* ---------- bucle ---------- */

function bridgeLoop(ts) {
  if (!bridge || !bridge.running) return;
  if (!bridge.last) bridge.last = ts;
  let dt = (ts - bridge.last) / 1000;
  bridge.last = ts;
  dt = Math.min(0.05, Math.max(0.001, dt));
  bridge.time += dt;

  updateBridge(dt);
  drawBridge();
  updateBridgeHud();

  bridge.raf = requestAnimationFrame(bridgeLoop);
}

function updateBridge(dt) {
  const b = bridge;
  const o = b.obj;
  const keys = b.keys;

  const up = keys['w'] || keys['arrowup'];
  const down = keys['s'] || keys['arrowdown'];
  const left = keys['a'] || keys['arrowleft'];
  const right = keys['d'] || keys['arrowright'];

  if (up) o.throttle += dt * 1.15;
  if (down) o.throttle -= dt * 1.35;
  if (b.joyY && Math.abs(b.joyY) > 0.08) o.throttle = clamp(-b.joyY, -0.6, 1);
  o.throttle = clamp(o.throttle, -0.4, 1);

  let rudder = (right ? 1 : 0) - (left ? 1 : 0);
  if (b.joyX && Math.abs(b.joyX) > 0.08) rudder = b.joyX;
  o.rudder = rudder;

  const maxSpeed = 22 + b.stats.speed * 2.2;
  const targetSpeed = o.throttle * maxSpeed;
  o.speed += (targetSpeed - o.speed) * Math.min(1, dt * 1.15);

  const spdFactor = clamp(Math.abs(o.speed) / maxSpeed, 0.08, 1);
  const dir = o.speed < -1 ? -1 : 1;
  o.angle += o.rudder * (0.18 + spdFactor * 1.15) * dt * dir;

  o.x += Math.cos(o.angle) * o.speed * dt;
  o.y += Math.sin(o.angle) * o.speed * dt;

  if (o.x < 50) { o.x = 50; o.speed *= 0.4; }
  if (o.x > BRIDGE_WORLD.w - 50) { o.x = BRIDGE_WORLD.w - 50; o.speed *= 0.4; }
  if (o.y < 50) { o.y = 50; o.speed *= 0.4; }
  if (o.y > BRIDGE_WORLD.h - 50) { o.y = BRIDGE_WORLD.h - 50; o.speed *= 0.4; }

  for (let i = 0; i < BRIDGE_ISLANDS.length; i++) {
    const isl = BRIDGE_ISLANDS[i];
    const dx = o.x - isl.x;
    const dy = o.y - isl.y;
    const d = Math.hypot(dx, dy) || 1;
    const min = isl.r + 26;
    if (d < min) {
      o.x = isl.x + dx / d * min;
      o.y = isl.y + dy / d * min;
      o.speed *= 0.35;
    }
  }

  if (o.fireCd > 0) o.fireCd -= dt;
  if (o.recoil > 0) o.recoil = Math.max(0, o.recoil - dt * 4);

  if (Math.abs(o.speed) > 12 && Math.random() < dt * 26) {
    const back = -Math.cos(o.angle) * 24;
    const side = -Math.sin(o.angle) * 24;
    b.particles.push({
      x: o.x + back + rand(-3, 3),
      y: o.y + side + rand(-3, 3),
      vx: -Math.cos(o.angle) * rand(6, 20) + rand(-8, 8),
      vy: -Math.sin(o.angle) * rand(6, 20) + rand(-8, 8),
      life: rand(0.7, 1.5),
      max: 1.5,
      size: rand(2, 5),
      color: '180,225,255'
    });
  }

  for (let i = b.targets.length - 1; i >= 0; i--) {
    const t = b.targets[i];
    if (!t.alive) {
      t.respawn -= dt;
      if (t.respawn <= 0) b.targets[i] = createTarget(pick(BRIDGE_TARGET_POOL));
      continue;
    }
    t.angle += t.turn * dt;
    if (Math.random() < dt * 0.4) t.turn = rand(-0.6, 0.6);
    t.x += Math.cos(t.angle) * t.speed * dt;
    t.y += Math.sin(t.angle) * t.speed * dt;
    if (t.x < 80 || t.x > BRIDGE_WORLD.w - 80) { t.angle = Math.PI - t.angle; t.x = clamp(t.x, 80, BRIDGE_WORLD.w - 80); }
    if (t.y < 80 || t.y > BRIDGE_WORLD.h - 80) { t.angle = -t.angle; t.y = clamp(t.y, 80, BRIDGE_WORLD.h - 80); }
    for (let k = 0; k < BRIDGE_ISLANDS.length; k++) {
      const isl = BRIDGE_ISLANDS[k];
      const dx = t.x - isl.x;
      const dy = t.y - isl.y;
      const d = Math.hypot(dx, dy) || 1;
      const min = isl.r + 30;
      if (d < min) {
        t.x = isl.x + dx / d * min;
        t.y = isl.y + dy / d * min;
        t.angle = Math.atan2(dy, dx);
      }
    }
  }

  for (let i = b.shells.length - 1; i >= 0; i--) {
    const s = b.shells[i];
    s.x += s.vx * dt;
    s.y += s.vy * dt;
    s.life -= dt;
    s.trail += dt;

    let hit = false;
    for (let j = 0; j < b.targets.length; j++) {
      const t = b.targets[j];
      if (!t.alive) continue;
      if (Math.hypot(s.x - t.x, s.y - t.y) < t.radius + 5) {
        t.hp -= s.dmg;
        hit = true;
        for (let p = 0; p < 8; p++) {
          b.particles.push({
            x: s.x, y: s.y,
            vx: rand(-80, 80), vy: rand(-80, 80),
            life: rand(0.25, 0.6), max: 0.6,
            size: rand(2, 4), color: '255,190,120'
          });
        }
        if (t.hp <= 0) sinkBridgeTarget(t);
        else sfx('hit');
        break;
      }
    }

    if (!hit && Math.abs(s.x - b.obj.x) < 8 && Math.abs(s.y - b.obj.y) < 8) hit = false;

    if (s.life <= 0 || insideIsland(s.x, s.y, 0)) {
      if (insideIsland(s.x, s.y, 0)) {
        for (let p = 0; p < 5; p++) {
          b.particles.push({
            x: s.x, y: s.y,
            vx: rand(-50, 50), vy: rand(-50, 50),
            life: rand(0.2, 0.45), max: 0.45,
            size: rand(1, 3), color: '210,230,245'
          });
        }
      }
      b.shells.splice(i, 1);
    } else if (hit) {
      b.shells.splice(i, 1);
    }
  }

  for (let i = b.particles.length - 1; i >= 0; i--) {
    const p = b.particles[i];
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.vx *= 0.96;
    p.vy *= 0.96;
    p.life -= dt;
    if (p.life <= 0) b.particles.splice(i, 1);
  }

  b.cam.x += (o.x - b.cam.x) * Math.min(1, dt * 3.2);
  b.cam.y += (o.y - b.cam.y) * Math.min(1, dt * 3.2);
}

/* ---------- dibujo ---------- */

function drawBridge() {
  const b = bridge;
  const ctx = b.ctx;
  const w = b.cssW;
  const h = b.cssH;
  const cam = b.cam;

  const sea = ctx.createLinearGradient(0, 0, 0, h);
  sea.addColorStop(0, '#081a2a');
  sea.addColorStop(0.55, '#082033');
  sea.addColorStop(1, '#05111d');
  ctx.fillStyle = sea;
  ctx.fillRect(0, 0, w, h);

  ctx.save();
  ctx.translate(w / 2 - cam.x, h / 2 - cam.y);

  const left = cam.x - w / 2;
  const right = cam.x + w / 2;
  const top = cam.y - h / 2;
  const bottom = cam.y + h / 2;

  ctx.strokeStyle = 'rgba(90,210,244,0.075)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let x = Math.floor(left / 100) * 100; x <= right; x += 100) {
    ctx.moveTo(x, top);
    ctx.lineTo(x, bottom);
  }
  for (let y = Math.floor(top / 100) * 100; y <= bottom; y += 100) {
    ctx.moveTo(left, y);
    ctx.lineTo(right, y);
  }
  ctx.stroke();

  ctx.strokeStyle = 'rgba(90,210,244,0.22)';
  ctx.lineWidth = 2;
  ctx.strokeRect(0, 0, BRIDGE_WORLD.w, BRIDGE_WORLD.h);

  drawBridgeIslands(ctx);

  for (let i = 0; i < b.particles.length; i++) {
    const p = b.particles[i];
    const alpha = clamp(p.life / p.max, 0, 1) * 0.65;
    ctx.beginPath();
    ctx.fillStyle = 'rgba(' + p.color + ',' + alpha.toFixed(3) + ')';
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    ctx.fill();
  }

  for (let i = 0; i < b.targets.length; i++) {
    const t = b.targets[i];
    if (!t.alive) continue;
    drawShipTop(ctx, t.x, t.y, t.angle, t.ship.role, '#ff6b6b', 0.92);
    const ratio = clamp(t.hp / t.maxHp, 0, 1);
    ctx.fillStyle = 'rgba(0,0,0,0.55)';
    ctx.fillRect(t.x - 24, t.y - 38, 48, 6);
    ctx.fillStyle = ratio > 0.5 ? '#ffb15e' : '#ff6b6b';
    ctx.fillRect(t.x - 24, t.y - 38, 48 * ratio, 6);
  }

  for (let i = 0; i < b.shells.length; i++) {
    const s = b.shells[i];
    ctx.strokeStyle = 'rgba(255,210,120,0.55)';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(s.x - s.vx * 0.03, s.y - s.vy * 0.03);
    ctx.lineTo(s.x, s.y);
    ctx.stroke();
    ctx.beginPath();
    ctx.fillStyle = '#ffe3a0';
    ctx.arc(s.x, s.y, 3.2, 0, Math.PI * 2);
    ctx.fill();
  }

  const o = b.obj;
  const recoil = o.recoil || 0;
  drawShipTop(ctx, o.x - Math.cos(o.angle) * recoil * 2, o.y - Math.sin(o.angle) * recoil * 2, o.angle, b.ship.role, '#f2b544', 1.05);

  ctx.restore();
}

function drawBridgeIslands(ctx) {
  for (let i = 0; i < BRIDGE_ISLANDS.length; i++) {
    const isl = BRIDGE_ISLANDS[i];
    ctx.beginPath();
    for (let a = 0; a <= 28; a++) {
      const ang = a / 28 * Math.PI * 2;
      const rr = isl.r * (1 + 0.1 * Math.sin(ang * 3 + isl.seed) + 0.05 * Math.sin(ang * 7 + isl.seed * 2));
      const px = isl.x + Math.cos(ang) * rr;
      const py = isl.y + Math.sin(ang) * rr;
      if (a === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.fillStyle = '#2c4a34';
    ctx.strokeStyle = '#5d7a4a';
    ctx.lineWidth = 3;
    ctx.fill();
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(isl.x + isl.r * 0.15, isl.y - isl.r * 0.2, isl.r * 0.28, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(70,110,70,0.8)';
    ctx.fill();
    ctx.beginPath();
    ctx.arc(isl.x - isl.r * 0.3, isl.y + isl.r * 0.25, isl.r * 0.2, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(56,92,60,0.8)';
    ctx.fill();
  }
}

function drawShipTop(ctx, x, y, angle, role, color, scale) {
  const L = (role === 'carrier' ? 62 : role === 'battleship' ? 58 : role === 'submarine' ? 46 : role === 'torpedo' ? 38 : 48) * scale;
  const W = (role === 'carrier' ? 20 : role === 'battleship' ? 18 : role === 'submarine' ? 10 : 14) * scale;

  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);

  ctx.beginPath();
  ctx.moveTo(-L * 0.45, -W * 0.5);
  ctx.lineTo(L * 0.12, -W * 0.5);
  ctx.lineTo(L * 0.5, 0);
  ctx.lineTo(L * 0.12, W * 0.5);
  ctx.lineTo(-L * 0.45, W * 0.5);
  ctx.quadraticCurveTo(-L * 0.56, 0, -L * 0.45, -W * 0.5);
  ctx.closePath();
  ctx.fillStyle = 'rgba(18,38,56,0.96)';
  ctx.fill();
  ctx.lineWidth = 2.2;
  ctx.strokeStyle = color;
  ctx.stroke();

  ctx.strokeStyle = 'rgba(220,235,245,0.22)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(-L * 0.34, 0);
  ctx.lineTo(L * 0.4, 0);
  ctx.stroke();

  if (role === 'carrier') {
    ctx.fillStyle = 'rgba(90,210,244,0.12)';
    ctx.strokeStyle = 'rgba(90,210,244,0.4)';
    ctx.fillRect(-L * 0.3, -W * 0.34, L * 0.62, W * 0.68);
    ctx.strokeRect(-L * 0.3, -W * 0.34, L * 0.62, W * 0.68);
    ctx.fillStyle = 'rgba(18,38,56,0.95)';
    ctx.fillRect(-L * 0.06, -W * 0.1, L * 0.16, W * 0.34);
  } else if (role === 'submarine') {
    ctx.beginPath();
    ctx.ellipse(-L * 0.08, 0, L * 0.16, W * 0.85, 0, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(18,38,56,0.95)';
    ctx.fill();
    ctx.strokeStyle = color;
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(-L * 0.12, 0);
    ctx.lineTo(-L * 0.12, -W * 0.9);
    ctx.stroke();
  } else {
    const turrets = role === 'battleship' || role === 'cruiser' ? 2 : 1;
    for (let i = 0; i < turrets; i++) {
      const tx = turrets === 1 ? L * 0.18 : (i === 0 ? -L * 0.16 : L * 0.2);
      ctx.beginPath();
      ctx.arc(tx, 0, Math.max(3, W * 0.22), 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(18,38,56,0.95)';
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.4;
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(tx + W * 0.2, 0);
      ctx.lineTo(tx + W * 0.75, 0);
      ctx.stroke();
    }
    ctx.fillStyle = 'rgba(18,38,56,0.95)';
    ctx.strokeStyle = color;
    ctx.fillRect(-L * 0.04, -W * 0.22, L * 0.14, W * 0.44);
    ctx.strokeRect(-L * 0.04, -W * 0.22, L * 0.14, W * 0.44);
  }

  ctx.beginPath();
  ctx.arc(L * 0.12, 0, 2.2, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();

  ctx.restore();
}

/* ---------- HUD ---------- */

function updateBridgeHud() {
  if (!bridge) return;
  const o = bridge.obj;
  const speedEl = $('#hudSpeed');
  const scoreEl = $('#hudScore');
  const sunkEl = $('#hudSunk');
  const rewardEl = $('#hudReward');
  const statusEl = $('#hudStatus');
  const throttleEl = $('#hudThrottle');
  if (speedEl) {
    const maxSpeed = 22 + bridge.stats.speed * 2.2;
    speedEl.textContent = Math.round(Math.abs(o.speed) / maxSpeed * bridge.stats.speed) + ' kn';
  }
  if (scoreEl) scoreEl.textContent = bridge.score;
  if (sunkEl) sunkEl.textContent = bridge.sunk;
  if (rewardEl) rewardEl.textContent = bridge.rewarded + '/10';
  if (statusEl) statusEl.textContent = o.fireCd > 0 ? 'RECARGANDO' : 'LISTO';
  if (throttleEl) throttleEl.style.width = clamp((o.throttle + 0.4) / 1.4 * 100, 0, 100) + '%';
}
